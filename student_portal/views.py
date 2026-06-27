from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import calendar

# Consolidated all models into one clean import
from .models import UserProfile, StudentResume, AttendanceRecord, University, TrainingTrack

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_admin_context(title):
    return {'user_role': 'admin', 'panel_title': title}

def get_system_context(title):
    return {'user_role': 'student', 'panel_title': title}

# ==========================================
# PUBLIC & AUTH VIEWS
# ==========================================
def home_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_manage')
        else:
            return redirect('attendance_log')
    return render(request, 'home.html')

def it_roles_view(request):
    return render(request, 'it_roles.html', get_admin_context('IT Role Structures'))

def apply_view(request):
    return render(request, 'apply.html', get_admin_context('Application Submission Window'))

# ==========================================
# STUDENT VIEWS
# ==========================================
def resume_builder_view(request):
    test_user = User.objects.first() 
    if not test_user:
        return render(request, 'resume_builder.html', {'user_role': 'student', 'error': 'Please create a superuser first!'})
    
    profile, created = UserProfile.objects.get_or_create(user=test_user, defaults={'role': 'student'})
    resume = StudentResume.objects.filter(student=profile).first()

    if request.method == 'POST':
        specialization = request.POST.get('specialization')
        skills = request.POST.get('skills')
        objective = request.POST.get('objective')
        
        if request.POST.get('action') == 'delete':
            if resume:
                resume.delete()
            return redirect('resume_builder')

        if resume:
            resume.specialization = specialization
            resume.skills = skills
            resume.objective = objective
            resume.save()
        else:
            StudentResume.objects.create(
                student=profile, specialization=specialization, 
                skills=skills, objective=objective
            )
        return redirect('resume_builder')

    context = {'user_role': 'student', 'panel_title': 'Resume Engine', 'resume': resume}
    return render(request, 'resume_builder.html', context)

@login_required
def attendance_log_view(request):
    now = timezone.now()
    today = now.date()
    profile = request.user.userprofile

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clock_in':
            AttendanceRecord.objects.create(
                student=profile, date=today, check_in=now.time(),
                is_verified=False, record_type='regular'
            )
            messages.success(request, "Successfully clocked in!")
            return redirect('attendance_log')

        elif action == 'clock_out':
            open_shift = AttendanceRecord.objects.filter(student=profile, check_out__isnull=True).first()
            if open_shift:
                open_shift.check_out = now.time()
                duration = datetime.combine(today, open_shift.check_out) - datetime.combine(today, open_shift.check_in)
                hours = duration.total_seconds() / 3600.0
                open_shift.hours_worked = round(Decimal(hours), 2)
                open_shift.save()
            return redirect('attendance_log')

    my_shifts = AttendanceRecord.objects.filter(student=profile).order_by('-date')
    is_clocked_in = AttendanceRecord.objects.filter(student=profile, check_out__isnull=True).exists()

    total_hours_earned = AttendanceRecord.objects.filter(student=profile, is_verified=True).aggregate(Sum('hours_worked'))['hours_worked__sum'] or Decimal('0.00')
    total_hours_earned = round(float(total_hours_earned), 2)
    required_hours = float(profile.required_hours) if profile.required_hours else 240.0
    progress_percentage = min(int((total_hours_earned / required_hours) * 100), 100) if required_hours > 0 else 0

    year, month = today.year, today.month
    monthly_records = AttendanceRecord.objects.filter(student=profile, date__year=year, date__month=month)

    cal = calendar.Calendar(firstweekday=6)
    month_shifts = {shift.date.day: shift for shift in monthly_records}
    
    calendar_grid = []
    for week in cal.monthdayscalendar(year, month):
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': '', 'status': 'empty', 'record': None})
            else:
                day_info = {'day': day, 'status': 'none', 'record': None}
                if day in month_shifts:
                    shift = month_shifts[day]
                    day_info['record'] = shift
                    if shift.check_out is None: day_info['status'] = 'active'
                    elif shift.is_verified: day_info['status'] = 'verified'
                    else: day_info['status'] = 'pending'
                week_data.append(day_info)
        calendar_grid.append(week_data)

    context = {
        'my_shifts': my_shifts, 'profile': profile, 'total_hours_earned': total_hours_earned,
        'required_hours': required_hours, 'progress_percentage': progress_percentage,
        'calendar_grid': calendar_grid, 'month_name': calendar.month_name[month],
        'year': year, 'records': monthly_records.order_by('-date'), 'is_clocked_in': is_clocked_in,  
    }
    return render(request, 'attendance_log.html', context)

