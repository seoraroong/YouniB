# studyarchive/models.py

from django.db import models
from django.conf import settings  # settings.AUTH_USER_MODEL을 가져옵니다.
from django.utils import timezone

# 사용자가 직접 생성하는 강의 카테고리 모델
class Course(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # CustomUser를 참조
    year = models.CharField(max_length=4)
    semester = models.CharField(max_length=4)  
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.year} - {self.semester} - {self.name}"


# 강의 카테고리에 해당하는 강의 자료 모델
class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # Course와 연결
    title = models.CharField(max_length=255)  # 강의 자료 제목
    file = models.FileField(upload_to='course_materials/')  # PDF 파일
    description = models.TextField()  # 설명
    upload_date = models.DateTimeField(auto_now_add=True)  # 업로드 날짜와 시간

    # 요약 상태 필드 추가
    SUMMARY_STATUS_CHOICES = [
        ('pending', '요약 중'),
        ('completed', '요약 완료'),
        ('failed', '요약 실패'),
    ]
    summary_status = models.CharField(
        max_length=20,
        choices=SUMMARY_STATUS_CHOICES,
        default='pending',
    )
    
    def __str__(self):
        return f"Material for {self.course.name}: {self.title}"