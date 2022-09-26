from datetime import datetime, date, tzinfo, timedelta
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from account.decorators import unauthenticated_user, allowed_users
from django.contrib.auth.models import User
from account.models import Doctor, Staff, Patient, Warden
from django.contrib import messages
from .models import Diagnostic, Prescription, MedicalHistory, UserCheckInCheckOut
from .utils import create_pdf, send_to_email
import time
from graphos.renderers.gchart import PieChart
from graphos.sources.simple import SimpleDataSource
from django.db.models import Q

# !important REMEMBER TO CHANGE THE force_text TO force_str ROM THE ENV FOR GRAPHOS/UTILS.PY

# Create your views here.

@method_decorator(login_required, name='dispatch')
class Home(TemplateView):
    template_name = 'main/index.html'
    context = locals()
    context['active'] = 'home'

    def get(self, request):
        return render(request, self.template_name, self.context)


@method_decorator(allowed_users(allowed_roles=['admin', 'doctor']), name='dispatch')
class Dashboard(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'

    def get(self, request):
        # Redirect Admin and Doctor to their respective dashboard
        user = request.user
        user_groups = user.groups.all()
        # print(user_groups[0].name)
        if user_groups[0].name == 'admin':
            return redirect('active_users_chart')
        elif user_groups[0].name == 'doctor':
            return redirect('all_patients')
        else:
            return redirect('home')


#  Doctor's Views
@method_decorator(allowed_users(allowed_roles=['admin', 'doctor']), name='dispatch')
class AllPatients(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'all_patients'

    def get(self, request):
        patients = Patient.objects.all()
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in patients
        search_text = request.POST.get('search_text')
        patients = Patient.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text))
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)


