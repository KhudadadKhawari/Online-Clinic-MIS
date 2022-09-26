from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def profile_image_url(self, instance):
        return f"static/images/profile_images/{instance}"
    
    photo = models.ImageField(upload_to=profile_image_url, default='static/images/profile_images/default.jpg')

    def __str__(self) -> str:
        return self.user.username

class Staff(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)

    def profile_image_url(self, instance):
        return f"static/images/profile_images/{instance}"

    photo = models.ImageField(upload_to=profile_image_url, default='static/images/profile_images/default.jpg')

    def __str__(self):
        return f"{self.user.username}"


class Doctor(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)

    def profile_image_url(self, instance):
        return f"static/images/profile_images/{instance}"

    photo = models.ImageField(upload_to=profile_image_url, default='static/images/profile_images/default.jpg')

    def __str__(self):
        return f"{self.user.username}"


class Warden(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)

    def profile_image_url(self, instance):
        return f"static/images/profile_images/{instance}"

    photo = models.ImageField(upload_to=profile_image_url, default='static/images/profile_images/default.jpg')

    def __str__(self):
        return f"{self.user.username}"


class Patient(models.Model):
    doctors = models.ManyToManyField(Doctor, related_name='doctors', blank=True)
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100,null=True)
    date_of_birth = models.DateField(null=True)
    email_verified = models.IntegerField(default=0) # 0 = not verified, 1 = verified
    registered_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    approval_status = models.IntegerField(default=0) # 0: Pending , 1: approved, 2: rejected
    date_created = models.DateTimeField(auto_now_add=True)

    def profile_image_url(self, instance):
        return f"static/images/profile_images/{instance}"

    photo = models.ImageField(upload_to=profile_image_url, default='static/images/profile_images/default.jpg')


    @property
    def age(self):
        return int((datetime.now().date() - self.date_of_birth).days/365.25)

    def __str__(self):
        return f"{self.user.username}"
