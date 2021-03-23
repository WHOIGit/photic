from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    # TODO: username/password fields are still being auto-filled in by Chrome
    username = forms.CharField(widget=forms.TextInput(
        attrs={"placeholder": "Username", "autocomplete": "new-password"}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={"placeholder": "Password", "autocomplete": "new-password"}
    ))


class UserForm(forms.ModelForm):
    new_password = forms.CharField(required=False, widget=forms.PasswordInput(

    ))
    confirm_password = forms.CharField(required=False, widget=forms.PasswordInput(

    ))

    def clean_first_name(self):
        if not self.cleaned_data["first_name"]:
            raise forms.ValidationError("First Name is required")

        return self.cleaned_data["first_name"]

    def clean_last_name(self):
        if not self.cleaned_data["last_name"]:
            raise forms.ValidationError("Last Name is required")

        return self.cleaned_data["last_name"]

    def clean_confirm_password(self):
        if "new_password" not in self.cleaned_data or self.cleaned_data["new_password"] == "":
            return ""

        if self.cleaned_data["new_password"] != self.cleaned_data["confirm_password"]:
            raise forms.ValidationError("Passwords do not match")

        return self.cleaned_data["confirm_password"]

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', "is_staff", "is_active" )
        widgets = {
            'first_name': forms.TextInput(attrs={'required': ''}),
            'last_name': forms.TextInput(attrs={'required': ''}),
            'email': forms.TextInput(attrs={'required': ''}),
            'username': forms.TextInput(attrs={'required': ''}),
        }
        labels = {
                    "first_name": "First Name*",
                    "last_name": "Last Name*",
                    "email": "Email Address*",
                    "username": "User Name*"
                }
