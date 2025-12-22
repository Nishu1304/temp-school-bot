from django.db import models
from django.conf import settings
from django.utils import timezone
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User
from rest_framework.validators import ValidationError
from django.core.validators import MinValueValidator,MaxValueValidator
import os
from django.contrib.auth import get_user_model

User = get_user_model()
    
class Subject(models.Model):
    subject = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)  # e.g., MATH101
    description = models.TextField(blank=True, null=True)  # brief info about the subject
    # grade_level = models.CharField(max_length=50, blank=True, null=True)  # e.g., Class 5, Class 6
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subject']

    def __str__(self):
        return f"{self.subject} ({self.code})" if self.code else self.subject
    
class ClassRoom(models.Model):
    BOARD_CHOICES = [
        ('blackboard', 'Blackboard'),
        ('whiteboard', 'Whiteboard'),
        ('projector', 'Projector'),
        ('smart_board', 'Smart Board'),
        ('digital_display', 'Digital Display'),
    ]
    class_room = models.CharField(max_length=50) # LTU1,LTU2
    # section_name = models.CharField(max_length=10, blank=True, null=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    facilities  = MultiSelectField(
        max_length=225,
        choices=BOARD_CHOICES,
        default='blackboard',
        help_text="Type of board or teaching equipment available"
    )
    def __str__(self):
        return f"{self.class_room}" 
    
class Class(models.Model):
    """Represents an academic class such as 'Class X - A'."""
    class_name = models.CharField(max_length=50)               # e.g., Class X
    section = models.CharField(max_length=10, blank=True, null=True)  # e.g., A, B
    subjects = models.JSONField(default=list)    # classrooms = models.ManyToManyField(ClassRoom, related_name='classes')
    student_count = models.PositiveIntegerField(default=0)
    max_seats = models.PositiveIntegerField(default=40)
    room_no = models.CharField(null=True, blank=True,max_length=4)

    def __str__(self):
        return f"{self.class_name} {self.section or ''}".strip()
    

# Book Model
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} ({self.author})"
    
class BookIssue(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='issues')
    issued_to = models.ForeignKey('Account.StudentProfile', on_delete=models.CASCADE)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    is_returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.book.title} -> {self.issued_to.student_name}"
    def clean(self):
        # issue_date can't be in the future
        if self.issue_date > timezone.now().date():
            raise ValidationError("Issue date cannot be in the future.")

        # due_date must be after issue_date
        if self.due_date < self.issue_date:
            raise ValidationError("Due date must be after issue date.")

        # if returned, return_date must exist and be valid
        if self.is_returned:
            if not self.return_date:
                raise ValidationError("Return date required when book is returned.")
            if self.return_date < self.issue_date:
                raise ValidationError("Return date cannot be before issue date.")
    def save(self, *args, **kwargs):
        # Auto update available copies
        if not self.pk:  # Only when issuing
            book = self.book
            if book.available_copies > 0:
                book.available_copies -= 1
                book.save()
            else:
                raise ValueError("No copies available for issue")
        super().save(*args, **kwargs)    
class AdmissionInquiry(models.Model):
    student_name = models.CharField(max_length=100)
    parent_name = models.CharField(max_length=100, null=True)
    contact_number = models.CharField(max_length=15, null=True)
    email = models.EmailField(blank=True, null=True)
    class_name = models.CharField(max_length=50, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.created_at}"
    #    Attendance alerts to parents
    
class Attendance(models.Model):
    selected_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_records',default=None)
    student = models.ForeignKey('Account.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')])
    remark = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date')  # Prevent duplicate entries

    def __str__(self):
        return f"{self.student.student_name} - {self.date} ({self.status})"