@method_decorator(allowed_users(allowed_roles=['doctor']), name='dispatch')
class Diagnose(TemplateView):

    http_method_names = ['post']
    
    def post(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            messages.error(request, 'Patient does not exist')
            return redirect('all_patients')

        try:
            doctor = request.user.doctor
            diagnostic = Diagnostic.objects.create(
                patient=patient,
                doctor=doctor,
                description=request.POST.get('description'),
                disease = request.POST.get('disease'),
            )
            diagnostic.save()
            medical_history = MedicalHistory.objects.create(
                patient=patient,
                diagnostic=diagnostic,
            )
            medical_history.save()
            medical_history.doctors.add(doctor)
            medical_history.save()
            patient.doctors.add(request.user.doctor) # add doctor to the patient's doctors list
            patient.save()
            messages.info(request, 'Diagnostic created', 'alert-info')
            return redirect('all_patients')
        except Exception as e:
            messages.info(request, f'Something went wrong {e}', 'alert-info')
            return redirect('all_patients')


@method_decorator(allowed_users(allowed_roles=['doctor']), name='dispatch')
class Prescribe(TemplateView):
    template_name = 'main/add_prescription.html'
    context = locals()

    def get(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            messages.error(request, 'Patient does not exist')
            return redirect('all_patients')

        self.context['patient'] = patient
        diagnoses = Diagnostic.objects.filter(patient=patient, doctor=request.user.doctor)
        self.context['diagnoses'] = diagnoses

        return render(request, self.template_name, self.context)

    def post(self, request, id):
        diangose = Diagnostic.objects.get(id=request.POST.get('diagnose'))
        try:
            prescription = Prescription.objects.create(
                diagnose=diangose,
                medicine=request.POST.get('medicine'),
                description=request.POST.get('description'),
            )
            prescription.save()
            messages.info(request, 'Prescription created', 'alert-info')
            return redirect('prescribe',id)
        except Exception as e:
            messages.info(request, f'Something went wrong {e}', 'alert-info')
            return redirect('prescribe',id)
        

@method_decorator(allowed_users(allowed_roles=['doctor']), name='dispatch')
class MyPatients(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'my_patients'

    def get(self, request):
        my_patients = Patient.objects.filter(doctors=request.user.doctor)
        diagnoses = Diagnostic.objects.filter(doctor=request.user.doctor)
        self.context['diagnoses'] = diagnoses
        self.context['my_patients'] = my_patients
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in patients
        search_text = request.POST.get('search_text')
        my_patients = Patient.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text), doctors=request.user.doctor)
        self.context['my_patients'] = my_patients
        return render(request, self.template_name, self.context)

@method_decorator(allowed_users(allowed_roles=['doctor']), name='dispatch')
class MedicalHistoryView(TemplateView):
    template_name = 'main/medical_history.html'
    context = locals()

    def get(self, request, id):
        try:
            patient = Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            messages.error(request, 'Patient does not exist', 'alert-info')
            return redirect('my_patients')

        self.context['patient'] = patient
        self.context['medical_histories'] = MedicalHistory.objects.filter(patient=patient, doctors=request.user.doctor)
        return render(request, self.template_name, self.context)

@method_decorator(allowed_users(allowed_roles=['doctor']), name='dispatch')
class SendPrescreptionToPEmail(TemplateView):
    http_method_names = ['get']
    def get(self, request, pid, id):
        # pid = patient_id, id = diagnostic_id
        try:
            patient = Patient.objects.get(id=pid)
            diagnostic = Diagnostic.objects.get(id=id)
            # Generate PDF File
            pdf_file = create_pdf(patient, diagnostic)
            send_to_email(pdf_file, patient.user.email)      

            messages.info(request, 'Encrypted prescription sent to patient', 'alert-info')
            return redirect('medical_history',id=pid)
        except Exception as e:
            messages.error(request, f'Something went wrong\n {e}', 'alert-info')
            return redirect('medical_history',id=pid)
        


# End of Doctor Views


# Patient's Views
@method_decorator(allowed_users(allowed_roles=['patient']), name='dispatch')
class MyMedicalHistory(TemplateView):
    template_name = 'main/my_medical_history.html'
    context = locals()

    def get(self, request):
        medical_history = MedicalHistory.objects.filter(patient=request.user.patient)
        self.context['medical_histories'] = medical_history
        return render(request, self.template_name, self.context)


@method_decorator(allowed_users(allowed_roles=['patient']), name='dispatch')
class AllowedDoctors(TemplateView):
    template_name = 'main/allowed_viewers_doctors.html'
    context = locals()

    def get(self, request):
        medical_history = MedicalHistory.objects.filter(patient=request.user.patient)
        self.context['medical_histories'] = medical_history
        return render(request, self.template_name, self.context)


@allowed_users(allowed_roles=['patient'])
def allow_doctor(request, mid):
    if request.method == 'POST':
        try:
            medical_history = MedicalHistory.objects.get(id=mid)
            doctor = Doctor.objects.get(id=request.POST.get('doctor_id'))
            medical_history.doctors.add(doctor)
            messages.info(request, 'Doctor added to the list of allowed viewers', 'alert-info')
            return redirect('allowed_viewers_doctors')
        except Exception as e:
            messages.error(request, f'Something went wrong\n {e}', 'alert-info')
            return redirect('allowed_viewers_doctors')
    else:
        return redirect('allowed_viewers_doctors')


@allowed_users(allowed_roles=['patient'])
def disallow_doctor(request, mid):
    if request.method == 'POST':
        try:
            medical_history = MedicalHistory.objects.get(id=mid)
            doctor = Doctor.objects.get(id=request.POST.get('doctor_id'))
            # if the doctor is the creator of that diagnose, then it is not allowed to be removed
            if medical_history.diagnostic.doctor == doctor:
                messages.error(request, 'You cannot remove the creator of the diagnose', 'alert-info')
                return redirect('allowed_viewers_doctors')
                
            medical_history.doctors.remove(doctor)
            messages.info(request, 'Doctor removed from the list of allowed viewers', 'alert-info')
            return redirect('allowed_viewers_doctors')
        except Exception as e:
            messages.error(request, f'Something went wrong\n {e}', 'alert-info')
            return redirect('allowed_viewers_doctors')
    else:
        return redirect('allowed_viewers_doctors')


# End of Patient's Views

# Warden's Views
@method_decorator(allowed_users(allowed_roles=['warden']), name='dispatch')
class ScanId(TemplateView):
    template_name = 'main/scan_id.html'
    context = locals()
    context['active'] = 'scan_id'

    def get(self, request):
        return render(request, self.template_name, self.context)
    
    def post(self, request):
        # TODO: Check if the user already chedked in in last 5 Miniuts
        user_type = request.POST.get('user_type')
        id = request.POST.get('id')
        # print(user_type,id)
        if user_type is not None:
            if user_type == 'staff':
                user_ = Staff.objects.get(id=id)
            elif user_type == 'doctor':
                user_ = Doctor.objects.get(id=id)
            else: 
                messages.error(request, 'Invalid user type in QR-Code', 'alert-info')
                self.context['passed_text'] = "invalid user type in qr code"
                return redirect('scan_id')
            
            # Create User Check In/ Check out
            user = user_.user
            # print(user.email)
            # If already checked in / check them out
            warden_user = request.user
            ward = Warden.objects.get(user=warden_user)
            try:
                check_in = UserCheckInCheckOut.objects.get(user=user, status="check_in", checked_in__date=datetime.today())
                # print(check_in)
                # diffrence = datetime.now() - check_in.checked_in.replace(tzinfo=None)
                diffrence = datetime.now() - check_in.checked_in
                # print(diffrence)
                # JavaScript is sending many requests. only accepting one request per 5 minutes. 
                if diffrence.seconds < 300: 
                    self.context['passed_text'] = f"{user.first_name} {user.last_name} You have already checked in today"
                    return redirect('scan_id')

                check_in.status = "check_out"
                check_in.checked_out = datetime.now()
                check_in.warden = ward
                check_in.save()
                messages.info(request, f"{user.first_name} {user.last_name} User Checked Out" , 'alert-info')
                self.context['passed_text'] = f"{user.first_name} {user.last_name} User Checked Out"
                return redirect('scan_id')

            except UserCheckInCheckOut.DoesNotExist:
                # try except/ if user is already checked out today
                try:
                    today_checked_out = UserCheckInCheckOut.objects.filter(user=user, status="check_out", checked_in__date=datetime.today())
                    if today_checked_out.count() > 0:
                        self.context['passed_text'] = f"{user.first_name} {user.last_name} You have already checked out today"
                        return redirect('scan_id')
                except UserCheckInCheckOut.DoesNotExist:
                    pass
                check_in = UserCheckInCheckOut.objects.create(user=user, status="check_in", checked_in=datetime.now(), warden=ward)
                check_in.save()
                messages.info(request, f'{user.first_name} {user.last_name} User Checked In', 'alert-info')
                self.context['passed_text'] = f"{user.first_name} {user.last_name} User Checked In"
                return redirect('scan_id')
        else:
            messages.error(request, 'QR-Code is not related', 'alert-info')
            self.context['passed_text'] = "QR-Code is not related"
            return redirect('scan_id')


# end of Warden's Views

# Admin Views
@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class UsersCheckInCheckOutTodayView(TemplateView):
    template_name = 'main/users_check.html'
    context = locals()
    context['active'] = 'users_check_in_check_out_today'

    def get(self, request):
        check_in_check_out = UserCheckInCheckOut.objects.filter(checked_in__date=datetime.today())
        self.context['check_in_check_out'] = check_in_check_out
        return render(request, self.template_name, self.context)

@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class UsersCheckInCheckOutAllTimeView(TemplateView):
    template_name = 'main/users_check.html'
    context = locals()
    context['active'] = 'users_check_in_check_out_all_time'

    def get(self, request):
        check_in_check_out = UserCheckInCheckOut.objects.order_by('-checked_in')
        self.context['check_in_check_out'] = check_in_check_out
        return render(request, self.template_name, self.context)


@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AllStaff(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'staffs'

    def get(self, request):
        staffs = Staff.objects.all()
        self.context['staffs'] = staffs
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in staff's
        search_text = request.POST.get('search_text')
        staffs = Staff.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text))
        self.context['staffs'] = staffs
        return render(request, self.template_name, self.context)

