from django.shortcuts import render, redirect
from .models import Course, CourseMaterial
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import logging

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
        # 강의 ID에 해당하는 강의를 찾기
        course = get_object_or_404(Course, id=course_id)

        # 폼 데이터에서 제목, 설명, 파일을 받아옵니다.
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')  # 업로드된 파일 받기

        if not title or not description or not file:
            return JsonResponse({'success': False, 'message': '모든 필드를 작성해주세요.'})

        # CourseMaterial 모델에 새 자료를 추가
        course_material = CourseMaterial.objects.create(
            course=course,
            title=title,
            description=description,
            file=file
        )

        # PDF 파일이 업로드된 후, FastAPI 서버로 전달
        try:
            # FastAPI 서버로 파일 전송
            file_path = course_material.file.path  # 업로드된 파일의 경로
            response_data = send_file_to_fastapi(file_path)  # FastAPI 서버에서 처리 후 결과 받기

            # 처리된 결과를 Django DB에 저장하거나, 추가 작업을 수행할 수 있습니다
            # 예를 들어:
            # course_material.processing_result = response_data['result']
            # course_material.save()

            return JsonResponse({'success': True, 'message': '자료가 업로드되었습니다.', 'result': response_data})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f"파일 처리 중 오류 발생: {str(e)}"})

    else:
        return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# 업로드된 파일을 FastAPI 서버로 전송하는 함수
def send_file_to_fastapi(file_path):
    fastapi_url = "http://127.0.0.1:5000/process-pdf"  # FastAPI 서버 URL
    logging.debug(f"Sending file to FastAPI: {file_path}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(fastapi_url, files=files)

        if response.status_code != 200:
            raise Exception(f"Failed to send file. Status code: {response.status_code}")
        
        logging.debug(f"FastAPI Response: {response.json()}")
        return response.json()

    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        raise Exception("Error during file upload to FastAPI.")


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