class TeacherAttendance(models.Model):
    selected_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='teacher_attendance_records', default=None, null=True)
    teacher = models.ForeignKey('Account.TeacherProfile', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')])
    remark = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('teacher', 'date')

    def __str__(self):
        # show teacher name if available
        try:
            name = self.teacher.teacher_name
        except Exception:
            name = str(self.teacher)
        return f"{name} - {self.date} ({self.status})"

# Basic notices ( Time table ,holidays, PTM, events)    
# from django.contrib.auth import get_user_model

# Dynamically get your custom User model
User = get_user_model()


class NoticeModel(models.Model):
    TARGET_CHOICES = [
        ('student', 'Student'),
        ('classes', 'classes'),
        ('Teachers', 'Teachers'),

    ]

    # --- Target info ---
    target = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default='students',
        help_text="Select who this notice is for"
    )
    class_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Specify class if applicable (leave empty for all classes)"
    )

    # --- Notice details ---
    title = models.CharField(max_length=200)
    description = models.TextField()
    applicable_date = models.DateField(default=timezone.localdate)

    # --- Specific students (optional) ---
    specific_students = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated names or admission numbers if notice is for specific students"
    )

    # --- Meta and control fields ---
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ✅ safer than get_user_model() at top level
        on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        related_name="notices_posted",
        default=None,
        null=True,
        blank=True
    )
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notice"
        verbose_name_plural = "Notices"

    def __str__(self):
        return f"{self.title} ({self.applicable_date})"

    # --- Helper methods ---
    def get_specific_students_list(self):
        """Convert comma-separated string to list"""
        if self.specific_students:
            return [s.strip() for s in self.specific_students.split(',') if s.strip()]
        return []

    def is_for_all_students(self):
        """Check if notice applies to all students"""
        return not self.specific_students and not self.class_name   

# Fee due reminders
class FeeModel(models.Model):
    student = models.ForeignKey('Account.StudentProfile', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    due_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=[('Paid', 'Paid'), ('Pending', 'Pending')],
        default='Pending'
    )

    def __str__(self):
        return f"{self.student.student_name} - {self.status}"

class FAQ(models.Model):
    questions  = models.CharField(max_length=255)
    answer  = models.TextField()

    def __str__(self):
        return f"{self.questions}"
    
# Homework & assignment sharing
class Homework(models.Model):
    ASSIGNMENT_TYPE_CHOICES = [
        ('class', 'Whole Class'),
        ('student', 'Specific Student(s)'),
    ]

    Assigned_By_teacher = models.ForeignKey('Account.TeacherProfile', on_delete=models.CASCADE, related_name='homeworks',default=None, null=True, blank=True)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='homeworks', blank=True, null=True)
    students = models.ManyToManyField('Account.StudentProfile', related_name='assigned_homeworks_to', blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1025)
    subject = models.CharField(max_length=100)
    due_date = models.DateField()
    file = models.FileField(upload_to='homework_files/', blank=True, null=True)
    assignment_type = models.CharField(max_length=10, choices=ASSIGNMENT_TYPE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} ({self.get_assignment_type_display()})"
    
'''Exam/grades management (marks entry +
report card).'''

class Exam(models.Model):
    EXAM_TYPES = [
        ('mid_term', 'Mid Term'),
        ('final', 'Final'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('unit_test', 'Unit Test'),
    ]
    
    EXAM_STATUS = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    class_name = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='exams')
    academic_year = models.CharField(max_length=9)
    term = models.CharField(max_length=50)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)
    exam_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)  # For exams spanning multiple days
    status = models.CharField(max_length=20, choices=EXAM_STATUS, default='upcoming')
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'class_name', 'academic_year', 'term']
        ordering = ['exam_date']
    
    def __str__(self):
        return f"{self.name} - {self.class_name} - {self.academic_year}"
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.exam_date > timezone.now().date() and self.status == 'upcoming'
    
    def save(self, *args, **kwargs):
        # Auto-update status based on dates
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.status != 'cancelled':
            if self.exam_date > today:
                self.status = 'upcoming'
            elif self.end_date and self.end_date < today:
                self.status = 'completed'
            else:
                self.status = 'ongoing'
        
        super().save(*args, **kwargs)

