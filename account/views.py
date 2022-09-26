from django.db import IntegrityError
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.views.generic import TemplateView
from .utils import password_generator, generate_username
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .decorators import unauthenticated_user, allowed_users
from .models import Staff, Doctor, Patient, Warden
from django.contrib import messages
from .forms import UserProfileForm
from .tokens import account_activation_token
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import PasswordChangeForm
import requests
from django.conf import settings
from django.db.models import Q


#function to check recaptcha
def check_recaptcha(response):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    params = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': response
    }
    r = requests.get(url=url, params=params)
    if r.json()['success']:
        return True
    else:
        return False


@method_decorator(unauthenticated_user, name='dispatch')
class Register(TemplateView):
    template_name = 'account/register.html'
    context = locals()
    context['active'] = 'register'
    context['recaptcha_site_key'] = settings.RECAPTCHA_SITE_KEY

    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        try:
            username = request.POST.get('username').lower().replace(' ', '')
            password1 = request.POST.get('password')
            password2 = request.POST.get('confirm_password')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')

            # Checking for reCaptcha
            if not check_recaptcha(request.POST.get('g-recaptcha-response')):
                messages.error(request, 'Invalid Captcha.', 'alert-info')
                return redirect('register')
            # Checking if user already exists then login them in 
            user = authenticate(username=username, password=password1)
            
            #  Check for the existence of username, email or mismatch of passwords
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username {username} already exists', 'alert-info')
                return redirect('register')
            if password1 != password2:
                messages.error(request, 'Passwords do not match', "alert-info")
                return redirect('register')
            if User.objects.filter(email=email).exists():
                messages.error(request, f'Email {email} already exists', "alert-info")
                return redirect('register')

            #Creating The user Object and the Patient Object
            user_group = Group.objects.get(name='patient')
            user = User.objects.create_user(username=username, password=password1, email=email, first_name=first_name, last_name=last_name)
            user.is_active = False # deactivate user's account until it gets confirmed by the staff
            user.save()
            user_group.user_set.add(user) # Adding User to Patient Users Group
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            date_of_birth = request.POST.get('date_of_birth')
            patient = Patient.objects.create(
                user=user,
                phone_number=phone_number,
                address=address,
                date_of_birth=date_of_birth,   
            )
            if request.FILES.get('profile_picture'):
                profile_picture = request.FILES.get('profile_picture')
                patient.photo=profile_picture
            patient.save()
            # Sending Email to the user to confirm their account
            user_email = user.email
            site = get_current_site(request) # Getting the domain
            html_message = render_to_string('account/email_confirmation_mail.html', {
                'user': user,
                'protocol': 'http',
                'domain': site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            # filling the  activation mail template w/ all the variables 
            message = f"""
            Hi {{ user.username }},
            To confirm your Email and Activate your Account on  {{ domain }},
            click the link below:

            http://{{ site.domain }}/confirm_email/{{ uid }}/{{ token }}

            If clicking the link above doesn't work, please copy and paste the URL in a new browser
            window instead.

            Thanks,
            Hospital Management System
            """
            # TODO: Uncomment on Production
            send_mail(
                'Verify Your Email Address',
                message,
                'Clinic Management System ',
                [user_email],
                html_message=html_message,
                fail_silently=True
            )
            messages.success(request, "Account Created Successfully Please Check Your E-mail For Verification", "alert-success")
            return redirect('home')

        except IntegrityError as e:
            messages.error(request, f'{e}', 'alert-info')
            return redirect('register')


def confirm_email(request, uidb64, token):
    """Check the activation token sent via mail."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        messages.warning(request, str(e), 'alert-warning' )
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        # user.is_active = True  # now we're activating the user
        user.patient.email_verified = 1  # and we're changing the boolean field so that the token link becomes invalid
        user.save()
        user.patient.save()
        messages.success(request, f'Email is Verified', 'alert-success')
    else:
        messages.warning(request, 'Account activation link is invalid.', 'alert-warning')

    return redirect('home')


@method_decorator(unauthenticated_user, name='dispatch')
class UserLogin(TemplateView):
    template_name = 'account/login_page.html'
    context = locals()
    context['active'] = 'login'
    context['recaptcha_site_key'] = settings.RECAPTCHA_SITE_KEY

    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        username = request.POST.get('username').lower().replace(' ', '')
        password = request.POST.get('password')
        if '@' in username:
            the_user = User.objects.get(email=username)
            username = the_user.username

        # Checking if reCapthca is valid
        if not check_recaptcha(request.POST.get('g-recaptcha-response')):
            messages.error(request, 'Invalid Captcha', 'alert-info')
            return redirect('user_login')

        if User.objects.filter(username=username).exists():
            # if user is patient they need to verify their email inorder to login
            user = User.objects.get(username=username)
            user_groups = user.groups.all()
            if user_groups.filter(name='patient').exists():
                if user.patient.email_verified == 0:
                    messages.error(request, 'Please Verify Your Email', 'alert-info')
                    return redirect('user_login')

            if not user.is_active: # if user is not active
                if user_groups.filter(name='patient').exists():
                    if user.patient.approval_status == 0:
                        messages.error(request, 'Your Account is Pending Approval', 'alert-info')
                        return redirect('user_login')
                    elif user.patient.approval_status == 2: 
                        messages.error(request, 'Your Joining Request is Rejected', 'alert-info')
                        return redirect('user_login')
                    else:
                        messages.error(request, 'Your Account is Deactivated please contact support team', 'alert-info')
                        return redirect('user_login')
                else:
                    messages.error(request, 'Your Account is not Active or has been disabled please contact support team', 'alert-info')
                    return redirect('user_login')
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('/')
                else:
                    messages.error(request, 'Invalid Password', 'alert-info')
        else:
            messages.error(request, 'Username Doesn\'t Exists', 'alert-info')
        return redirect('user_login')


@method_decorator(login_required, name='dispatch')
class UserLogout(TemplateView):

    def get(self, request):
        logout(request)
        return redirect('user_login')

@method_decorator(login_required, name='dispatch')
class Profile(TemplateView):
    template_name = 'account/profile.html'
    context = locals()
    context['active'] = 'profile'
    def qr_code_text(self, user_id=0):
        """Generate QR code text for the user."""
        user = self.request.user
        l = user.groups.values_list('name', flat=True)[0]

        txtjson = "{"+f'"user_type":"{l}",'+f'"user_id":{user_id}'+"}"
        
        return txtjson
    
    def get(self, request):
        user = self.request.user
        l = user.groups.values_list('name', flat=True) # Getting the user's group
        self.context['user_group'] = l[0]
        # self.context['qr_code_text'] = self.qr_code_text() # Creating the Json for the QR-Code
        if l[0] == 'patient':
            form = UserProfileForm(instance=user, initial={'phone_number': user.patient.phone_number, 'address': user.patient.address, 'date_of_birth': user.patient.date_of_birth})
            user_id = user.patient.id
        elif l[0] == 'doctor':
            form = UserProfileForm(instance=user, initial={'phone_number': user.doctor.phone_number, 'address': user.doctor.address})
            user_id = user.doctor.id
        elif l[0] == 'warden':
            form = UserProfileForm(instance=user, initial={'phone_number': user.warden.phone_number, 'address': user.warden.address})
            user_id = user.warden.id
        elif l[0] == 'staff':
            form = UserProfileForm(instance=user, initial={'phone_number': user.staff.phone_number, 'address': user.staff.address})
            user_id = user.staff.id
        else:
            form = UserProfileForm(instance=user)
            user_id = 0
        self.context['qr_code_text'] = self.qr_code_text(user_id)
        self.context['form'] = form

        return render(request, self.template_name, self.context)

    
    def post(self, request):        
        current_user = request.user
        email = current_user.email
        form = UserProfileForm(request.POST, request.FILES, instance=current_user)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data.get('username').lower().replace(' ', '_')
            user.email = email # keeping the email the same
            user.save()
            messages.info(request, 'Profile Updated Successfully', 'alert-info')
            return redirect('profile')
        else:
            messages.info(request, 'No Changes Applied', 'alert-warning')
            return redirect('profile')

@method_decorator(login_required, name='dispatch')
class ChangePassword(TemplateView):
    template_name = 'account/change_password.html'
    context = locals()
    context['active'] = 'profile'

    def get(self, request):
        form = PasswordChangeForm(request.user)
        self.context['form'] = form
        return render(request, self.template_name, self.context)

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!', 'alert-success')
            return redirect('profile')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{field.name}: {error}", 'alert-warning')
            return redirect('change_password')


# Staff's Views
@method_decorator(allowed_users(allowed_roles=['staff']), name='dispatch')
class RegisterPatient(TemplateView):
    template_name = 'account/register_patient.html'
    context = locals()
    context['active'] = 'register_patient'

    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        email = request.POST.get('email').lower().replace(' ', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        date_of_birth = request.POST.get('date_of_birth')
        address = request.POST.get('address')

        username = generate_username(first_name, last_name)
        password = password_generator(10)

        if User.objects.filter(username=username).exists():
            username = generate_username(first_name, last_name)

        if User.objects.filter(email=email).exists():
            messages.info(request, f'Email {email} already exists', 'alert-info')
            return redirect('register_patient')

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.save()
        user_group = Group.objects.get(name='patient')
        user_group.user_set.add(user)
        # Current Staff User 
        staff_user = request.user
        current_user = Staff.objects.get(user=staff_user)
        patient = Patient.objects.create(
            user=user,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            address=address,
            email_verified = 1,
            approval_status = 1,
            registered_by = current_user,
        )
        patient.save()
        
        # Sending Email to the user with their account details  
        user_email = user.email
        site = get_current_site(request) # Getting the domain
        message = f"""
        Hello {user.username},
        To login to your account, use the following details:
        Username: {user.username}
        Password: {password}
        Thanks for registering with us.
        """
        html_message = render_to_string('account/user_account_details.html', {
            'user': user,
            'domain': site.domain,
            'password': password,
        })
        # filling the  activation mail template w/ all the variables
        # TODO: Uncomment on Production
        print(html_message)
        # send_mail(
        #     'Your Account Details',
        #     message,
        #     'Clinic Management System',
        #     [user_email],
        #     html_message= html_message,
        #     fail_silently=True
        # )
        messages.success(request, "Account Created Successfully user can  Check their E-mail For the credentials", "alert-success")
        return redirect('register_patient')


@method_decorator(allowed_users(allowed_roles=['staff']), name='dispatch')
class ApprovePatientsRequest(TemplateView):
    template_name = 'account/approve_patients_request.html'
    context = locals()
    context['active'] = 'approve_patients_request'

    def get(self, request):
        inactive_users = User.objects.filter(is_active=False, groups__name='patient', patient__approval_status=0)
        self.context['patients'] = inactive_users
        return render(request, self.template_name, self.context)

    def post(self, request):
        # search in patients
        search_text = request.POST.get('search_text')
        patients = User.objects.filter(Q(username__icontains=search_text) |Q(first_name__icontains=search_text) | Q(last_name__icontains=search_text) | Q(email__icontains=search_text) | Q(patient__phone_number__icontains=search_text),is_active=False, groups__name='patient', patient__approval_status=0)
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)

# Approve, Decline, Delete and send back to pending Patients Joining Requests
@allowed_users(allowed_roles=['staff'])
def approve_patient(request, pk):
    user = User.objects.get(pk=pk)
    user.is_active = True
    user.save()
    user.patient.approval_status = 1
    user.patient.registered_by = Staff.objects.get(user=request.user) #getting the staff account who approved the patient
    user.patient.save()
    messages.success(request, f'Account for {user.username} is approved', 'alert-success')
    return redirect('approve_patients_request')


@allowed_users(allowed_roles=['staff'])
def reject_patient(request, pk):
    user = User.objects.get(pk=pk)
    user.patient.approval_status = 2
    user.patient.save()
    messages.success(request, f'Account for {user.username} is declined', 'alert-success')
    return redirect('approve_patients_request')


@allowed_users(allowed_roles=['staff', 'admin'])
def delete_patient(request, pk):
    user = User.objects.get(pk=pk)
    user.delete()
    current_user_groups = request.user.groups.values_list('name',flat = True) # QuerySet Object
    current_user_groups_list = list(current_user_groups)  # Converting QuerySet Object to List
    if 'staff' in current_user_groups_list:
        messages.success(request, f'Account for {user.username} is deleted', 'alert-success')
        return redirect('approve_patients_request')
    elif 'admin' in current_user_groups_list:
        messages.success(request, f'Account for {user.username} is deleted', 'alert-success')
        return redirect('patients')

@allowed_users(allowed_roles=['staff'])
def send_to_pending_patients(request, pk):
    user = User.objects.get(pk=pk)
    user.patient.approval_status = 0 
    user.is_active = False
    user.save()
    user.patient.save()
    messages.success(request, f'Account for {user.username} is sent to pending', 'alert-success')
    return redirect('rejected_patients')


class RejectedPatients(TemplateView):
    template_name = 'account/rejected_patients.html'
    context = locals()
    context['active'] = 'rejected_patients'

    def get(self, request):
        rejected_patients = User.objects.filter(is_active=False, groups__name='patient', patient__approval_status=2)
        self.context['patients'] = rejected_patients
        return render(request, self.template_name, self.context)

    def post(self, request):
        # search in patients
        search_text = request.POST.get('search_text')
        patients = User.objects.filter(Q(username__icontains=search_text) |Q(first_name__icontains=search_text) | Q(last_name__icontains=search_text) | Q(email__icontains=search_text) | Q(patient__phone_number__icontains=search_text),is_active=False, groups__name='patient', patient__approval_status=2)
        self.context['patients'] = patients
        return render(request, self.template_name, self.context)


### Admin Views
@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AddStaff(TemplateView):
    def get(self, request):
        return redirect('all_staff')

    def post(self, request):
        email = request.POST.get('email').lower().replace(' ', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        username = generate_username(first_name, last_name)
        password = password_generator(10)

        if User.objects.filter(username=username).exists():
            username = generate_username(first_name, last_name)

        if User.objects.filter(email=email).exists():
            messages.info(request, f'Email {email} already exists', 'alert-info')
            return redirect('all_staff')

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.save()
        user_group = Group.objects.get(name='staff')
        user_group.user_set.add(user)
        staff = Staff.objects.create(
            user=user,
            phone_number=phone_number,
            address=address
        )
        staff.save()
        
        # Sending Email to the user with their account details  
        user_email = user.email
        site = get_current_site(request) # Getting the domain
        message = f"""
        Hello {user.username},
        To login to your account, use the following details:
        Username: {user.username}
        Password: {password}
        for any query contact the admin.
        """
        html_message = render_to_string('account/user_account_details.html', {
            'user': user,
            'domain': site.domain,
            'password': password,
        })
        # filling the  activation mail template w/ all the variables
        print(html_message)
        # TODO: Uncomment On Production
        # send_mail(
        #     'Your Account Details',
        #     message,
        #     'Clinic Management System',
        #     [user_email],
        #     html_message= html_message,
        #     fail_silently=True
        # )
        messages.success(request, "Account Created Successfully user can  Check their E-mail For the credentials", "alert-success")
        return redirect('all_staff')


@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AddDoctor(TemplateView):
    def get(self, request):
        return redirect('all_doctors')

    def post(self, request):
        email = request.POST.get('email').lower.replace(' ', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        username = generate_username(first_name, last_name)
        password = password_generator(10)

        if User.objects.filter(username=username).exists():
            username = generate_username(first_name, last_name)

        if User.objects.filter(email=email).exists():
            messages.info(request, f'Email {email} already exists', 'alert-info')
            return redirect('all_doctors')

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.save()
        user_group = Group.objects.get(name='doctor')
        user_group.user_set.add(user)
        doctor = Doctor.objects.create(
            user=user,
            phone_number=phone_number,
            address=address
        )
        doctor.save()
        
        # Sending Email to the user with their account details  
        user_email = user.email
        site = get_current_site(request) # Getting the domain
        message = f"""
        Hello {user.username},
        To login to your account, use the following details:
        Username: {user.username}
        Password: {password}
        for any query contact the admin.
        """
        html_message = render_to_string('account/user_account_details.html', {
            'user': user,
            'domain': site.domain,
            'password': password,
        })
        # filling the  activation mail template w/ all the variables
        print(html_message)
        # TODO: Uncomment On Production
        # send_mail(
        #     'Your Account Details',
        #     message,
        #     'Clinic Management System',
        #     [user_email],
        #     html_message= html_message,
        #     fail_silently=True
        # )
        messages.success(request, "Account Created Successfully user can  Check their E-mail For the credentials", "alert-success")
        return redirect('all_doctors')


@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AddPatient(TemplateView):
    def get(self, request):
        return redirect('patients')

    def post(self, request):
        email = request.POST.get('email').lower().replace(' ', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        date_of_birth = request.POST.get('date_of_birth')

        username = generate_username(first_name, last_name)
        password = password_generator(10)

        if User.objects.filter(username=username).exists():
            username = generate_username(first_name, last_name)

        if User.objects.filter(email=email).exists():
            messages.info(request, f'Email {email} already exists', 'alert-info')
            return redirect('patients')

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.save()
        user_group = Group.objects.get(name='patient')
        user_group.user_set.add(user)
        patient = Patient.objects.create(
            user=user,
            phone_number=phone_number,
            address=address,
            date_of_birth=date_of_birth,
            email_verified=1,
            approval_status=1,
        )
        patient.save()
        
        # Sending Email to the user with their account details  
        user_email = user.email
        site = get_current_site(request) # Getting the domain
        message = f"""
        Hello {user.username},
        To login to your account, use the following details:
        Username: {user.username}
        Password: {password}
        for any query contact the admin.
        """
        html_message = render_to_string('account/user_account_details.html', {
            'user': user,
            'domain': site.domain,
            'password': password,
        })
        # filling the  activation mail template w/ all the variables
        print(html_message)
        # TODO: Uncomment On Production
        # send_mail(
        #     'Your Account Details',
        #     message,
        #     'Clinic Management System',
        #     [user_email],
        #     html_message= html_message,
        #     fail_silently=True
        # )
        messages.success(request, "Account Created Successfully user can  Check their E-mail For the credentials", "alert-success")
        return redirect('patients')



@method_decorator(allowed_users(allowed_roles=['admin']), name='dispatch')
class AddWarden(TemplateView):
    template_name = 'main/dashboard.html'
    context = locals()
    context['active'] = 'dashboard'
    context['active2'] = 'wardens'

    def get(self, request):
        return render(request, self.template_name, self.context)

    def post(self, request):
        email = request.POST.get('email').lower.replace(' ', '')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        username = generate_username(first_name, last_name)
        password = password_generator(10)

        if User.objects.filter(username=username).exists():
            username = generate_username(first_name, last_name)

        if User.objects.filter(email=email).exists():
            messages.info(request, f'Email {email} already exists', 'alert-info')
            return redirect('wardens')

        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        user.save()
        user_group = Group.objects.get(name='warden')
        user_group.user_set.add(user)
        warden = Warden.objects.create(
            user=user,
            phone_number=phone_number,
            address=address
        )
        warden.save()
        
        # Sending Email to the user with their account details  
        user_email = user.email
        site = get_current_site(request) # Getting the domain
        message = f"""
        Hello {user.username},
        To login to your account, use the following details:
        Username: {user.username}
        Password: {password}
        for any query contact the admin.
        """
        html_message = render_to_string('account/user_account_details.html', {
            'user': user,
            'domain': site.domain,
            'password': password,
        })
        # filling the  activation mail template w/ all the variables
        print(html_message)
        # TODO: Uncomment On Production
        # send_mail(
        #     'Your Account Details',
        #     message,
        #     'Clinic Management System',
        #     [user_email],
        #     html_message= html_message,
        #     fail_silently=True
        # )
        messages.success(request, "Account Created Successfully user can  Check their E-mail For the credentials", "alert-success")
        return redirect('wardens')