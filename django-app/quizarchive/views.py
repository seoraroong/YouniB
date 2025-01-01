from django.shortcuts import render, redirect
from studyarchive.models import Course, CourseMaterial
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import QuizSubmission, SubmissionDetail, Quiz
from studyarchive.models import Course
from django.utils import timezone
import json
import logging
from studydashboard.views import extract_and_save_keywords


logger = logging.getLogger(__name__)

@login_required
def quizarchive_view(request):
    """
    사용자의 강의 목록을 조회하여 퀴즈 아카이브 페이지를 렌더링합니다.
    """
    courses = Course.objects.filter(user=request.user)
    return render(request, 'quiz_index.html', {'courses': courses})

def quiz_list_by_material(request, course_material_id):
    """
    특정 강의 자료(course_material_id)에 대한 퀴즈 목록 반환
    """
    quizzes = Quiz.objects.filter(course_material__id=course_material_id).values(
        'id', 'title', 'question', 'options', 'answer', 'question_type', 'course_material_id'
    )
    return JsonResponse({
        "quizzes": list(quizzes),
        "course_material_id": course_material_id 
    })

def quiz_list_by_course(request, course_id):
    """
    특정 강의(course_id)에 대한 퀴즈 목록 반환 (course_material_id 기준 중복 제거)
    """
    quizzes = Quiz.objects.filter(course__id=course_id).values('course_material_id', 'title','question_type').distinct()
    return JsonResponse({
        "quizzes": list(quizzes)
    })
    
    
def quiz_detail(request, quiz_id):
    """
    특정 퀴즈(quiz_id)의 상세 정보를 반환하는 뷰
    """
    try:
        # 퀴즈 조회
        quiz = Quiz.objects.get(id=quiz_id)
        
        # JSON 형태로 반환
        return JsonResponse({
            "title": quiz.title,
            "question": quiz.question,
            "options": quiz.options,  # JSONField는 그대로 반환 가능
            "answer": quiz.answer,
            "type": quiz.question_type
        })
    except Quiz.DoesNotExist:
        return JsonResponse({"error": "Quiz not found"}, status=404)


def materials(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        materials = CourseMaterial.objects.filter(course=course).values('id', 'title')

        return JsonResponse({
            "course_name": course.name,
            "materials": list(materials)
        })
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)
    
def save_quiz_submission(request):
    if request.method == "POST":
        user = request.user
        data = json.loads(request.body)
        logger.debug("수신된 데이터: %s", data)  # 수신된 데이터 로그 출력
        
        material_id = data.get('material_id')
        if not material_id:
            return JsonResponse({"error": "material_id가 전달되지 않았습니다."}, status=400)

        user_answers = data.get('user_answers')
        if not user_answers:
            return JsonResponse({"error": "user_answers가 전달되지 않았습니다."}, status=400)

        # 중복 제출 방지 테스트용 코드 (임시로 기존 제출 삭제)
        QuizSubmission.objects.filter(user=user, course_material_id=material_id).delete()

        # 중복 제출 방지
        if QuizSubmission.objects.filter(user=user, course_material_id=material_id).exists():
            return JsonResponse({"error": "You have already submitted this quiz."}, status=400)

        correct_count = 0
        total_questions = len(user_answers)

        # 퀴즈 제출 저장
        submission = QuizSubmission.objects.create(
            user=user,
            course_material_id=material_id,
            total_questions=total_questions,
            correct_answers=0,
            submitted_at=timezone.now()
        )

        # Quiz 객체 캐싱 (keys를 정수형으로 변환하여 조회)
        quiz_ids = list(map(int, user_answers.keys()))  # user_answers의 키를 정수형으로 변환
        quizzes = Quiz.objects.filter(id__in=quiz_ids)
        quiz_dict = {quiz.id: quiz for quiz in quizzes}  # quiz_dict 키를 정수형으로 설정

        # 비교 결과를 저장할 리스트
        results = []

        # 각 문제의 정/오답 판단 및 저장
        for quiz_id_str, user_answer in user_answers.items():
            try:
                quiz_id = int(quiz_id_str)  # 키를 정수형으로 변환
                quiz = quiz_dict.get(quiz_id)
                if not quiz:
                    logger.warning(f"Quiz ID {quiz_id}가 존재하지 않습니다.")
                    continue  # 존재하지 않는 quiz_id 무시
            except ValueError:
                logger.warning(f"Invalid quiz_id 형식: {quiz_id_str}")
                continue  # 잘못된 quiz_id 형식 무시

            # 단답식, 객관식 구별 없이 첫글자만 비교해서 정답여부 판별(객관식, 단답식 따라 다르게 처리 필요함)
            user_answer_clean = user_answer.strip()[0]
            logger.debug(f"정제된 사용자 답변: {user_answer_clean} (원본: {user_answer})")  
            print(f"정제된 사용자 답변: {user_answer_clean} (원본: {user_answer})")
            
            correct_answer_clean = quiz.answer.strip()[0]
            logger.debug(f"정제된 정답: {correct_answer_clean}")
            print(f"정제된 정답: {correct_answer_clean}")  # 터미널 출력

            is_correct = (correct_answer_clean == user_answer_clean)
            if is_correct:
                correct_count += 1

            # SubmissionDetail 저장
            SubmissionDetail.objects.create(
                submission=submission,
                quiz=quiz,
                user_answer=user_answer,
                is_correct=is_correct
            )

            # 결과 리스트에 문제, 사용자의 답, 정답 추가
            results.append({
                "question": quiz.question,
                "user_answer": user_answer,
                "correct_answer": quiz.answer,
                "is_correct": is_correct
            })

        # 맞춘 문제 수 업데이트
        submission.correct_answers = correct_count
        submission.save()
        
        extract_and_save_keywords(submission.id)

        # JSON 응답으로 비교 결과 반환
        return JsonResponse({
            "message": "Submission saved successfully.",
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "results": results  # 비교 결과 추가
        })