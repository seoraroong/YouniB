from django.urls import path
from . import views

app_name = 'studydashboard'

urlpatterns = [
    path('', views.studydashboard, name='studydashboard'),  # 기본 스터디 대시보드 페이지
    path('progress/', views.get_progress, name='get_progress'),
]
