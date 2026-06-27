from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ==========================================
    # PUBLIC & AUTH ROUTES
    # ==========================================
    path('', views.home_view, name='home'),
    path('it-roles/', views.it_roles_view, name='it_roles'),
    path('apply/', views.apply_view, name='apply'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ==========================================
    # STUDENT PORTAL ROUTES
    # ==========================================
    path('seeker/resume/', views.resume_builder_view, name='resume_builder'),
    path('attendance/log/', views.attendance_log_view, name='attendance_log'),
    path('report/', views.report_view, name='report'),

    # ==========================================
    # SUPERVISOR PORTAL ROUTES
    # ==========================================
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/attendance/<int:student_id>/', views.supervisor_student_attendance, name='supervisor_student_attendance'),
    path('supervisor/evaluate-reports/', views.report_review_view, name='report_review'),

    # ==========================================
    # ADMIN / COORDINATOR ROUTES
    # ==========================================
    path('admin-manage/', views.admin_manage_view, name='admin_manage'),
    path('portal/universities/', views.admin_universities_view, name='admin_universities'),
    path('admin/resumes/', views.admin_resume_list, name='admin_resumes'),
    
    # (Placeholder) Mentor Route sharing the supervisor evaluation view for now
    path('mentor/verify-reports/', views.report_review_view, name='mentor_review'),
]