from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')  # 원하는 필드 표시
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
