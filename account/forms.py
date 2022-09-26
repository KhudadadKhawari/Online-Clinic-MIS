from django import forms
from django.contrib.auth.models import User
from .models import Staff, Doctor, Warden, Patient, Admin


class UserProfileForm(forms.ModelForm):
    photo = forms.ImageField(widget=forms.FileInput(attrs={'id':'file','type':'file','onchange':'loadFile(event)'}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type':'date','nmae':'date_of_birth', 'class':'form-control'}), required=False)
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'type':'text','nmae':'phone_number', 'class':'form-control'}), required=False)
    address = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','name':'address','placeholder':'Address'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control','username':'something','placeholder':'Username'}),
            'email': forms.EmailInput(attrs={'class':'form-control','email':'something','placeholder':'Email', 'readonly':'true'}),
            'first_name': forms.TextInput(attrs={'class':'form-control','first_name':'something','placeholder':'First Name'}),
            'last_name': forms.TextInput(attrs={'class':'form-control','last_name':'something','placeholder':'Last Name'}),
        }
    
    def save(self, commit=True):
        user = super(UserProfileForm, self).save(commit=commit)
        l = user.groups.values_list('name', flat=True) # Getting user groups query set
        groups = list(l) # Converting query set to list

        photo = self.cleaned_data.get('photo')
        phone_number = self.cleaned_data.get('phone_number')
        address = self.cleaned_data.get('address')
        if 'patient' in groups:
            patient = Patient.objects.get(user=user)
            patient.phone_number = phone_number
            patient.address = address
            if photo:
                patient.photo = photo
            patient.save()
        elif 'warden' in groups:
            warden = Warden.objects.get(user=user)
            warden.phone_number = phone_number
            warden.address = address
            if photo:
                warden.photo = photo
            warden.save()
        elif 'doctor' in groups:
            doctor = Doctor.objects.get(user=user)
            doctor.phone_number = phone_number
            doctor.address = address
            if photo:
                doctor.photo = photo
            doctor.save()
        elif 'staff' in groups:
            staff = Staff.objects.get(user=user)
            staff.phone_number = phone_number
            staff.address = address
            if photo:
                staff.photo = photo
            staff.save()
        elif 'admin' in groups:
            admin = Admin.objects.get(user=user)
            if photo:
                admin.photo = photo
            admin.save()
        return user
