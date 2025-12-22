from rest_framework import serializers
from django.contrib.auth import authenticate,get_user_model
from Account.models import StudentProfile

# from Account.models import User, Profile ,StudentProfile,TeacherProfile,StaffProfile,ParentProfile

from schoolApp.models import AdmissionInquiry,Attendance,FeeModel,FAQ,ClassRoom,Homework, Subject,Class,Book, BookIssue, Exam, ExamSubject, Grade, ReportCard,TimeTable,Bus,Stop
User  =  get_user_model()


# serializer for AdmissionInquiry 
class AdmissionInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionInquiry
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    # StudentProfile stores student_name; map that for frontend convenience
    student_name = serializers.CharField(source='student.student_name', read_only=True)
    # selected_class is the FK on Attendance -> Class; expose a human readable class label
    class_name = serializers.CharField(source='selected_class.class_name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'selected_class', 'class_name', 'student', 'student_name', 'date', 'status', 'remark']


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.teacher_name', read_only=True)
    class_name = serializers.CharField(source='selected_class.class_name', read_only=True)

    class Meta:
        model = __import__('schoolApp.models', fromlist=['TeacherAttendance']).TeacherAttendance
        fields = ['id', 'selected_class', 'class_name', 'teacher', 'teacher_name', 'date', 'status', 'remark']
    
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = '__all__'


class ClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = Class
        fields = '__all__'

    def validate(self, data):
        subjects = data.get('subjects', [])

        # subjects must be a list
        if not isinstance(subjects, list):
            raise serializers.ValidationError("Subjects must be a list.")

        # max 7 subjects
        if len(subjects) > 7:
            raise serializers.ValidationError("A class cannot have more than 7 subjects.")

        # student_count / max_seats validation
        student_count = data.get('student_count')
        max_seats = data.get('max_seats')

        if student_count is not None and max_seats is not None:
            if student_count > max_seats:
                raise serializers.ValidationError(
                    "Student count cannot be greater than maximum seats available."
                )

        return data

from schoolApp.models import NoticeModel


class NoticeSerializer(serializers.ModelSerializer):
    # Provide frontend-friendly field names in the JSON output
    className = serializers.CharField(source='class_name', read_only=True)
    applicableDate = serializers.DateField(source='applicable_date', read_only=True, format='%Y-%m-%d')
    applicableTo = serializers.SerializerMethodField()
    postedBy = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True, format='%Y-%m-%dT%H:%M:%S')

    class Meta:
        model = NoticeModel
        # include model fields so updates still work, but representation will include friendly names
        fields = [
            'id', 'target', 'class_name', 'className', 'title', 'description', 'applicable_date', 'applicableDate',
            'specific_students', 'applicableTo', 'posted_by', 'postedBy', 'is_published', 'created_at', 'createdAt', 'updated_at'
        ]

    def get_applicableTo(self, obj):
        # Return list of specific students if available
        if obj.specific_students:
            return [s.strip() for s in obj.specific_students.split(',') if s.strip()]
        return []

    def get_postedBy(self, obj):
        try:
            return obj.posted_by.username if obj.posted_by else None
        except Exception:
            return None
class FeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeModel
        fields = "__all__"
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
         model = FAQ   
         fields = '__all__'          

class HomeworkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='Assigned_By_teacher.username', read_only=True)

    # Student IDs (ManyToMany)
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=StudentProfile.objects.all(),
        source='students',
        many=True,
        required=False
    )

    # Student names
    student_names = serializers.SlugRelatedField(
        slug_field='student_name',       # FIXED
        source='students',
        read_only=True,
        many=True
    )

    class Meta:
        model = Homework
        fields = [
            'id', 'Assigned_By_teacher', 'teacher_name',
            'assignment_type',
            'class_name',               # ⭐ ADDED — REQUIRED
            'student_ids', 'student_names',
            'title', 'description', 'subject', 'due_date',
            'file', 'created_at'
        ]
        read_only_fields = ['created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = getattr(self, "initial_data", {})

        classroom_id = data.get("class_name")

        if classroom_id:
            self.fields["student_ids"].queryset = StudentProfile.objects.filter(
                class_name_id=classroom_id
            )   # FIXED
        else:
            self.fields["student_ids"].queryset = StudentProfile.objects.none()

    def validate(self, attrs):
        assignment_type = attrs.get("assignment_type")
        class_obj = attrs.get("class_name")       # FIXED (was classroom)
        students = attrs.get("students", [])

        if assignment_type == "class" and not class_obj:
            raise serializers.ValidationError({"class_name": "Class is required for class assignments."})

        if assignment_type == "student" and not students:
            raise serializers.ValidationError({"students": "At least one student is required."})

        return attrs

    def create(self, validated_data):
        students = validated_data.pop("students", [])
        homework = Homework.objects.create(**validated_data)
        if students:
            homework.students.set(students)
        return homework

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'


class BookIssueSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    issued_user = serializers.CharField(source='issued_to.username', read_only=True)

    class Meta:
        model = BookIssue
        fields = [
            'id', 'book', 'book_title', 'issued_to', 'issued_user',
            'issue_date', 'due_date', 'return_date', 'is_returned'
        ]    
    def validate(self, data):
        issue_date = data.get("issue_date")
        due_date = data.get("due_date")
        return_date = data.get("return_date")
        is_returned = data.get("is_returned", False)

        if due_date and issue_date and due_date < issue_date:
            raise serializers.ValidationError("Due date must be after issue date.")
        if return_date and issue_date and return_date < issue_date:
            raise serializers.ValidationError("Return date cannot be before issue date.")
        if is_returned and not return_date:
            raise serializers.ValidationError("Return date required when returned is True.")

        return data


class ExamSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.subject', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    
    class Meta:
        model = ExamSubject
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    class_name_detail = ClassSerializer(source='class_name', read_only=True)
    subjects = ExamSubjectSerializer(source='exam_subjects', many=True, read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    upcoming_subjects = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = '__all__'
    
    def get_upcoming_subjects(self, obj):
        """Get subjects for this exam that haven't been graded for a student"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # You can customize this based on your needs
            # For example, get subjects that student hasn't taken yet
            return ExamSubjectSerializer(
                obj.exam_subjects.all(), 
                many=True
            ).data
        return []

class ExamCreateSerializer(serializers.ModelSerializer):
    subjects = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of subjects with max_marks: [{'subject': 1, 'max_marks': 100}]"
    )
    
    class Meta:
        model = Exam
        fields = '__all__'
    
    def create(self, validated_data):
        subjects_data = validated_data.pop('subjects', [])
        exam = Exam.objects.create(**validated_data)
        
        # Create exam subjects
        for subject_data in subjects_data:
            ExamSubject.objects.create(
                exam=exam,
                subject_id=subject_data['subject'],
                max_marks=subject_data['max_marks']
            )
        
        return exam

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    subject_name = serializers.CharField(source='subject.subject', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    class_name = serializers.CharField(source='exam.class_name.name', read_only=True)
    
    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ('grade', 'percentage', 'remarks')

class ReportCardSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    exam_details = ExamSerializer(source='exam', read_only=True)
    grades = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportCard
        fields = '__all__'
    
    def get_grades(self, obj):
        grades = Grade.objects.filter(student=obj.student, exam=obj.exam)
        return GradeSerializer(grades, many=True).data
    
    #  TimeTableSerializer
class TimeTableSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    uploaded_on = serializers.DateTimeField(read_only=True, format="%y-%m-%d - %H:%M")

    class Meta:
        model = TimeTable
        fields = "__all__"
        read_only_fields = ['file_type', 'uploaded_by_name', 'uploaded_on']    


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ["id", "name", "arrivalTime", "departureTime"]


class BusSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, required=False)

    class Meta:
        model = Bus
        fields = [
            "id",
            "busNumber",
            "driverName",
            "driverPhone",
            "capacity",
            "status",
            "start",
            "startDeparture",
            "end",
            "endArrival",
            "aadhaarFile",
            "licenseFile",
            "aadhaarNameState",
            "aadhaarDataState",
            "licenseNameState",
            "licenseDataState",
            "addedDate",
            "stops",
        ]
        read_only_fields = ["addedDate"]

    # CREATE with nested stops
    def create(self, validated_data):
        stops_data = validated_data.pop("stops", [])
        bus = Bus.objects.create(**validated_data)
        # create stops defensively (accept arrivalTime or arrival_time keys)
        for stop in stops_data:
            name = stop.get("name") or stop.get("stop_name") or ""
            arrival = stop.get("arrivalTime") or stop.get("arrival_time") or ""
            departure = stop.get("departureTime") or stop.get("departure_time") or ""
            s = Stop.objects.create(bus=bus, name=str(name), arrivalTime=str(arrival), departureTime=str(departure))
            try:
                # debug
                print(f"[BusSerializer.create] created Stop id={s.id} for bus={bus.id}")
            except Exception:
                pass
        return bus

    # UPDATE with nested stops
    def update(self, instance, validated_data):
        stops_data = validated_data.pop("stops", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if stops_data is not None:
            # remove existing stops and recreate from provided data
            instance.stops.all().delete()
            for stop in stops_data:
                name = stop.get("name") or stop.get("stop_name") or ""
                arrival = stop.get("arrivalTime") or stop.get("arrival_time") or ""
                departure = stop.get("departureTime") or stop.get("departure_time") or ""
                s = Stop.objects.create(bus=instance, name=str(name), arrivalTime=str(arrival), departureTime=str(departure))
                try:
                    print(f"[BusSerializer.update] created Stop id={s.id} for bus={instance.id}")
                except Exception:
                    pass

        return instance        