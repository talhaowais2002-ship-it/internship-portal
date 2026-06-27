from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. CORE SYSTEM ENTITIES
# ==========================================
class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    coordinator_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    date_affiliated = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class TrainingTrack(models.Model):
    DEPARTMENT_CHOICES = [
        ('IT', 'Information Technology'),
        ('BUS', 'Business & Finance'),
        ('ENG', 'Engineering'),
    ]
    
    title = models.CharField(max_length=200)
    department = models.CharField(max_length=5, choices=DEPARTMENT_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_department_display()})"

class Company(models.Model):
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

# ==========================================
# 2. USER ACTORS
# ==========================================
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('supervisor', 'Company Supervisor'),
        ('university_mentor', 'University Mentor'),
        ('university_admin', 'University Coordinator'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    internship_start_date = models.DateField(null=True, blank=True)
    required_hours = models.DecimalField(max_digits=5, decimal_places=2, default=240.00)
    
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    assigned_track = models.ForeignKey(TrainingTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    current_company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='interns')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class CompanySupervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='supervisors')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Company Supervisors"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.company.name})"

# ==========================================
# 3. STUDENT ACTIVITY & TRACKING
# ==========================================
class StudentResume(models.Model):
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume of {self.student.user.username}"

class AttendanceRecord(models.Model):
    RECORD_TYPES = [
        ('regular', 'Regular Shift'),
        ('emergency_break', 'Emergency Break'),
    ]
    
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    device_api_status = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES, default='regular')

    def __str__(self):
        return f"{self.student.user.username} - {self.date} ({self.record_type})"

class WeeklyReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Supervisor Approval'),
        ('approved', 'Approved - Pending Mentor Grade'),
        ('graded', 'Graded & Completed'),
    )
    
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='weekly_reports')
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    
    tasks_completed = models.TextField(help_text="What did you accomplish this week?")
    challenges_faced = models.TextField(blank=True, help_text="Any technical issues or blockers?")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    supervisor_comments = models.TextField(blank=True, null=True)
    mentor_grade = models.CharField(max_length=5, blank=True, null=True, help_text="e.g., A, B, Pass")
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Week of {self.week_start_date} - {self.student.user.username}"