@allowed_users(allowed_roles=['admin'])
def delete_staff(request, id):
    staff = User.objects.get(id=id)
    staff.delete()
    messages.info(request, f'Staff {staff.first_name} {staff.last_name} Deleted Successfully', 'alert-info')
    return redirect('all_staff')

@allowed_users(allowed_roles=['admin'])
def update_staff(request, id):
    try:
        staff = User.objects.get(id=id)
    except User.DoesNotExist:
        messages.error(request, 'Staff does not exist', 'alert-info')
        return redirect('all_staff')
    try:
        staff.username = request.POST.get('username')
        staff.first_name = request.POST.get('first_name')
        staff.last_name = request.POST.get('last_name')
        staff.email = request.POST.get('email')
        staff.staff.phone_number = request.POST.get('phone_number')
        staff.staff.address = request.POST.get('address')
        staff.staff.save()
        staff.save()
        messages.success(request, f'Staff {staff.first_name} {staff.last_name} Updated Successfully', 'alert-success')
        return redirect('all_staff')
    except Exception as e:
        messages.error(request, f'Error: {e}', 'alert-danger')
        return redirect('all_staff')

@allowed_users(allowed_roles=['admin'])
def active_disable_staff(request, id):
    staff = User.objects.get(id=id)
    if staff.is_active:
        staff.is_active = False
        messages.success(request, f'Staff {staff.first_name} {staff.last_name} Disabled Successfully', 'alert-success')
    else:
        staff.is_active = True
        messages.success(request, f'Staff {staff.first_name} {staff.last_name} Activated Successfully', 'alert-success')
    staff.save()
    return redirect('all_staff')


