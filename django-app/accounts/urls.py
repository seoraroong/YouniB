from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'  # 네임스페이스 설정

urlpatterns = [
    path('', views.login_register_view, name='login_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # 로그아웃
    path('register/', views.register_view, name='register'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile', views.profile_view, name="profile"),
    path('api/search/', views.search, name="search"),
    path('purchase/<int:item_id>/', views.purchase_item, name='purchase_item'),
    path('equip/<int:user_item_id>/', views.equip_item, name='equip_item'),
    path('unequip/<int:user_item_id>/', views.unequip_item, name='unequip_item'),
    path('solve-problem/', views.solve_problem, name='solve_problem'),
    path('get-today-problem/', views.get_today_problem, name='get_today_problem'),
]