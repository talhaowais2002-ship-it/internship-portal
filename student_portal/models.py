from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. USER PROFILE MODEL
# ==========================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default='student')
    internship_start_date = models.DateField(null=True, blank=True)
    required_hours = models.DecimalField(max_digits=5, decimal_places=2, default=240.00)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# ==========================================
# 2. STUDENT RESUME MODEL
# ==========================================
class StudentResume(models.Model):
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume of {self.student.user.username}"


# ==========================================
# 3. ATTENDANCE RECORD MODEL WITH HOURLY TRACKING
# ==========================================
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
    
    # New tracking elements
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES, default='regular')

    def __str__(self):
        return f"{self.student.user.username} - {self.date} ({self.record_type})"
    
class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    coordinator_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    date_affiliated = models.DateField(auto_now_add=True)

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