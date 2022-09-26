from django.dispatch import receiver
from axes.signals import user_locked_out
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from datetime import datetime

@receiver(user_locked_out)
def user_locked_out_signal(*args, **kwargs):
    # username, ip_address, user_agent 
    # send email to the user to inform about this unauthorized login attempt

    site = get_current_site(kwargs['request'])
    user = User.objects.get(username=kwargs['username'])
    date_time = datetime.now()
    html_message = render_to_string('account/failed_login_attempts_email.html', {
        'username': user.username,
        'domain': site.domain,
        'ip_address': kwargs['ip_address'],
        'date and time': date_time

    })
    # filling the  activation mail template w/ all the variables 
    message = f"""
    Hi { kwargs['username'] },
    Someone is trying to log in to your account on { site.domain }.

    Here are the details:
    IP Address: { kwargs['ip_address'] }
    date and time: { date_time }


    If this was you please ignore this email.

    This is a system generated email. Please do not reply to this email.

    Thanks,
    {site.domain}
    """
    # TODO: sending the email to the user uncomment on production
    # send_mail(
    #     'Failed Login Attempts',
    #     message,
    #     'Clinic Management System ',
    #     [user.email],
    #     html_message=html_message,
    #     fail_silently=True
    # )