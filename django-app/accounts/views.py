from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .forms import CustomUserChangeForm
from .models import CustomUser
from django.core.files.storage import FileSystemStorage
from studyarchive.models import CourseMaterial
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse


def login_register_view(request):
    # 로그인 폼과 회원가입 폼 초기화
    login_form = AuthenticationForm()
    register_form = CustomUserCreationForm()

    if request.method == 'POST':
        if 'login_submit' in request.POST:  # 로그인 처리
            login_form = AuthenticationForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                messages.success(request, '로그인 성공!')
                return redirect('home')
            else:
                messages.error(request, '로그인 실패. 다시 시도해주세요.')

        elif 'register_submit' in request.POST:  # 회원가입 처리
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                messages.success(request, '회원가입 성공!')
                return redirect('home')
            else:
                messages.error(request, '회원가입 실패. 입력 내용을 확인해주세요.')

    return render(request, 'accounts/login_register.html', {
        'login_form': login_form,
        'register_form': register_form,
    })

# 로그인 
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # 세션 시작
            return redirect('accounts:dashboard')  # 로그인 성공 시 홈 화면으로 리다이렉트
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')


# 로그아웃
def logout_view(request):
    logout(request)
    messages.info(request, '로그아웃 되었습니다.')
    return redirect('accounts:login_register')

# 회원가입
from django.db import transaction

def register_view(request):
    if request.method == 'POST':
        register_form = CustomUserCreationForm(request.POST, request.FILES)
        if register_form.is_valid():
            user = register_form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        register_form = CustomUserCreationForm()

    # Ensure 'register_form' is passed to the template in both GET and POST scenarios
    return render(request, 'accounts/login_register.html', {'register_form': register_form})


# 사용자 프로필을 보여주는 뷰
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def profile_update_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            # 이미지 파일을 업로드하고 저장하는 로직
            if 'profile_image' in request.FILES:
                profile_image = request.FILES['profile_image']
                
                # Image 저장
                fs = FileSystemStorage()
                filename = fs.save(profile_image.name, profile_image)
                uploaded_file_url = fs.url(filename)

                # 프로필 이미지 경로 업데이트
                request.user.profile_image = uploaded_file_url
                request.user.save()  # 프로필 이미지 변경 사항 저장

            # 사용자 프로필 정보 저장
            form.save()

            messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            return redirect('accounts:profile_update')
        else:
            messages.error(request, '프로필 업데이트에 실패했습니다. 다시 시도하세요.')
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'accounts/profile_update.html', {'form': form})

def search(request):
    query = request.GET.get('q', '').strip()  # 검색어 입력
    page = request.GET.get('page', 1)  # 페이지 번호
    results = []

    if query:  # 검색어가 비어 있지 않을 경우
        results = CourseMaterial.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)  # 제목 또는 설명에서 검색
        )

    # 페이지네이션 처리
    paginator = Paginator(results, 10)  # 한 페이지에 10개의 결과 표시
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = []

    # JSON 응답 생성
    data = {
        'results': [
            {
                'id': item.id,
                'title': item.title,
                'description': item.description,
            }
            for item in results
        ],
        'has_next': results.has_next() if results else False,
        'has_previous': results.has_previous() if results else False,
        'page': results.number if results else 1,
    }
    return JsonResponse(data)

def dashboard_view(request):
    # 로그인 후 보여줄 대시보드 페이지
    return render(request, 'accounts/dashboard.html')




    ### login required ...
    ### login 하지 않은 사용자가 접근 시 현재 에러 페이지 발생하는데, 이거를 로그인 유도로 수정하기!!