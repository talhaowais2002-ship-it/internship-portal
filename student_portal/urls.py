from django.urls import path
from django.contrib.auth import views as auth_views
from student_portal import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('it-roles/', views.it_roles_view, name='it_roles'),
    path('apply/', views.apply_view, name='apply'),
    path('seeker/resume/', views.resume_builder_view, name='resume_builder'),
    path('report/', views.report_view, name='report'),
    path('attendance/log/', views.attendance_log_view, name='attendance_log'),
    path('admin-manage/', views.admin_manage_view, name='admin_manage'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    # SYSTEM WORKFLOW INTERFACES
    path('attendance/log/', views.attendance_log_view, name='attendance_log'),
    path('supervisor/evaluate-reports/', views.report_review_view, name='report_review'),
    path('mentor/verify-reports/', views.report_review_view, name='mentor_review'),
    path('portal/universities/', views.admin_universities_view, name='admin_universities'),
    ]