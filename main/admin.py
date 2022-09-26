from django.contrib import admin
from .models import Diagnostic, Prescription, MedicalHistory, UserCheckInCheckOut

# Register your models here.
admin.site.register(Diagnostic)
admin.site.register(Prescription)
admin.site.register(MedicalHistory)
admin.site.register(UserCheckInCheckOut)