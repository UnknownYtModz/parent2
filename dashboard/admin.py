from django.contrib import admin
from .models import Student, Assessment, WellbeingLog, ParentActivity

admin.site.register(Student)
admin.site.register(Assessment)
admin.site.register(WellbeingLog)
admin.site.register(ParentActivity)
