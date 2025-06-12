from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .models import GameResult
from django.http import JsonResponse
from django.db.models import Subquery, OuterRef
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy

User = get_user_model()

def home(request):
    return render(request, 'game/home.html')

def auth_view(request):
    context = {
        'register_errors': {},
        'login_errors': {},
        'active_tab': 'login',
    }

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        if 'login' in request.POST:
            context['active_tab'] = 'login'
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)

            if user:
                login(request, user)
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect_url': '/dashboard/'})
                return redirect('dashboard')
            else:
                error_msg = 'Neplatný e-mail nebo heslo.'
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': {'general': error_msg}})
                context['login_errors']['general'] = error_msg

        elif 'register' in request.POST:
            context['active_tab'] = 'register'
            email = request.POST.get('email')
            nickname = request.POST.get('nickname')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            errors = {}

            if User.objects.filter(email=email).exists():
                errors['email'] = 'Tento e-mail už existuje.'

            if User.objects.filter(nickname=nickname).exists():
                errors['nickname'] = 'Tato přezdívka už je zabraná.'

            if password1 != password2:
                errors['password2'] = 'Hesla se neshodují.'

            if len(password1) < 8 or not any(c.isdigit() for c in password1) or not any(c.isalpha() for c in password1):
                errors['password1'] = 'Heslo musí mít alespoň 8 znaků a obsahovat písmeno i číslo.'

            if errors:
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors})
                context['register_errors'] = errors
            else:
                user = User.objects.create_user(email=email, password=password1, nickname=nickname)
                login(request, user)
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect_url': '/dashboard/'})
                return redirect('dashboard')

    return render(request, 'game/login.html', context)

@csrf_exempt
def ajax_register_validate(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        nickname = request.POST.get('nickname', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = {}

        if User.objects.filter(email=email).exists():
            errors['email'] = 'Tento e-mail už existuje.'

        if User.objects.filter(nickname=nickname).exists():
            errors['nickname'] = 'Tato přezdívka už je zabraná.'

        if password1 != password2:
            errors['password2'] = 'Hesla se neshodují.'

        if len(password1) < 8 or not any(c.isdigit() for c in password1) or not any(c.isalpha() for c in password1):
            errors['password1'] = 'Heslo musí mít alespoň 8 znaků a obsahovat písmeno i číslo.'

        return JsonResponse({'errors': errors})
    return JsonResponse({'error': 'Invalid method'}, status=405)


@csrf_exempt
def ajax_login_validate(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'errors': {
                'email': '',
                'password': 'Neplatný e-mail nebo heslo.'
            }})
    return JsonResponse({'error': 'Invalid method'}, status=405)

def logout_view(request):
    logout(request)
    return redirect('home')

def dashboard_view(request):
    # Subquery: nejlepší skóre pro daného uživatele
    best_score_subquery = (
        GameResult.objects
        .filter(user=OuterRef('user'))
        .order_by('-score')
        .values('score')[:1]
    )

    # Výběr záznamu s nejvyšším skóre na uživatele
    top_scores = (
        GameResult.objects
        .filter(score=Subquery(best_score_subquery))
        .order_by('user', '-score')   # ✅ MUSÍ být `user` jako první
        .distinct('user')             # DISTINCT ON (user)
    )

    # Až teď můžeš setřídit v Pythonu podle skóre (pokud chceš vizuálně nahoře ty nejlepší)
    sorted_scores = sorted(top_scores, key=lambda x: x.score, reverse=True)

    return render(request, 'game/dashboard.html', {'results': sorted_scores})

def play_view(request):
    return render(request, 'game/play.html')  # nečti svg_snippet jako soubor, použij {% include %}

def save_score(request):
    if request.method == 'POST' and request.user.is_authenticated:
        score = int(request.POST.get('score', 0))
        GameResult.objects.create(user=request.user, score=score)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def check_email(request):
    email = request.GET.get('email')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def check_nickname(request):
    nickname = request.GET.get('nickname')
    exists = User.objects.filter(nickname=nickname).exists()
    return JsonResponse({'exists': exists})

class SimplePasswordResetView(PasswordResetView):
    template_name = 'tasks/password_reset.html'
    email_template_name = 'tasks/password_reset_email.html'
    subject_template_name = 'tasks/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

class SimplePasswordResetDoneView(PasswordResetDoneView):
    template_name = 'tasks/password_reset_done.html'

class SimplePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'tasks/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class SimplePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'tasks/password_reset_complete.html'

def password_reset_done(request):
    return render(request, 'game/password_reset_done.html')

def privacy_policy(request):
    return render(request, 'game/privacy_policy.html')