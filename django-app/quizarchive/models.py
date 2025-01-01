from django.db import models
from django.conf import settings
from studyarchive.models import Course, CourseMaterial
from django.utils import timezone
from django.utils.timezone import now


class Quiz(models.Model):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice Question'),  # 객관식
        ('SAQ', 'Short Answer Question')      # 단답형
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자 참조
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # 코스 참조
    course_material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE)  # 강의자료 참조
    question_type = models.CharField(max_length=3, choices=QUESTION_TYPES)  # 문제 유형
    question = models.TextField()  # 문제 내용
    options = models.JSONField(blank=True, null=True)  # 선택지(객관식만 해당), JSON 형식으로 저장
    answer = models.TextField()  # 정답
    start_page = models.IntegerField()  # 시작 페이지
    end_page = models.IntegerField()  # 종료 페이지
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    title = models.CharField(max_length=255) 

    class Meta:
        ordering = ['-created_at']  # 최신 생성된 퀴즈가 먼저 보이도록 설정

    def __str__(self):
        return f"Quiz ({self.get_question_type_display()}) for {self.course_material.title} by {self.user.username}" 
    
    
class QuizSubmission(models.Model):
    """
    사용자의 퀴즈 제출 기록을 저장하는 모델
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')  # 사용자 참조
    course_material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE, related_name='submissions')
    total_questions = models.PositiveIntegerField()  # 전체 문제 수
    correct_answers = models.PositiveIntegerField()  # 맞춘 문제 수
    submitted_at = models.DateTimeField(default=timezone.now)  # 제출 시간

    def __str__(self):
        return f"{self.user.username} - {self.course_material.title} ({self.submitted_at})"

    def is_today_submission(self):
        """오늘의 문제 제출 여부 확인"""
        return self.submitted_at.date() == now().date()

class SubmissionDetail(models.Model):
    """
    사용자의 각 문제에 대한 답안과 정/오답 여부를 저장하는 모델
    """
    submission = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name='details')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submission_details')
    user_answer = models.CharField(max_length=255)  # 사용자가 선택한 답변
    is_correct = models.BooleanField()  # 정/오답 여부

    def __str__(self):
        return f"{self.quiz.title} - {'Correct' if self.is_correct else 'Wrong'}"
    

class Summary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자 참조
    course = models.ForeignKey(Course, on_delete=models.CASCADE)  # 코스 참조
    course_material = models.ForeignKey(CourseMaterial, on_delete=models.CASCADE)  # 강의자료 참조
    summary_text = models.TextField()  # 요약 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간

    class Meta:
        ordering = ['-created_at']  # 최신 요약이 먼저 보이도록 설정

    def __str__(self):
        return f"Summary for {self.course_material.title} by {self.user.username}"
