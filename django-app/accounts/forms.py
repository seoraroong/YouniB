from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

# 회원가입 폼
class CustomUserCreationForm(UserCreationForm):
    profile_image = forms.ImageField(required=False, label="Profile Image")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'profile_image']
        labels = {
            'username': 'User ID',
            'email': 'Email Address',
            'password1': 'Password',
            'password2': 'Confirm Password',
            'profile_image': 'Profile Image',
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2

    def save(self, commit=True):
        # Save user without committing to the database yet
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Set the hashed password
        if commit:
            user.save()
        return user

# 프로필 수정 폼
class CustomUserChangeForm(UserChangeForm):
    """
    프로필 수정 시 사용할 폼.
    비밀번호 필드는 제외하고 사용자명, 이메일, 프로필 이미지만 수정 가능.
    """
    password = None  # 비밀번호는 수정 폼에서 제외

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_image', 'school', 'major']
