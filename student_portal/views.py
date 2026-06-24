from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from .models import UserProfile, StudentResume, AttendanceRecord, University, TrainingTrack
from django.utils import timezone
from .models import UserProfile, AttendanceRecord
from datetime import date, datetime, timedelta
from decimal import Decimal
import calendar


# Helper context to toggle admin mode for structural testing
def get_admin_context(title):
    return {
        'user_role': 'admin',  # Enforces Admin view in sidebar
        'panel_title': title
    }

def home_view(request):
    # If a user is signed in, check their role and route them automatically
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_manage')  # Sends coordinators to the verification queue
        else:
            return redirect('attendance_log') # Sends student interns to their log tracker
            
    # If nobody is logged in, show the public internship tracks landing page
    return render(request, 'home.html')

def it_roles_view(request):
    return render(request, 'it_roles.html', get_admin_context('IT Role Structures'))

def apply_view(request):
    return render(request, 'apply.html', get_admin_context('Application Submission Window'))

def resume_builder_view(request):
    # For testing, grab your master superuser account and ensure it has a profile
    test_user = User.objects.first() 
    if not test_user:
        return render(request, 'resume_builder.html', {'user_role': 'student', 'error': 'Please create a superuser first!'})
    
    # Get or create the UserProfile for this test run
    profile, created = UserProfile.objects.get_or_create(user=test_user, defaults={'role': 'student'})
    
    # Check if a resume already exists for this profile
    resume = StudentResume.objects.filter(student=profile).first()

    if request.method == 'POST':
        specialization = request.POST.get('specialization')
        skills = request.POST.get('skills')
        objective = request.POST.get('objective')
        
        if request.POST.get('action') == 'delete':
            # Handle the "Delete Resume" feature requested by your instructor
            if resume:
                resume.delete()
            return redirect('resume_builder')

        # Create or update the resume entry
        if resume:
            resume.specialization = specialization
            resume.skills = skills
            resume.objective = objective
            resume.save()
        else:
            StudentResume.objects.create(
                student=profile,
                specialization=specialization,
                skills=skills,
                objective=objective
            )
        return redirect('resume_builder')

    context = {
        'user_role': 'student', # Keeps the student workspace menu active
        'panel_title': 'Resume Engine',
        'resume': resume
    }
    return render(request, 'resume_builder.html', context)

def report_view(request):
    context = get_admin_context('Weekly Progress Verification')
    context['student'] = {'name': 'Sayed Salman Alawi'}
    return render(request, 'progress_report.html', context)

