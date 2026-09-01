from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Candidate


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Your OTP will be sent here.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        label="6-digit code",
        widget=forms.TextInput(attrs={"autofocus": True, "inputmode": "numeric", "placeholder": "123456"}),
    )


class VoteForm(forms.Form):
    candidate = forms.ModelChoiceField(
        queryset=Candidate.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,
        label="Choose one candidate",
    )
