from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, LearnerProfile

class SignUpForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill px-4',
        'placeholder': 'Choose a cool username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control rounded-pill px-4',
        'placeholder': 'Secret password'
    }))
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select rounded-pill px-4'
    }))
    age = forms.IntegerField(min_value=5, max_value=15, initial=8, widget=forms.NumberInput(attrs={
        'class': 'form-control rounded-pill px-4',
        'placeholder': 'Your Age (5-15)'
    }))
    learning_style = forms.ChoiceField(choices=LearnerProfile.STYLE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select rounded-pill px-4'
    }))

    class Meta:
        model = CustomUser
        fields = ['username', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Automatically create default LearnerProfile
            LearnerProfile.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                learning_style=self.cleaned_data['learning_style']
            )
        return user

class LearnerProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = LearnerProfile
        fields = ['age', 'learning_style', 'difficulty_level', 'avatar']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control rounded-pill px-4'}),
            'learning_style': forms.Select(attrs={'class': 'form-select rounded-pill px-4'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-select rounded-pill px-4'}),
            'avatar': forms.Select(attrs={'class': 'form-select rounded-pill px-4'}),
        }