# NEW CORE ADMIN INTERFACES
@login_required
def admin_trainings_view(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
        
    trainings = TrainingTrack.objects.all().order_by('department')
    
    context = get_admin_context('Trainings & Track Modules')
    context['trainings'] = trainings
    
    # Notice we are sending this to a NEW html file now
    return render(request, 'admin_trainings.html', context)

@login_required
def admin_universities_view(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
        
    # --- FORM PROCESSING LOGIC ---
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        coordinator_name = request.POST.get('coordinator_name')
        contact_email = request.POST.get('contact_email')
        
        # Prevent empty submissions
        if name and coordinator_name and contact_email:
            University.objects.create(
                name=name,
                location=location,
                coordinator_name=coordinator_name,
                contact_email=contact_email
            )
            messages.success(request, f"Success: {name} has been formally affiliated!")
            # Refreshes the page to clear the form and show the new data
            return redirect(request.path) 

    # --- DATA PREPARATION ---
    universities = University.objects.all().order_by('-date_affiliated')
    
    context = get_admin_context('Affiliated University Records')
    context['universities'] = universities
    
    return render(request, 'admin_universities.html', context)

def admin_attendance_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Office Attendance & Location Rules'))

def admin_reports_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Weekly & Monthly Performance Invoices'))

def admin_reviews_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Goals Achievement & Performance Reviews'))

def admin_credentials_view(request):
    return render(request, 'admin_manage.html', get_admin_context('Corporate Awards & Graduation Certificates'))
# To test different actors, switch role string below to 'student', 'supervisor', or 'mentor'
def get_system_context(title):
    return {
        'user_role': 'student',  
        'panel_title': title
    }

@login_required
def attendance_log_view(request):
    now = timezone.now()
    today = now.date()
    profile = request.user.userprofile

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- CLOCK IN LOGIC ---
        if action == 'clock_in':
            AttendanceRecord.objects.create(
                student=profile,
                date=today,
                check_in=now.time(),
                is_verified=False,
                record_type='regular'
            )
            messages.success(request, "Successfully clocked in!")
            return redirect('attendance_log')

        # --- CLOCK OUT LOGIC ---
        elif action == 'clock_out':
            open_shift = AttendanceRecord.objects.filter(
                student=profile, check_out__isnull=True
            ).first()

            if open_shift:
                open_shift.check_out = now.time()
                duration = datetime.combine(today, open_shift.check_out) - datetime.combine(today, open_shift.check_in)
                hours = duration.total_seconds() / 3600.0
                open_shift.hours_worked = round(Decimal(hours), 2)
                open_shift.save()
            return redirect('attendance_log')

    # --- DATA PREPARATION ---
    my_shifts = AttendanceRecord.objects.filter(student=profile).order_by('-date')
    is_clocked_in = AttendanceRecord.objects.filter(student=profile, check_out__isnull=True).exists()

    # Cumulative Hours Math
    total_hours_earned = AttendanceRecord.objects.filter(
        student=profile, is_verified=True
    ).aggregate(Sum('hours_worked'))['hours_worked__sum'] or Decimal('0.00')
    
    total_hours_earned = round(float(total_hours_earned), 2)
    required_hours = float(profile.required_hours) if profile.required_hours else 240.0
    
    if required_hours > 0:
        progress_percentage = min(int((total_hours_earned / required_hours) * 100), 100)
    else:
        progress_percentage = 0

    # Calendar & Monthly Records Prep
    year, month = today.year, today.month
    month_name = calendar.month_name[month]

    monthly_records = AttendanceRecord.objects.filter(
        student=profile, date__year=year, date__month=month
    )

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)
    
    # Filter shifts specifically for the current viewing month for the calendar
    month_shifts = {
        shift.date.day: shift for shift in monthly_records 
    }

    calendar_grid = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': '', 'status': 'empty', 'record': None})
            else:
                day_info = {'day': day, 'status': 'none', 'record': None}
                if day in month_shifts:
                    shift = month_shifts[day]
                    day_info['record'] = shift
                    
                    if shift.check_out is None:
                        day_info['status'] = 'active'      # Blue
                    elif shift.is_verified:
                        day_info['status'] = 'verified'    # Green
                    else:
                        day_info['status'] = 'pending'     # Yellow
                week_data.append(day_info)
        calendar_grid.append(week_data)

    # --- FINAL RENDER ---
    context = {
        'my_shifts': my_shifts,
        'profile': profile,
        'total_hours_earned': total_hours_earned,
        'required_hours': required_hours,
        'progress_percentage': progress_percentage,
        'calendar_grid': calendar_grid,
        'month_name': month_name,
        'year': year,
        'records': monthly_records.order_by('-date'),
        'is_clocked_in': is_clocked_in,  
    }
    return render(request, 'attendance_log.html', context)

def report_review_view(request):
    context = get_system_context('Two-Tier Evaluation Engine')
    return render(request, 'report_review.html', context)
@login_required
def admin_manage_view(request):
    #Only allows users with staff status
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access this page.")
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        action = request.POST.get('action')
        if action == 'approve' and record_id:
            try:
                record = AttendanceRecord.objects.get(id=record_id)
                record.is_verified = True
                record.save()
                messages.success(request, f'Shift for {record.student.user.username} on {record.date} has been verified!')
            except AttendanceRecord.DoesNotExist:
                messages.error(request, 'Attendance record not found!')
            return redirect('admin_manage')
    pending_shifts = AttendanceRecord.objects.filter(is_verified=False, check_out__isnull=False).order_by('date')
    training_tracks = TrainingTrack.objects.filter(is_active=True) 

    context = {
        "pending_shifts": pending_shifts,
        "tracks": training_tracks, 
    }
    return render(request, 'admin_manage.html', context)