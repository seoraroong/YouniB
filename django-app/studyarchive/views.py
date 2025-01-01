from django.shortcuts import render, redirect
from .models import Course, CourseMaterial
from quizarchive.models import Quiz
from quizarchive.models import Summary
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import logging
import threading
import requests
from django.http import JsonResponse
from django.contrib.auth.models import User
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import OuterRef, Subquery
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

@login_required
def studyarchive_view(request):
    if request.method == "POST":
        # POST 요청으로 강의 추가
        year = request.POST['year']
        semester = request.POST['semester']
        course_name = request.POST['course_name']
        
        # 강의 추가
        Course.objects.create(user=request.user, year=year, semester=semester, name=course_name)
        
        # 강의 추가 후 리디렉션
        return redirect('studyarchive:studyarchive')
    
    # GET 요청 시 강의 목록을 보여줍니다.
    courses = Course.objects.filter(user=request.user)

    # 모든 강의 자료를 최신순으로 가져오기
    course_materials = CourseMaterial.objects.filter(course__user=request.user).order_by('-upload_date')

    return render(request, 'index.html', {'courses': courses})


@login_required
def upload_course_material(request, course_id):
    if request.method == 'POST':
        # 강의 가져오기
        course = get_object_or_404(Course, id=course_id)

        # 제목, 설명, 파일 가져오기
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')  # 파일 업로드

        if not title or not description or not file:
            return JsonResponse({'success': False, 'message': '모든 필드를 작성해주세요.'})

        # DB에 강의 자료 저장
        course_material = CourseMaterial.objects.create(
            course=course,
            title=title,
            description=description,
            file=file
        )

        # FastAPI 서버로 파일을 보내는 작업을 비동기로 처리
        threading.Thread(
            target=send_file_to_fastapi,
            args=(course_material.file.path, course_material.id)
        ).start()

        # 업로드 성공 응답
        return JsonResponse({'success': True, 'message': '자료가 업로드되었습니다.'})

    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 알림 전송 함수
def send_notification_to_user(user_id, message):
    try:
        channel_layer = get_channel_layer()
        logger.debug(f"Sending notification to user {user_id}: {message}")
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "user_notification",
                "message": message,
            },
        )
        logger.info(f"Notification sent to user {user_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")

    
# 업로드된 파일을 FastAPI 서버로 전송하는 함수
def send_file_to_fastapi(file_path, course_material_id):
    fastapi_url = "http://127.0.0.1:8080/process-pdf"

    try:
        logging.info(f"Sending file: {file_path} with course_material_id: {course_material_id}")
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'course_material_id': course_material_id}
            response = requests.post(fastapi_url, files=files, data=data, timeout=600)
        
        # FastAPI 응답 로그 기록
        logging.info(f"FastAPI response status code: {response.status_code}")
        logging.info(f"FastAPI response content: {response.text}")

        # 응답 처리
        if response.status_code == 200:
            response_data = response.json()
            message = response_data.get("message", "")

            # 메시지에 따라 summary_status 업데이트
            if message == "PDF 처리 및 모델 추론 성공":
                CourseMaterial.objects.filter(id=course_material_id).update(summary_status="completed")
                logging.info(f"Summary status updated to 'completed' for material ID {course_material_id}")
            elif message == "Quiz saved successfully.":
                CourseMaterial.objects.filter(id=course_material_id).update(summary_status="quiz_completed")
                logging.info(f"Summary status updated to 'quiz_completed' for material ID {course_material_id}")
            elif message == "Summary saved successfully.":
                CourseMaterial.objects.filter(id=course_material_id).update(summary_status="summary_saved")
                logging.info(f"Summary status updated to 'summary_saved' for material ID {course_material_id}")
            else:
                CourseMaterial.objects.filter(id=course_material_id).update(summary_status="failed")
                logging.warning(f"Unrecognized message: {message}. Summary status updated to 'failed' for material ID {course_material_id}")
            
            return response_data
        else:
            # 실패 상태 업데이트
            CourseMaterial.objects.filter(id=course_material_id).update(summary_status="failed")
            raise Exception(f"Failed to send file. Status code: {response.status_code}")
 
    except requests.RequestException as e:
        # 네트워크 오류 또는 예외 발생 시 상태를 "failed"로 업데이트
        logging.error(f"Failed to send file to FastAPI: {e}")
        CourseMaterial.objects.filter(id=course_material_id).update(summary_status="failed")
        raise
    
