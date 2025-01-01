from django.urls import path
from . import views

app_name = 'quizarchive'

urlpatterns = [
    path('', views.quizarchive_view, name='quizarchive'),
    path('quiz_list_by_course/<int:course_id>/', views.quiz_list_by_course, name='quiz_list_by_course'),
    path('quiz_list_by_material/<int:course_material_id>/', views.quiz_list_by_material, name='quiz_list_by_material'),
    path('quiz_detail/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('save_quiz_submission/', views.save_quiz_submission, name='save_quiz_submission'),
]