@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AllDoctors(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'all_doctors'

    def get(self, request):
        doctors = Doctor.objects.all()
        self.context['doctors'] = doctors
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in Doctors's
        search_text = request.POST.get('search_text')
        doctors = Doctor.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text))
        self.context['doctors'] = doctors
        return render(request, self.template_name, self.context)


@allowed_users(allowed_roles=['admin'])
def delete_doctor(request, id):
    doctor = User.objects.get(id=id)
    doctor.delete()
    messages.info(request, f'Doctor {doctor.first_name} {doctor.last_name} Deleted Successfully', 'alert-info')
    return redirect('all_doctors')

@allowed_users(allowed_roles=['admin'])
def update_doctor(request, id):
    try:
        doctor = User.objects.get(id=id)
    except User.DoesNotExist:
        messages.error(request, 'Doctor does not exist', 'alert-info')
        return redirect('all_doctors')
    try:
        doctor.username = request.POST.get('username')
        doctor.first_name = request.POST.get('first_name')
        doctor.last_name = request.POST.get('last_name')
        doctor.email = request.POST.get('email')
        doctor.doctor.phone_number = request.POST.get('phone_number')
        doctor.doctor.address = request.POST.get('address')
        doctor.doctor.save()
        doctor.save()
        messages.success(request, f'Doctor {doctor.first_name} {doctor.last_name} Updated Successfully', 'alert-success')
        return redirect('all_doctors')
    except Exception as e:
        messages.error(request, f'Error: {e}', 'alert-danger')
        return redirect('all_doctors')

@allowed_users(allowed_roles=['admin'])
def active_disable_doctor(request, id):
    doctor = User.objects.get(id=id)
    if doctor.is_active:
        doctor.is_active = False
        messages.success(request, f'Doctor {doctor.first_name} {doctor.last_name} Disabled Successfully', 'alert-success')
    else:
        doctor.is_active = True
        messages.success(request, f'Doctor {doctor.first_name} {doctor.last_name} Activated Successfully', 'alert-success')
    doctor.save()
    return redirect('all_doctors')

# Active users chart
@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class ActiveUsersChart(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'active_users_chart'

    def get(self, request):
        # all usrs chart
        all_patients_count = Patient.objects.filter(user__is_active=True).count()
        all_doctors_count = Doctor.objects.filter(user__is_active=True).count()
        all_staff_count = Staff.objects.filter(user__is_active=True).count()
        all_warden_count = Warden.objects.filter(user__is_active=True).count()

        data_for_all_users_chart = [
            ['User Type', 'Count'],
            ['Patients', all_patients_count],
            ['Doctors', all_doctors_count],
            ['Staffs', all_staff_count],
            ['Warden', all_warden_count],
        ]
        all_users_chart = PieChart(SimpleDataSource(data=data_for_all_users_chart))
        all_users_chart.options['title'] = 'All Users'
        self.context['all_users_chart'] = all_users_chart
        


        # end of all users chart
        #  Active Users Chart
        today = datetime.today()
        seven_days_before = today - timedelta(days=7)
        users = User.objects.filter(last_login__date__gte=seven_days_before)
        active_patients_count = 0
        active_doctors_count = 0
        active_staffs_count = 0
        active_wardens_count = 0
        for user in users:
            if user.groups.filter(name='doctor').exists():
                active_doctors_count += 1
            elif user.groups.filter(name='staff').exists():
                active_staffs_count += 1
            elif user.groups.filter(name='patient').exists():
                active_patients_count += 1
            elif user.groups.filter(name='warden').exists():
                active_wardens_count += 1

        data_for_active_users_chart = [
            ['User Type', 'Count'],
            ['Patients', active_patients_count],
            ['Doctors', active_doctors_count],
            ['Staffs', active_staffs_count],
            ['Wardens', active_wardens_count]
        ]
        active_users_chart = PieChart(SimpleDataSource(data=data_for_active_users_chart))
        active_users_chart.options['title'] = 'Last 7 Days Active Users'
        self.context['active_users_chart'] = active_users_chart
        # End of active users chart

        return render(request, self.template_name, self.context)

# for patients 
@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class Patients(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'patients'

    def get(self, request):
        patients = Patient.objects.all()
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in Patients
        search_text = request.POST.get('search_text')
        patients = Patient.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text))
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)

