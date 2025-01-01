from django.shortcuts import render
from quizarchive.models import Quiz, QuizSubmission, SubmissionDetail
from studyarchive.models import CourseMaterial, Course 
from studydashboard.models import Keyword
from accounts.models import CustomUser
from django.http import JsonResponse
from keybert import KeyBERT  # 키워드 추출을 위해 KeyBERT 사용

# 정보가 저장된 DB에서 틀린 문제를 불러와서 키워드 추출을 진행하고 저장시키는 코드
@staticmethod
def extract_and_save_keywords(submission_id):
    """
    is_correct가 False인 SubmissionDetail에서 Quiz 데이터를 가져와
    질문에서 키워드를 추출하고 Keyword 모델에 저장합니다.
    """
    """
    특정 제출 ID의 틀린 문제에서 키워드를 추출하고 저장합니다.
    """
    incorrect_submissions = SubmissionDetail.objects.filter(
        submission_id=submission_id,
        is_correct=False
    )
    
    kw_model = KeyBERT()  # KeyBERT 인스턴스 생성

    for submission in incorrect_submissions:
        quiz = submission.quiz
        quiz_content = quiz.question  # 질문에서만 키워드 추출
        keywords = kw_model.extract_keywords(
            quiz_content,
            keyphrase_ngram_range=(1, 1),  # 단일 단어 키워드만 추출 # 두 단어쌍 또는 세 단어쌍
            stop_words='english',
            top_n=10
        )

        for kw in keywords:
            Keyword.objects.create(
                user=submission.submission.user,  # 제출한 사용자로 설정
                course=quiz.course,  # 연결된 Course 설정
                course_material=quiz.course_material,  # 연결된 CourseMaterial 설정
                keyword=kw[0],  # 키워드 텍스트 저장
                question=quiz.question,
                relevance_score=kw[1]  # 관련성 점수 저장
            )


# 스터디 대시보드 페이지
def studydashboard(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # 전체 학습 진행률 데이터 계산
    progress_data = calculate_overall_progress(request.user)

    # 강의 ID 필터링 (기본값은 'all')
    course_id = request.GET.get('course_id', 'all')

    if course_id == 'all':
        # 모든 강의 자료 가져오기
        course_materials = CourseMaterial.objects.filter(course__user=request.user)
    else:
        # 특정 강의 자료만 가져오기
        course_materials = CourseMaterial.objects.filter(course__id=course_id, course__user=request.user)

    # 강의별 진행률 데이터 계산
    course_progress = []
    for material in course_materials:
        submission_details = SubmissionDetail.objects.filter(
            submission__course_material=material,
            submission__user=request.user
        )
        correct_answers = submission_details.filter(is_correct=True).count()
        total_questions = submission_details.count()

        if total_questions == 0 and correct_answers == 0:
            progress = 0.0
            is_not_attempted = True  # 풀지 않은 상태
        else:
            progress = (correct_answers / total_questions) * 100 if total_questions else 0
            is_not_attempted = False  # 풀었거나 시도했음
            
        course_progress.append({
            "material_title": material.title,
            "progress": round(progress, 2),
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "is_not_attempted": is_not_attempted,  # 상태값 추가
        })

    # 필터에 사용할 강의 데이터 (중복 제거)
    courses = Course.objects.filter(user=request.user).values('id', 'name').distinct()

    # 대시보드 화면 렌더링
    return render(request, 'studydashboard.html', {
        "progress_data": progress_data,
        "course_progress": course_progress,
        "courses": courses,  # 강의 필터 옵션 데이터
    })
    
# 전체 진행률 계산 (전체 퀴즈 풀이 진행률)
def calculate_overall_progress(user):
    # 전체 생성된 퀴즈 수
    total_quizzes = Quiz.objects.filter(user=user).count()

    # 제출된 퀴즈 수
    submissions = QuizSubmission.objects.filter(user=user)
    completed_questions = sum(submission.total_questions for submission in submissions)

    if total_quizzes == 0:
        return {"progress": 0, "completed_questions": 0, "total_quizzes": 0}

    progress = (completed_questions / total_quizzes) * 100
    return {
        "progress": round(progress, 2),
        "completed_questions": completed_questions,
        "total_quizzes": total_quizzes,
    }


# 강의별 진행률 계산
def calculate_course_progress(user):
    submissions = QuizSubmission.objects.filter(user=user)
    course_progress = []

    for submission in submissions:
        # ZeroDivision Error 방지
        if submission.total_questions == 0:
            progress = 0.0
        else:
            progress = (submission.correct_answers / submission.total_questions) * 100
        
        course_progress.append({
            "course_material_id": submission.course_material_id,
            "progress": round(progress, 2),
            "total_questions": submission.total_questions,
            "correct_answers": submission.correct_answers,
        })

    return course_progress

# 학습 진행률 API
def get_progress(request):
    if request.user.is_authenticated:
        progress_data = calculate_overall_progress(request.user)
        course_progress = calculate_course_progress(request.user)
        return JsonResponse({
            "progress_data": progress_data,
            "course_progress": course_progress,
        })
    else:
        return JsonResponse({"error": "Unauthorized"}, status=401)