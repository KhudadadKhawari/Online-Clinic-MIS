from django.shortcuts import render, HttpResponse
import requests
from account.models import Staff, Patient, Doctor, Warden
from django.contrib.auth.models import User, Group
import datetime


# Create your views here.

# function to save an image from url
def save_image(url):
    # save image to local
    image_name = url.split('/')[-1]
    with open(f"static/images/test/{image_name}", 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
    
    return f"static/images/test/{image_name}"


# create a new staff
def create_staff(request):
    staffs = []
    user_group = Group.objects.get(name='staff')
    for _ in range (50):
        reandom_user = requests.get('https://randomuser.me/api/')
        random_user_json = reandom_user.json()
        random_user_image = random_user_json['results'][0]['picture']['large']
        random_user_image_url = save_image(random_user_image)

        username = random_user_json['results'][0]['login']['username']
        password = "userpassword"
        first_name = random_user_json['results'][0]['name']['first']
        last_name = random_user_json['results'][0]['name']['last']
        email = random_user_json['results'][0]['email']
        phone_number = random_user_json['results'][0]['phone']
        address = random_user_json['results'][0]['location']['street']

        staff = Staff.objects.create(
            user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email),
            phone_number=phone_number,
            address=address,
            photo=random_user_image_url
        )
        user_group.user_set.add(staff.user)
        staffs.append(staff)
        print(f"finished {staff}")

    return HttpResponse(f"{staffs}")


def create_doctor(request):
    doctors = []
    user_group = Group.objects.get(name='doctor')
    for _ in range (50):
        reandom_user = requests.get('https://randomuser.me/api/')
        random_user_json = reandom_user.json()
        random_user_image = random_user_json['results'][0]['picture']['large']
        random_user_image_url = save_image(random_user_image)

        username = random_user_json['results'][0]['login']['username']
        password = "userpassword"
        first_name = random_user_json['results'][0]['name']['first']
        last_name = random_user_json['results'][0]['name']['last']
        email = random_user_json['results'][0]['email']
        phone_number = random_user_json['results'][0]['phone']
        address = f"{random_user_json['results'][0]['location']['street']['name']}, {random_user_json['results'][0]['location']['street']['number']}, {random_user_json['results'][0]['location']['city']}, {random_user_json['results'][0]['location']['state']}, {random_user_json['results'][0]['location']['postcode']}, {random_user_json['results'][0]['location']['country']}"
        print(address)

        doctor = Doctor.objects.create(
            user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email),
            phone_number=phone_number,
            address=address,
            photo=random_user_image_url
        )
        user_group.user_set.add(doctor.user)
        doctors.append(doctor)
        print(f"finished {doctor}")

    return HttpResponse(f"{doctors}")




def create_warden(request):
    wardens = []
    user_group = Group.objects.get(name='warden')
    for _ in range (50):
        reandom_user = requests.get('https://randomuser.me/api/')
        random_user_json = reandom_user.json()
        random_user_image = random_user_json['results'][0]['picture']['large']
        random_user_image_url = save_image(random_user_image)

        username = random_user_json['results'][0]['login']['username']
        password = "userpassword"
        first_name = random_user_json['results'][0]['name']['first']
        last_name = random_user_json['results'][0]['name']['last']
        email = random_user_json['results'][0]['email']
        phone_number = random_user_json['results'][0]['phone']
        address = f"{random_user_json['results'][0]['location']['street']['name']}, {random_user_json['results'][0]['location']['street']['number']}, {random_user_json['results'][0]['location']['city']}, {random_user_json['results'][0]['location']['state']}, {random_user_json['results'][0]['location']['postcode']}, {random_user_json['results'][0]['location']['country']}"
        print(address)

        warden = Warden.objects.create(
            user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email),
            phone_number=phone_number,
            address=address,
            photo=random_user_image_url
        )
        user_group.user_set.add(warden.user)
        wardens.append(warden)
        print(f"finished {warden}")

    return HttpResponse(f"{wardens}")