@method_decorator(csrf_exempt, name='dispatch')
class SaveQuizView(View):
    def post(self, request):
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            logger.debug(f"Received data: {data}")
            
            course_material_id = data.get("course_material_id")
            results = data.get("results")
            
            if not course_material_id or not results:
                return JsonResponse({"status": "error", "message": "Missing required data."}, status=400)

            # 강의자료 및 관련 정보 확인
            course_material = CourseMaterial.objects.get(id=course_material_id)
            course = course_material.course
            user = course_material.course.user

            # Quiz 모델에 데이터 저장
            for result in results:
                question_type = result.get("question_type")
                if question_type not in ["MCQ", "SAQ"]:
                    return JsonResponse(
                        {"status": "error", "message": f"Invalid question_type: {question_type}"}, 
                        status=400
                    )

                # Quiz 데이터 저장
                quiz_data = {
                    "user": user,
                    "course": course,
                    "course_material": course_material,
                    "question_type": question_type,
                    "question": result["question"],
                    "answer": result["answer"],
                    "start_page": result["start_page"],
                    "end_page": result["end_page"],
                    "title": f"{course_material.title}_퀴즈"
                }
                print('장고의 views.py의 savequizview 클래스')
                print(quiz_data)

                # 객관식일 경우 options 추가
                if question_type == "MCQ":
                    quiz_data["options"] = result.get("options", [])

                # Quiz 저장
                Quiz.objects.create(**quiz_data)

            # 알림 전송
            send_notification_to_user(
                user_id=user.id,
                message=f"{course_material.title} 자료에 대한 새로운 퀴즈가 추가되었습니다."
            )
            
            return JsonResponse({"status": "success", "message": "Quiz saved successfully."})

        except CourseMaterial.DoesNotExist:
            logger.error("CourseMaterial not found.")
            return JsonResponse({"status": "error", "message": "CourseMaterial not found."}, status=404)

        except KeyError as e:
            logger.error(f"Missing key: {str(e)}")
            return JsonResponse({"status": "error", "message": f"Missing key: {str(e)}"}, status=400)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse({"status": "error", "message": f"Error: {str(e)}"}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SaveSummaryView(View):
    def post(self, request):
        try:
            # 요청 데이터 파싱
            data = json.loads(request.body)
            logger.debug(f"Received data: {data}")

            course_material_id = data.get("course_material_id")
            results = data.get("results")

            if not course_material_id or not results:
                return JsonResponse({"status": "error", "message": "Missing required data."}, status=400)

            # 강의자료 및 관련 정보 확인
            course_material = CourseMaterial.objects.get(id=course_material_id)
            course = course_material.course
            user = course_material.course.user

            # Summary 모델에 데이터 저장
            for result in results:
                Summary.objects.create(
                    user=user,
                    course=course,
                    course_material=course_material,
                    summary_text=result["summary_text"],
                )
            
            # 알림 전송
            send_notification_to_user(
                user_id=user.id,
                message=f"{course_material.title} 자료의 요약이 성공적으로 저장되었습니다."
            )

            return JsonResponse({"status": "success", "message": "Summary saved successfully."})

        except CourseMaterial.DoesNotExist:
            return JsonResponse({"status": "error", "message": "CourseMaterial not found."}, status=404)

        except KeyError as e:
            return JsonResponse({"status": "error", "message": f"Missing key: {str(e)}"}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error: {str(e)}"}, status=500)

@login_required
def delete_material(request, material_id):
    try:
        # 해당 자료 가져오기
        material = get_object_or_404(CourseMaterial, id=material_id, course__user=request.user)
        material.delete()  # 자료 삭제
        return JsonResponse({'success': True})
    except CourseMaterial.DoesNotExist:
        return JsonResponse({'success': False}, status=400)


@login_required
def edit_material(request, material_id):
    if request.method == 'POST':
        # 해당 자료 찾기
        material = get_object_or_404(CourseMaterial, id=material_id, course__user=request.user)
        
        # 수정된 데이터 받아오기
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')  # 파일이 있을 경우 새 파일을 받음

        # 자료 수정
        if title:
            material.title = title
        if description:
            material.description = description
        if file:
            material.file = file
        
        material.save()  # 변경사항 저장

        return JsonResponse({'success': True, 'message': '자료가 수정되었습니다.'})
    else:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 강의 자료 목록을 반환하는 뷰 추가
@login_required
def show_course_materials(request, course_id):
    # 해당 강의 조회
    course = get_object_or_404(Course, id=course_id, user=request.user)
    
    # 강의에 연결된 자료 목록 가져오기
    materials = CourseMaterial.objects.filter(course=course)
    
    # 자료 목록을 제목만 반환
    materials_data = [
        {
            'id': material.id,
            'title': material.title,
            'summary_status': material.summary_status
        }
        for material in materials
    ]
    
    return JsonResponse({
        'course_name': course.name,
        'materials': materials_data,
    })

# 자료 상세보기 페이지
@login_required
def material_detail(request, material_id):
    # 해당 자료 가져오기
    material = get_object_or_404(CourseMaterial, id=material_id)
    
    return JsonResponse({
        'material': {
            'title': material.title,
            'description': material.description,
            'file_url': material.file.url,
            'summary_status': material.summary_status
        }
    })

# 사용자가 추가한 강의를 모달을 통해 삭제하는 뷰
@login_required  # 사용자가 로그인된 상태에서만 삭제 가능
def delete_course(request, course_id):
    try:
        # 해당 강의가 존재하는지 확인
        course = Course.objects.get(id=course_id, user=request.user)
        course.delete()  # 강의 삭제
        return JsonResponse({'success': True})  # 삭제 성공
    except Course.DoesNotExist:
        return JsonResponse({'success': False}, status=400)  # 강의가 존재하지 않으면 실패
    

def course_materials(request, course_id):
    try:
        # Course 정보 가져오기
        course = Course.objects.get(id=course_id)
        course_data = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
        }
        
        # CourseMaterial 정보 가져오기
        materials = CourseMaterial.objects.filter(course_id=course_id).values(
            "id", "title", "summary_status"
        )
        
        # 각 CourseMaterial에 연결된 Summary의 summary_text 추가
        materials_data = []
        for material in materials:
            summary = Summary.objects.filter(course_material_id=material["id"]).first()
            material_data = {
                "id": material["id"],
                "title": material["title"],
                "summary_status": material["summary_status"],
                "summary_text": summary.summary_text if summary else None
            }
            materials_data.append(material_data)
        
        # Course와 CourseMaterial을 합쳐 반환
        response_data = {
            "course": course_data,
            "materials": materials_data,
        }
        return JsonResponse(response_data, safe=False)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    
# "요약 보기" 데이터 반환 뷰
@login_required
def get_summary(request, material_id):
    try:
        # 해당 자료 가져오기
        material = get_object_or_404(CourseMaterial, id=material_id, course__user=request.user)

        # 요약 상태 확인
        if material.summary_status != "completed":
            return JsonResponse({"error": "Summary not available"}, status=400)
        
        # Summary 모델에서 데이터 가져오기
        summaries = Summary.objects.filter(course_material=material)
        
        if not summaries:
            return JsonResponse({"error": "Summary not found"}, status=404)
        summary_texts = [summary.summary_text for summary in summaries if summary.summary_text]
    
        # 요약 데이터를 반환
        return JsonResponse({"summary_texts": summary_texts})

    except CourseMaterial.DoesNotExist:
        return JsonResponse({"error": "Material not found"}, status=404)
