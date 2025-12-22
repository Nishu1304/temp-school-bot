from django.contrib import admin
from Account.models import User,StudentProfile,TeacherProfile,ParentProfile,StaffProfile

# Register your models here.

# admin.site.register(User)

class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'email', 'password', 'role','is_active',)
admin.site.register(User,UserAdmin)

class StudentAdmin(admin.ModelAdmin):
         list_display = ('id','student_name','enrollment_no',)
admin.site.register(StudentProfile,StudentAdmin)


# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ('id','user','phone_number','gender',)
# admin.site.register(Profile,ProfileAdmin)

admin.site.register(TeacherProfile)
admin.site.register(ParentProfile)
admin.site.register(StaffProfile)