def create_patient(request):
    patients = []
    user_group = Group.objects.get(name='patient')
    for _ in range (50):
        reandom_user = requests.get('https://randomuser.me/api/')
        random_user_json = reandom_user.json()
        random_user_image = random_user_json['results'][0]['picture']['large']
        random_user_image_url = save_image(random_user_image)

        username = random_user_json['results'][0]['login']['username']
        password = "userpassword"
        first_name = random_user_json['results'][0]['name']['first']
        last_name = random_user_json['results'][0]['name']['last']
        email = random_user_json['results'][0]['email']
        phone_number = random_user_json['results'][0]['phone']
        address = f"{random_user_json['results'][0]['location']['street']['name']}, {random_user_json['results'][0]['location']['street']['number']}, {random_user_json['results'][0]['location']['city']}, {random_user_json['results'][0]['location']['state']}, {random_user_json['results'][0]['location']['postcode']}, {random_user_json['results'][0]['location']['country']}"
        dob = random_user_json['results'][0]['dob']['date'][:10]
        date_of_birth = datetime.datetime.strptime(dob, "%Y-%m-%d")
        print(date_of_birth)


        staff = Staff.objects.get(user__username="demo_staff")

        patient = Patient.objects.create(
            user=User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name, email=email),
            date_of_birth = date_of_birth,
            email_verified = 1,
            phone_number=phone_number,
            address=address,
            photo=random_user_image_url,
            registered_by = staff,
            approval_status = 1,
        )
        user_group.user_set.add(patient.user)
        patients.append(patient)
        print(f"finished {patient}")

    return HttpResponse(f"{patients}")




def send_email(request):
    from django.core.mail import EmailMessage
    message = f"""
        Hi,
        This email contains an encrypted PDF file which is supposed to be your prescription.
        THe password of the PDF file is: Reversed last 4 digits of your phone+Your username+Your age without the + sign.
        for example:
        if your phone number is "+911234567890" and your username is "abc" and your age is "20" then your password will be "0987abc20"
        please find the attached pdf file to this email.

        Regards
        Clinic Management System
        """
    mail = EmailMessage(
        subject="Prescription",
        body=message,
        from_email="noreply@clinicmanagement.com",
        to=['test@example.com'],
    )
    with open('static/test/test_pdf.pdf', 'rb') as f:
        mail.attach(f'Prescription.pdf', f.read(), 'application/pdf')
        mail.send()

# def send_email(request):
#     from mailjet_rest import Client
#     import os
#     api_key = '50b1cfc7f6efcc110aed37aa876d3758'
#     api_secret = 'e8598e1b7e43e02aadfa2379670a276f'
#     mailjet = Client(auth=(api_key, api_secret), version='v3.1')
#     data = {
#         'Messages': [
#             {
#                 "From": {
#                     "Email": "hospital.management2022@gmail.com",
#                     "Name": "hospital_m"
#                 },
#                 "To": [
#                     {
#                     "Email": "hospital.management2022@gmail.com",
#                     "Name": "Khudadad"
#                     }
#                 ],
#                 "Subject": "Greetings from Mailjet.",
#                 "TextPart": "My first Mailjet email",
#                 "HTMLPart": "<h3>Dear passenger 1, welcome to <a href='https://www.mailjet.com/'>Mailjet</a>!</h3><br />May the delivery force be with you!",
#                 "CustomID": "AppGettingStartedTest",
#                 'Attachments': [{
#                     'Content-type': 'image/jpeg',
#                     'Filename': 'attachment.jpg',
#                     'content': 'https://www.mailjet.com/images/theme/v3/logo-dark.png'
#                 }]
#            }
#         ]
#     }
#     result = mailjet.send.create(data=data)
#     print (result.status_code)
#     print (result.json())
#     return HttpResponse("Email sent")