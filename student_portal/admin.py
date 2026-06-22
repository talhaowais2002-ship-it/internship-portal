from django.contrib import admin
from .models import AttendanceRecord, UserProfile, StudentResume, University, TrainingTrack

# Register your models here so they show up in the dashboard
admin.site.register(AttendanceRecord)
admin.site.register(UserProfile)
admin.site.register(StudentResume)
admin.site.register(University)
admin.site.register(TrainingTrack)