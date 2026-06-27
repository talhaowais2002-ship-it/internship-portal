from django.contrib import admin
from .models import AttendanceRecord, UserProfile, TrainingTrack, University, StudentResume, Company, CompanySupervisor

# Register your models here so they show up in the dashboard
admin.site.register(AttendanceRecord)
admin.site.register(UserProfile)
admin.site.register(StudentResume)
admin.site.register(University)
admin.site.register(TrainingTrack)
admin.site.register(Company)
admin.site.register(CompanySupervisor)