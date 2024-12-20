from django.db import models
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="User ID"
    )
    email = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=128, verbose_name="Password")
    profile_image = models.ImageField(
        upload_to='profile_images/',  # 업로드할 경로
        blank=True,
        null=True,
        verbose_name="Profile Image",
        default='profile_images/default_profile.png'  # 기본 이미지 경로
    )
    school = models.CharField(max_length=100, blank=True, null=True, verbose_name="School")
    major = models.CharField(max_length=100, blank=True, null=True, verbose_name="Major")


    first_name = None  # 기본 AbstractUser 필드 제거
    last_name = None   # 기본 AbstractUser 필드 제거

    def __str__(self):
        return self.username