class ExamSubject(models.Model):
    """Bridge table for exams and subjects with subject-specific max marks"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    max_marks = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Maximum marks for this subject in this exam"
    )
    exam_time = models.TimeField(blank=True, null=True)  # Time for this subject's exam
    exam_duration = models.DurationField(blank=True, null=True)  # Duration of the exam
    
    class Meta:
        unique_together = ['exam', 'subject']
    
    def __str__(self):
        return f"{self.exam.name} - {self.subject.subject} - Max: {self.max_marks}"

class Grade(models.Model):
    student = models.ForeignKey('Account.StudentProfile', on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_marks = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    grade = models.CharField(max_length=2, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'exam', 'subject']
    
    def save(self, *args, **kwargs):
        # Calculate percentage
        if self.marks_obtained and self.max_marks:
            self.percentage = (self.marks_obtained / self.max_marks) * 100
            self.grade = self.calculate_grade(self.percentage)
            self.remarks = self.calculate_remarks(self.percentage)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def calculate_grade(percentage):
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B'
        elif percentage >= 60: return 'C'
        elif percentage >= 50: return 'D'
        else: return 'F'
    
    @staticmethod
    def calculate_remarks(percentage):
        if percentage >= 80: return 'Excellent'
        elif percentage >= 60: return 'Good'
        elif percentage >= 50: return 'Average'
        else: return 'Needs Improvement'
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.marks_obtained}/{self.max_marks}"

class ReportCard(models.Model):
    student = models.ForeignKey("Account.StudentProfile", on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    obtained_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overall_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.CharField(max_length=2, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'exam']
    
    def save(self, *args, **kwargs):
        # Calculate overall percentage and grade
        grades = Grade.objects.filter(student=self.student, exam=self.exam)
        
        if grades.exists():
            self.obtained_marks = sum(grade.marks_obtained for grade in grades)
            self.total_marks = sum(grade.max_marks for grade in grades)
            
            if self.total_marks > 0:
                self.overall_percentage = (self.obtained_marks / self.total_marks) * 100
                self.overall_grade = Grade.calculate_grade(self.overall_percentage)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Report Card - {self.student} - {self.exam}"
    
class TimeTable(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='uploadTimeTables/')
    file_type = models.CharField(max_length=20, blank=True)  # auto-filled later
    uploaded_by = models.ForeignKey('Account.TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            self.file_type = ext.lower().replace('.', '') or 'other'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title    

def aadhaar_upload_path(instance, filename):
    return f"BusData/{instance.id}/aadhaar/{filename}"


def license_upload_path(instance, filename):
    return f"BusData/{instance.id}/license/{filename}"


class Bus(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("maintenance", "Maintenance"),
    ]

    # Auto id from Django (no need to define manually)

    busNumber = models.CharField(max_length=50)
    driverName = models.CharField(max_length=100)
    driverPhone = models.CharField(max_length=20)
    capacity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    start = models.CharField(max_length=100)
    startDeparture = models.CharField(max_length=50)
    end = models.CharField(max_length=100)
    endArrival = models.CharField(max_length=50)

    aadhaarFile = models.FileField(upload_to=aadhaar_upload_path, null=True, blank=True)
    licenseFile = models.FileField(upload_to=license_upload_path, null=True, blank=True)

    aadhaarNameState = models.CharField(max_length=255, null=True, blank=True)
    aadhaarDataState = models.TextField(null=True, blank=True)

    licenseNameState = models.CharField(max_length=255, null=True, blank=True)
    licenseDataState = models.TextField(null=True, blank=True)

    addedDate = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.busNumber


class Stop(models.Model):
    # Auto ID from Django

    bus = models.ForeignKey(Bus, related_name="stops", on_delete=models.CASCADE)

    name = models.CharField(max_length=150)
    arrivalTime = models.CharField(max_length=50)
    departureTime = models.CharField(max_length=50)

    def __str__(self):
        return self.name