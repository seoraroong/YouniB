from django.urls import path
from . import views

app_name = 'studyarchive'

urlpatterns = [
    path('', views.studyarchive_view, name='studyarchive'),
    path('course_materials/<int:course_id>/', views.show_course_materials, name='show_course_materials'),  # 강의 자료 목록
    path('material_detail/<int:material_id>/', views.material_detail, name='material_detail'),  # 자료 상세보기
    path('delete/<int:course_id>/', views.delete_course, name='delete_course'),  # 강의 삭제   # 기본 페이지
    path('upload_material/<int:course_id>/', views.upload_course_material, name='upload_course_material'),
    path('delete_material/<int:material_id>/', views.delete_material, name='delete_material'),
    path('edit_material/<int:material_id>/', views.edit_material, name='edit_material'),
]
