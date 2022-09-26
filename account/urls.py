from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register_patient/', views.RegisterPatient.as_view(), name='register_patient'),
    path('approve_patients_request/', views.ApprovePatientsRequest.as_view(), name='approve_patients_request'),
    path('rjected_patients/', views.RejectedPatients.as_view(), name='rejected_patients'),
    path('patient/approve/<pk>', views.approve_patient, name='approve_patient'),
    path('patient/reject/<pk>', views.reject_patient, name='reject_patient'),
    path('patient/delete/<pk>', views.delete_patient, name='delete_patient'),
    path('patient/send_to_pending/<pk>', views.send_to_pending_patients, name='send_to_pending_patients'),
    path('account/profile/', views.Profile.as_view(), name='profile'),
    path('account/profile/change_password/', views.ChangePassword.as_view(), name='change_password'),
    path('account/register/', views.Register.as_view(), name='register'),
    path('account/login/', views.UserLogin.as_view(), name='user_login'),
    path('account/logout/', views.UserLogout.as_view(), name='user_logout'), 
    path('confirm_email/<uidb64>/<token>', views.confirm_email, name='confirm_email'),
    # Forget Password
    path('account/password_reset/', auth_views.PasswordResetView.as_view(template_name='account/forgot_password/password_reset.html'), name='password_reset'),
    path('account/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/forgot_password/password_reset_done.html'), name='password_reset_done'),
    path('account/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/forgot_password/password_reset_confirm.html'), name='password_reset_confirm'),
    path('account/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/forgot_password/password_reset_complete.html'), name='password_reset_complete'),
    # admin views
    path('add_staff/', views.AddStaff.as_view(), name='add_staff'),
    path('add_doctor/', views.AddDoctor.as_view(), name='add_doctor'),
    path('add_patient/', views.AddPatient.as_view(), name='add_patient'),
    path('add_warden', views.AddWarden.as_view(), name='add_warden'),

    

]