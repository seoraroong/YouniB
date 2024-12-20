from django.shortcuts import render, redirect
from studyarchive.models import Course, CourseMaterial
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404



@login_required
def quizarchive_view(request):
    if request.method == "POST":
        # POST 요청으로 강의 추가
        year = request.POST['year']
        semester = request.POST['semester']
        course_name = request.POST['course_name']
        
        # 강의 추가
        Course.objects.create(user=request.user, year=year, semester=semester, name=course_name)
        
        # 강의 추가 후 리디렉션
        return redirect('quizarchive:quizarchive')
    
    # GET 요청 시 강의 목록을 보여줍니다.
    courses = Course.objects.filter(user=request.user)

    # 모든 강의 자료를 최신순으로 가져오기
    course_materials = CourseMaterial.objects.filter(course__user=request.user).order_by('-upload_date')

    return render(request, 'quiz_index.html', {'courses': courses})


