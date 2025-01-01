"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views  # accounts 앱의 views를 가져옴


urlpatterns = [
    path('', account_views.login_register_view, name='login_register'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  
    path('dashboard/', account_views.dashboard_view, name='dashboard'),
    path('studyarchive/', include('studyarchive.urls')),
    path('quizarchive/', include('quizarchive.urls')),
    path('studydashboard/', include('studydashboard.urls')),
]

# 미디어 파일 제공 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)