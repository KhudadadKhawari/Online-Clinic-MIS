from django import views
from django.urls import path
from . import views


urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    #  warden views
    path('scan_id/', views.ScanId.as_view(), name='scan_id'),
    # Admin Views
    path('active_users_chart/', views.ActiveUsersChart.as_view(), name='active_users_chart'),
    path('users_check_in_check_out/today', views.UsersCheckInCheckOutTodayView.as_view(), name='users_check_in_check_out_today'),
    path('users_check_in_check_out/all_time', views.UsersCheckInCheckOutAllTimeView.as_view(), name='users_check_in_check_out_all_time'),

    # for staffs
    path('all_staff/', views.AllStaff.as_view(), name='all_staff'),
    path('staff/delete/<id>/', views.delete_staff, name='delete_staff'),
    path('staff/update/<id>/', views.update_staff, name='update_staff'),
    path('staff/active_disable/<id>/', views.active_disable_staff, name='active_disable_staff'),
    # for doctors
    path('all_doctors/', views.AllDoctors.as_view(), name='all_doctors'),
    path('doctor/delete/<id>/', views.delete_doctor, name='delete_doctor'),
    path('doctor/update/<id>/', views.update_doctor, name='update_doctor'),
    path('doctor/active_disable/<id>/', views.active_disable_doctor, name='active_disable_doctor'),
    # for patients
    path('patients/', views.Patients.as_view(), name='patients'),
    path('patient/update/<id>/', views.update_patient, name='update_patient'),
    path('patient/active_disable/<id>/', views.active_disable_patient, name='active_disable_patient'),
    # for warden
    path('wardens/', views.Wardens.as_view(), name='wardens'),
    path('warden/update/<id>/', views.update_warden, name='update_warden'),
    path('warden/delete/<id>/', views.delete_warden, name='delete_warden'),
    path('warden/active_disable/<id>/', views.active_disable_warden, name='active_disable_warden'),

    # Doctor Views
    path('my_patients/', views.MyPatients.as_view(), name='my_patients'),
    path('all_patients/', views.AllPatients.as_view(), name='all_patients'),

    path('patient/diagnose/<id>', views.Diagnose.as_view(), name='diagnose_patient'),
    path('patient/<id>/', views.Prescribe.as_view(), name='prescribe'),
    path('patient/<id>/medical_history', views.MedicalHistoryView.as_view(), name='medical_history'),
    path('patient/<pid>/medical_history/<id>', views.SendPrescreptionToPEmail.as_view(), name='send_prescreption_to_p_email'),

    # Patient Views
    path('my_medical_history/', views.MyMedicalHistory.as_view(), name='my_medical_history'),
    path('my_medical_history/allowed_doctors/', views.AllowedDoctors.as_view(), name='allowed_viewers_doctors'),
    path('my_medical_history/<mid>/allow_doctor', views.allow_doctor, name='allow_doctor'),
    path('my_medical_history/<mid>/disallow_doctor', views.disallow_doctor, name='disallow_doctor'),
    
]  