from django.urls import path
from . import views

app_name = 'quizarchive'

urlpatterns = [
    path('', views.quizarchive_view, name='quizarchive'),
    # path('materials_quiz/<int:material_id>/', views.show_materials_quiz, name='show_materials_quiz'),  # 강의별 퀴즈 목록
    # path('quiz_detail/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),  # 퀴즈 상세보기
]