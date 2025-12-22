# ------------------------------
from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import StudentProfile,TeacherProfile,ParentProfile,StaffProfile
from django.contrib.auth import get_user_model
import uuid
from django.db.models import Max

User = get_user_model()
@receiver(pre_save, sender=StudentProfile)
def generate_enrollment_number(sender, instance, **kwargs):
       
    """
    Generate sequential enrollment numbers: ENR000001, ENR000002, etc.
    """
    if not instance.enrollment_no:
        # Get the highest current enrollment number
        max_enrollment = StudentProfile.objects.aggregate(
            max_num=Max('enrollment_no')
        )['max_num']
        
        if max_enrollment and max_enrollment.startswith('ENR'):
            try:
                # Extract number part and increment
                current_num = int(max_enrollment[3:])
                next_num = current_num + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        
        # Format as ENR000001, ENR000002, etc.
        instance.enrollment_no = f"ENR{next_num:06d}"            

# Signal to generate sequential staff ID
@receiver(pre_save, sender=TeacherProfile)
def generate_staff_id(sender, instance, **kwargs):
    """
    Generate sequential staff ID: STF1001, STF1002, etc.
    """
    if not instance.staff_id:
        # Get the highest current staff ID
        last_teacher = TeacherProfile.objects.aggregate(
            max_id=Max('staff_id')
        )['max_id']
        
        if last_teacher and last_teacher.startswith('STF'):
            try:
                # Extract number part and increment
                current_num = int(last_teacher[3:])  # Remove 'STF' prefix
                next_num = current_num + 1
            except ValueError:
                # If format is wrong, start from 1001
                next_num = 1001
        else:
            # Start from STF1001
            next_num = 1001
        
        # Format as STF1001, STF1002, etc.
        instance.staff_id = f"STF{next_num}"        

# ------------------------------
# StudentProfile → User
# ------------------------------
@receiver(post_save, sender=StudentProfile)
def create_user_for_student(sender, instance, created, **kwargs):
    if created:
        if not User.objects.filter(email=instance.email).exists():
            user = User.objects.create(
                username=instance.student_name,   # or use instance.email
                email=instance.email,
                role="student",
                phone_number=instance.phone_number,
                gender=instance.gender,
                dob=instance.dob,
                address=instance.address,
                profile_picture=instance.profile_picture,
                language_preference=instance.language_preference,
                is_active=True,
            )
            user.set_password("student@123")  # default password (optional)
            user.save()

# ------------------------------
# TeacherProfile → User
# ------------------------------
@receiver(post_save, sender=TeacherProfile)
def create_user_for_teacher(sender, instance, created, **kwargs):
    if created:
        if not User.objects.filter(email=instance.email).exists():
            user = User.objects.create(
                username=instance.teacher_name,   # or use instance.email
                email=instance.email,
                role="teacher",
                gender=instance.gender,
                dob=instance.dob,
                address=instance.address,
                profile_picture=instance.profile_picture,
                language_preference=instance.language_preference,
                is_active=True,
            )
            user.set_password("teacher@123")  # default password (optional)
            user.save()