from django.contrib.auth.models import User
from django.db import models
from account.models import Doctor, Patient, Staff, Warden


# Create your models here.
class Diagnostic(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    disease = models.CharField(max_length=100)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.disease} | {self.patient.user.first_name} {self.patient.user.last_name}"

class Prescription(models.Model):
    diagnose = models.ForeignKey(Diagnostic, on_delete=models.CASCADE)
    medicine = models.CharField(max_length=100)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medicine} | {self.diagnose.patient.user.first_name} {self.diagnose.patient.user.last_name}"

class MedicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctors = models.ManyToManyField(Doctor, related_name='allowed_doctors')
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient}"

CHOICES = (
    ("check_in", 'check in'),
    ("check_out", 'check out'),
)
class UserCheckInCheckOut(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    checked_in = models.DateTimeField(null=True, blank=True)
    status = models.CharField(choices=CHOICES, max_length=50, default="check_in")
    checked_out = models.DateTimeField(null=True, blank=True)
    warden = models.ForeignKey(Warden, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"