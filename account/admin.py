from django.contrib import admin
from .models import Patient, Staff, Doctor, Warden, Admin

# Register your models here.
admin.site.register(Patient)
admin.site.register(Staff)
admin.site.register(Doctor)
admin.site.register(Warden)
admin.site.register(Admin)