@allowed_users(allowed_roles=['admin'])
def delete_patient(request, id):
    patient = User.objects.get(id=id)
    patient.delete()
    messages.info(request, f'Patient {patient.first_name} {patient.last_name} Deleted Successfully', 'alert-info')
    return redirect('patients')

@allowed_users(allowed_roles=['admin'])
def update_patient(request, id):
    try:
        patient = User.objects.get(id=id)
    except User.DoesNotExist:
        messages.error(request, 'Patient does not exist', 'alert-info')
        return redirect('patients')
    try:
        patient.username = request.POST.get('username')
        patient.first_name = request.POST.get('first_name')
        patient.last_name = request.POST.get('last_name')
        patient.email = request.POST.get('email')
        patient.patient.phone_number = request.POST.get('phone_number')
        patient.patient.address = request.POST.get('address')
        patient.patient.save()
        patient.save()
        messages.success(request, f'Patient {patient.first_name} {patient.last_name} Updated Successfully', 'alert-success')
        return redirect('patients')
    except Exception as e:
        messages.error(request, f'Error: {e}', 'alert-danger')
        return redirect('patients')

@allowed_users(allowed_roles=['admin'])
def active_disable_patient(request, id):
    patient = User.objects.get(id=id)
    if patient.is_active:
        patient.is_active = False
        messages.success(request, f'Patient {patient.first_name} {patient.last_name} Disabled Successfully', 'alert-success')
    else:
        patient.is_active = True
        messages.success(request, f'Patient {patient.first_name} {patient.last_name} Activated Successfully', 'alert-success')
    patient.save()
    return redirect('patients')


@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class Wardens(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'wardens'

    def get(self, request):
        wardens = Warden.objects.all()
        self.context['wardens'] = wardens
        return render(request, self.template_name, self.context)
    def post(self, request):
        # search in Wardens
        search_text = request.POST.get('search_text')
        wardens = Warden.objects.filter(Q(user__username__icontains=search_text) |Q(user__first_name__icontains=search_text) | Q(user__last_name__icontains=search_text) | Q(user__email__icontains=search_text) | Q(phone_number__icontains=search_text))
        self.context['wardens'] = wardens
        return render(request, self.template_name, self.context)

@allowed_users(allowed_roles=['admin'])
def delete_warden(request, id):
    warden = User.objects.get(id=id)
    warden.delete()
    messages.info(request, f'Warden {warden.first_name} {warden.last_name} Deleted Successfully', 'alert-info')
    return redirect('wardens')

def update_warden(request, id):
    try:
        warden = User.objects.get(id=id)
    except User.DoesNotExist:
        messages.error(request, 'Warden does not exist', 'alert-info')
        return redirect('wardens')
    try:
        warden.username = request.POST.get('username')
        warden.first_name = request.POST.get('first_name')
        warden.last_name = request.POST.get('last_name')
        warden.email = request.POST.get('email')
        warden.warden.phone_number = request.POST.get('phone_number')
        warden.warden.address = request.POST.get('address')
        warden.warden.save()
        warden.save()
        messages.success(request, f'Warden {warden.first_name} {warden.last_name} Updated Successfully', 'alert-success')
        return redirect('wardens')
    except Exception as e:
        messages.error(request, f'Error: {e}', 'alert-danger')
        return redirect('wardens')

@allowed_users(allowed_roles=['admin'])
def active_disable_warden(request, id):
    warden = User.objects.get(id=id)
    if warden.is_active:
        warden.is_active = False
        messages.success(request, f'Warden {warden.first_name} {warden.last_name} Disabled Successfully', 'alert-success')
    else:
        warden.is_active = True
        messages.success(request, f'Warden {warden.first_name} {warden.last_name} Activated Successfully', 'alert-success')
    warden.save()
    return redirect('wardens')



# Error Pages
def error_404(request, exception):
    return render(request, 'main/error_handlers/404.html')

def error_500(request):
    return render(request, 'main/error_handlers/500.html')

def error_403(request, exception):
    return render(request, 'main/error_handlers/403.html')

def error_400(request, exception):
    return render(request, 'main/error_handlers/400.html')