from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')  # 원하는 필드 표시
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')

# admin.py
from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')  # 표시할 필드
    list_filter = ('category', 'is_active')  # 필터 옵션
    search_fields = ('name', 'description')  # 검색 필드
    fields = ('name', 'description', 'image', 'category', 'price', 'is_active')  # 폼에 표시할 필드
