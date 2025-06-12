from django.urls import path
from . import views
from .views import logout_view
from .views import save_score
from .views import check_email, check_nickname
from django.contrib.auth.views import PasswordResetView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.auth_view, name='login'),  # jednotná view
    path('logout/', logout_view, name='logout'),
    path('play/', views.play_view, name='play'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('save-score/', save_score, name='save_score'),
    path('ajax/check-email/', check_email, name='check_email'),
    path('ajax/check-nickname/', check_nickname, name='check_nickname'),
    path('ajax/register-validate/', views.ajax_register_validate, name='ajax_register_validate'),
    path('ajax/login-validate/', views.ajax_login_validate, name='ajax_login_validate'),
    path('password_reset/', PasswordResetView.as_view(
        template_name='game/password_reset.html',
        email_template_name='game/password_reset_email.html',
        subject_template_name='game/password_reset_subject.txt'
    ), name='password_reset'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]
