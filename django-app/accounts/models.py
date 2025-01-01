from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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

    # 경험치 필드 추가
    experience_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Experience Points"
    )
    
    first_name = None  # 기본 AbstractUser 필드 제거
    last_name = None   # 기본 AbstractUser 필드 제거

    def __str__(self):
        return self.username
    
    def add_experience(self, points):
        """경험치 추가"""
        self.experience_points += points
        self.save()

    def subtract_experience(self, points):
        """경험치 차감 (아이템 구매)"""
        if points <= 0:
            raise ValueError("차감할 경험치는 0보다 커야 합니다.")
        if self.experience_points >= points:
            self.experience_points -= points
            self.save()
            return True
        return False

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('hat', 'Hat'),
        ('clothing', 'Clothing'),
        ('accessory', 'Accessory'),
    ]

    name = models.CharField(max_length=100, verbose_name="Item Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(
        upload_to='item_images/', 
        blank=True, 
        null=True, 
        verbose_name="Item Image"
    )
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        verbose_name="Category"
    )
    price = models.PositiveIntegerField(verbose_name="Price (Experience Points)")
    is_active = models.BooleanField(default=True, verbose_name="Available for Purchase")

    def __str__(self):
        return self.name
    

class UserItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user_items',
        verbose_name="User"
    )
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE, 
        related_name='owned_by',
        verbose_name="Item"
    )
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Purchase Date")
    is_equipped = models.BooleanField(default=False, verbose_name="Equipped")

    class Meta:
        unique_together = ('user', 'item')  # 하나의 아이템은 한 사용자가 한 번만 소유 가능

    def __str__(self):
        return f"{self.user.username} - {self.item.name}"