# ==========================================
# SUPERVISOR VIEWS
# ==========================================
@login_required
def supervisor_dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role != 'supervisor':
        return redirect('home')

    supervisor_company = profile.current_company
    interns = UserProfile.objects.filter(role='student', current_company=supervisor_company).select_related('user', 'university', 'assigned_track') if supervisor_company else []

    return render(request, 'supervisor_dashboard.html', {'company': supervisor_company, 'interns': interns})

@login_required
def supervisor_student_attendance(request, student_id):
    supervisor_profile = get_object_or_404(UserProfile, user=request.user)
    if supervisor_profile.role != 'supervisor':
        return redirect('home')

    student_profile = get_object_or_404(UserProfile, id=student_id, role='student')
    logs = AttendanceRecord.objects.filter(student=student_profile).order_by('-date')

    return render(request, 'supervisor_attendance.html', {'student': student_profile, 'logs': logs})

# ==========================================
# ADMIN & COORDINATOR VIEWS
# ==========================================
@login_required
def admin_manage_view(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
        
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        if request.POST.get('action') == 'approve' and record_id:
            try:
                record = AttendanceRecord.objects.get(id=record_id)
                record.is_verified = True
                record.save()
                messages.success(request, f'Shift for {record.student.user.username} on {record.date} has been verified!')
            except AttendanceRecord.DoesNotExist:
                messages.error(request, 'Attendance record not found!')
            return redirect('admin_manage')
            
    pending_shifts = AttendanceRecord.objects.filter(is_verified=False, check_out__isnull=False).order_by('date')
    return render(request, 'admin_manage.html', {"pending_shifts": pending_shifts, "tracks": TrainingTrack.objects.filter(is_active=True)})

@login_required
def admin_trainings_view(request):
    if not request.user.is_staff: raise PermissionDenied("You do not have permission to access this page.")
    context = get_admin_context('Trainings & Track Modules')
    context['trainings'] = TrainingTrack.objects.all().order_by('department')
    return render(request, 'admin_trainings.html', context)

@login_required
def admin_universities_view(request):
    if not request.user.is_staff: raise PermissionDenied("You do not have permission to access this page.")
    if request.method == 'POST':
        name, location = request.POST.get('name'), request.POST.get('location')
        coordinator_name, contact_email = request.POST.get('coordinator_name'), request.POST.get('contact_email')
        if name and coordinator_name and contact_email:
            University.objects.create(name=name, location=location, coordinator_name=coordinator_name, contact_email=contact_email)
            messages.success(request, f"Success: {name} has been formally affiliated!")
            return redirect(request.path) 

    context = get_admin_context('Affiliated University Records')
    context['universities'] = University.objects.all().order_by('-date_affiliated')
    return render(request, 'admin_universities.html', context)

@login_required
def admin_resume_list(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != 'university_admin' and not request.user.is_staff:
        return redirect('home')
    resumes = StudentResume.objects.all()
    return render(request, 'admin_resumes.html', {'resumes': resumes})

# ==========================================
# PLACEHOLDER VIEWS (To be built next)
# ==========================================
def report_view(request):
    context = get_admin_context('Weekly Progress Verification')
    context['student'] = {'name': 'Sayed Salman Alawi'}
    return render(request, 'progress_report.html', context)

def report_review_view(request):
    return render(request, 'report_review.html', get_system_context('Two-Tier Evaluation Engine'))

def admin_reports_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Weekly & Monthly Performance Invoices'))

def admin_reviews_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Goals Achievement & Performance Reviews'))

def admin_credentials_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Corporate Awards & Graduation Certificates'))