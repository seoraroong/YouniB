from django.db import models
from django.conf import settings  # settings.AUTH_USER_MODEL을 가져옵니다.
from studyarchive.models import Course, CourseMaterial
from quizarchive.models import Quiz, SubmissionDetail

# 키워드 모델
class Keyword(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='keywords')  # 사용자와 연결
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='keywords')  # Course와 연결
    course_material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE, related_name='keywords')  # CourseMaterial와 연결
    keyword = models.CharField(max_length=255)  # 저장된 키워드
    question = models.TextField()  # 키워드와 연관된 질문
    relevance_score = models.FloatField(null=True, blank=True)  # 관련성 점수 추가
    created_at = models.DateTimeField(auto_now_add=True) 
    

    def __str__(self):
        return f"Keyword: {self.keyword} (User: {self.user.username})"

    