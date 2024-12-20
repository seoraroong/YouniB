from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'  # 네임스페이스 설정

urlpatterns = [
    path('', views.login_register_view, name='login_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # 로그아웃
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/update/', views.profile_update_view, name='profile_update'),  # 기존 프로필 업데이트 URL
    path('profile', views.profile_view, name="profile"),
    path('search/', views.search, name='search'),
]
