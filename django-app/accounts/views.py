from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .forms import CustomUserChangeForm
from django.core.files.storage import FileSystemStorage
from studyarchive.models import CourseMaterial
from quizarchive.models import Quiz
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from .models import Item, UserItem
from quizarchive.models import Quiz, SubmissionDetail, QuizSubmission
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now



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
                return redirect('/')
            else:
                print('실패실패실패')
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
            return redirect('/')
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


def search(request):
    query = request.GET.get('q', '').strip()
    search_filter = request.GET.get('filter', '').strip()

    if not query:
        return JsonResponse({"error": "검색어가 입력되지 않았습니다."}, status=400)

    results = []

    # 강의자료 검색
    if search_filter == "material":
        materials = CourseMaterial.objects.filter(title__icontains=query)
        results = [
            {"title": material.title, "description": material.description}
            for material in materials
        ]
    
    # 퀴즈 검색
    elif search_filter == "quiz":
        quizzes = Quiz.objects.filter(title__icontains=query)
        results = [
            {"title": quiz.title, "description": quiz.question}
            for quiz in quizzes
        ]
    else:
        return JsonResponse({"error": "잘못된 필터링 옵션입니다."}, status=400)

    return JsonResponse({"results": results})


@login_required
def dashboard_view(request):
    """대시보드 뷰"""
    user = request.user
    items = Item.objects.filter(is_active=True)  # 구매 가능한 아이템
    user_items = UserItem.objects.filter(user=user)  # 사용자가 소유한 아이템
    equipped_items = user_items.filter(is_equipped=True)  # 착용 중인 아이템

    context = {
        'items': items,
        'user_items': user_items,
        'equipped_items': equipped_items,
        'experience_points': user.experience_points,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def purchase_item(request, item_id):
    """아이템 구매 뷰"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        if request.user.experience_points >= item.price:
            # 경험치 차감
            request.user.subtract_experience(item.price)

            # UserItem 생성
            UserItem.objects.create(user=request.user, item=item)
            messages.success(request, f"'{item.name}' 아이템을 구매했습니다!")
        else:
            messages.error(request, "경험치가 부족합니다. 더 많은 문제를 풀어 경험치를 얻으세요!")
        return redirect('accounts:dashboard')

@login_required
def equip_item(request, user_item_id):
    """아이템 착용 뷰"""
    user_item = get_object_or_404(UserItem, id=user_item_id, user=request.user)

    if request.method == "POST":
        # 같은 카테고리의 기존 착용 아이템 해제
        UserItem.objects.filter(user=request.user, item__category=user_item.item.category).update(is_equipped=False)

        # 선택한 아이템 착용
        user_item.is_equipped = True
        user_item.save()
        messages.success(request, f"'{user_item.item.name}' 아이템을 착용했습니다!")
        return redirect('accounts:dashboard')

@login_required
def unequip_item(request, user_item_id):
    """아이템 착용 해제 뷰"""
    user_item = get_object_or_404(UserItem, id=user_item_id, user=request.user)

    if request.method == "POST":
        user_item.is_equipped = False
        user_item.save()
        messages.success(request, f"'{user_item.item.name}' 아이템을 해제했습니다!")
        return redirect('accounts:dashboard')

@login_required
@csrf_exempt
def solve_problem(request):
    """
    오늘의 문제 정답 확인 및 경험치 증가
    """
    if request.method == "POST":
        user = request.user
        data = json.loads(request.body)
        submitted_answer = data.get("answer", None)
        quiz_id = data.get("quiz_id", None)

        if not quiz_id or submitted_answer is None:
            return JsonResponse({"success": False, "message": "문제와 정답을 입력해주세요."})

        # # 오늘 이미 문제를 풀었는지 확인
        # if QuizSubmission.objects.filter(user=user, submitted_at__date=now().date()).exists():
        #     return JsonResponse({
        #         "success": False,
        #         "message": "오늘의 문제를 이미 풀었습니다! 내일 만나요!"
        #     })

        try:
            quiz = Quiz.objects.get(id=quiz_id)

            # 사용자 입력의 첫 번째 문자를 추출하여 정답과 비교
            # user_selected_option = submitted_answer.split(')')[0].strip()  # "A) ~~~" -> "A"
            user_selected_option = submitted_answer
            is_correct = quiz.answer.strip() == user_selected_option

            # 제출 기록 업데이트
            submission, created = QuizSubmission.objects.get_or_create(
                user=user,
                course_material=quiz.course_material,
                defaults={'total_questions': 0, 'correct_answers': 0}
            )

            submission_detail, created = SubmissionDetail.objects.get_or_create(
                submission=submission,
                quiz=quiz,
                defaults={'user_answer': submitted_answer, 'is_correct': is_correct}
            )

            if not created:  # 이미 제출된 경우 업데이트
                submission_detail.user_answer = submitted_answer
                submission_detail.is_correct = is_correct
                submission_detail.save()

            # 제출 요약 업데이트
            if created:
                submission.total_questions += 1
            if is_correct:
                submission.correct_answers += 1
                submission.save()

                # 경험치 증가
                experience_gain = 10
                user.add_experience(experience_gain)

                return JsonResponse({
                    "success": True,
                    "message": "정답입니다! 경험치가 {} 증가했습니다.".format(experience_gain),
                    "current_experience": user.experience_points,
                    "quiz_completed": True
                })

            return JsonResponse({
                "success": False,
                "message": "틀렸습니다. 다시 시도해주세요.",
                "quiz_completed": False
            })

        except Quiz.DoesNotExist:
            return JsonResponse({"success": False, "message": "문제를 찾을 수 없습니다."}, status=404)

    return JsonResponse({"error": "잘못된 요청입니다."}, status=400)

@login_required
def get_today_problem(request):
    """
    사용자가 풀지 않은 문제 또는 틀린 문제를 가져오는 뷰
    """
    user = request.user
    
    # # 오늘 이미 문제를 풀었는지 확인
    # today_submission = QuizSubmission.objects.filter(user=user, submitted_at__date=now().date()).exists()
    # if today_submission:
    #     return JsonResponse({
    #         'message': '오늘 문제를 이미 푸셨습니다! 내일 만나요!',
    #         'quiz_available': False
    #     })

    # 사용자가 푼 문제 ID 가져오기
    solved_quiz_ids = SubmissionDetail.objects.filter(
        submission__user=user
    ).values_list('quiz_id', flat=True)

    # 틀린 문제 가져오기
    wrong_quiz_ids = SubmissionDetail.objects.filter(
        submission__user=user, is_correct=False
    ).values_list('quiz_id', flat=True)

    # 풀지 않은 문제 또는 틀린 문제 중 랜덤으로 하나 가져오기
    quiz = Quiz.objects.filter(
        Q(id__in=wrong_quiz_ids) | ~Q(id__in=solved_quiz_ids),
        question_type='MCQ'  # 객관식 문제만 가져오기
    ).order_by('?').first()
    
    if not quiz:
        return JsonResponse({'error': '풀 수 있는 문제가 없습니다.'}, status=404)

    options = quiz.options if isinstance(quiz.options, list) else json.loads(quiz.options)
    
    return JsonResponse({
        'question': quiz.question,
        'options': options,
        'quiz_id': quiz.id,
        'quiz_available': True
    }, encoder=DjangoJSONEncoder)