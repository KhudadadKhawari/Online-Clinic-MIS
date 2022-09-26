from fpdf import FPDF
from PyPDF2 import PdfFileReader, PdfFileWriter
from datetime import datetime
from django.core.mail import EmailMessage
import os


def generate_file_name():
    return f'prescription{datetime.now()}'.replace(':', '').replace(' ', '')


def encrypt_pdf(file, patient):
    encrypted_output = PdfFileWriter()
    the_file = PdfFileReader(file)
    number_of_pages = the_file.numPages
    for page in range(number_of_pages):
        encrypted_output.addPage(the_file.getPage(page))

    password = f"{patient.phone_number[:-5:-1]}{patient.user.username}{patient.age}"
    encrypted_output.encrypt(password)
    with open(file, 'wb') as f:
        encrypted_output.write(f)
    
    return file

def create_pdf(patient, diagnostic):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=16)
        pdf.cell(200, 10, txt=f'Doctor\'s Name: {diagnostic.doctor.user.first_name} {diagnostic.doctor.user.last_name}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Patient\'s Name: {patient.user.first_name} {patient.user.last_name}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Age: {patient.age}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Prescreption\'s Date Created: {datetime.now()}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'____________________________________________________________________________', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Disease: {diagnostic.disease}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Description: {diagnostic.description}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'Diagnose Date: {diagnostic.created}', ln=1, align='L')
        pdf.cell(200, 10, txt=f'____________________________________________________________________________', ln=1, align='L')
        
        for prescription in diagnostic.prescription_set.all():
            pdf.cell(200, 10, txt=prescription.medicine, ln=1)
            pdf.cell(200, 10, txt=prescription.description, ln=1)
            pdf.cell(200, 10, txt='_________________________________', ln=1)

        file = f'static/{generate_file_name()}.pdf'
        pdf.output(file)
        encrypted_file = encrypt_pdf(file, patient)

        return encrypted_file
    except Exception as e:
        return e


def send_to_email(file, email):
    try:
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
            to=[email],
        )
        with open(file, 'rb') as f:
            mail.attach(f'Prescription.pdf', f.read(), 'application/pdf')
            mail.send()
        os.remove(file) # remove file after sendint to email
    except Exception as e:
        return e