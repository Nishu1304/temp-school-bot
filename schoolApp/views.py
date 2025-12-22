from django.shortcuts import render
from rest_framework import generics,serializers
from rest_framework import viewsets
from rest_framework import status
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser,IsAuthenticated,AllowAny,SAFE_METHODS,BasePermission
from schoolApp.models import AdmissionInquiry,Attendance,FeeModel,FAQ,ClassRoom,Homework,Subject,Class,Book, BookIssue,TimeTable, NoticeModel
from Account.models import StaffProfile,TeacherProfile,ParentProfile,StudentProfile
from schoolApp.serializers import AdmissionInquirySerializer,AttendanceSerializer,FeeSerializer,FAQSerializer,SubjectSerializer,ClassRoomSerializer,ClassSerializer,HomeworkSerializer,BookSerializer, BookIssueSerializer,TimeTableSerializer, NoticeSerializer
from schoolApp.serializers import TeacherAttendanceSerializer
from Account.serializers import StudentProfileSerializer
from django.contrib.auth import get_user_model
from datetime import date
from django.utils import timezone
from rest_framework.response import Response
from schoolApp.permissions import IsAdminOrTeacher 
from schoolApp.models import NoticeModel
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_date
import json
import re
from rest_framework.permissions import AllowAny
from django.core.paginator import Paginator, EmptyPage
from Account.models import StudentProfile
from schoolApp.models import Class
from django.db.models import Q

from schoolApp.models import TeacherAttendance

# Create your views here.
User =  get_user_model()

@method_decorator(csrf_exempt,name='dispatch')
# class for Subject 
class SubjectAPIView(APIView):
    authentication_classes = []        # Disable SessionAuthentication (CSRF)
    # permission_classes = [AllowAny]
    
    def get(self,request,pk=None):
        if pk:
            subject = Subject.objects.get(pk=pk)
            serializer =SubjectSerializer(subject)
        else:    
            subjects = Subject.objects.all()
            serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)
    
    

    def post(self, request):
            serializer = SubjectSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        subject = get_object_or_404(Subject, pk=pk)
        serializer = SubjectSerializer(subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        subject = get_object_or_404(Subject, pk=pk)
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# APIView class for ClassRoom Model
@method_decorator(csrf_exempt,name='dispatch')
class ClassRoomAPIView(APIView):
    # permission_classes = [IsAdminOrTeacher]
    authentication_classes = [] 
    
    def get(self, request):
        classrooms = ClassRoom.objects.all()
        serializer = ClassRoomSerializer(classrooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Admin or Teacher can create (depending on your rule)
        serializer = ClassRoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        classroom = get_object_or_404(ClassRoom, pk=pk)
        serializer = ClassRoomSerializer(classroom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        classroom = get_object_or_404(ClassRoom, pk=pk)
        classroom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# APIView for Class Model
@method_decorator(csrf_exempt,name='dispatch')
class ClassAPIView(APIView):
    # permission_classes = [IsAdminUser]
    authentication_classes = [] 

    def get(self, request, pk=None):
        """
        GET all classes or a single class by ID
        """
        if pk:
            school_class = get_object_or_404(Class, pk=pk)
            serializer = ClassSerializer(school_class)
        else:
            classes = Class.objects.all()
            serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new Class
        """
        serializer = ClassSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        """
        Update an existing Class
        """
        school_class = get_object_or_404(Class, pk=pk)
        serializer = ClassSerializer(school_class, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        """
        Delete a Class
        """
        school_class = get_object_or_404(Class, pk=pk)
        school_class.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AdmissionInquiryView(generics.ListCreateAPIView,generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = [IsAdminUser]
     
    queryset = AdmissionInquiry.objects.all().order_by('created_at')
    serializer_class = AdmissionInquirySerializer


# Create Student User from Inquiry
# Once the school admin approves an inquiry, convert it into a real student user.
def approve_inquiry(inquiry_id):
    inquiry = AdmissionInquiry.objects.get(id = inquiry_id)

    # create student account
    student_user =User.objects.create_user(
       username = inquiry.student_name,
       email = inquiry.email,
       password = 'default123'
    )

    inquiry.converted = True
    inquiry.save()
    return student_user

# Get all students of a class
class ClassStudentsView(APIView):
    def get(self, request, class_id):
        # Return students for a class including parent info to help frontend display contact
        students = StudentProfile.objects.filter(class_name_id=class_id).select_related('class_name')
        data = []
        for s in students:
            data.append({
                "id": s.id,
                "name": s.student_name,
                "enrollmentNo": s.enrollment_no,
                "parent_name": s.parent_name or (getattr(s, 'parent', None) and getattr(s.parent, 'user', None) and getattr(s.parent.user, 'username', '')),
                "parent_contact": s.parent_contact or (getattr(s, 'parent', None) and getattr(s.parent, 'phone_number', '')),
                "class": f"{s.class_name.class_name}",
                "section": s.class_name.section,
            })
        return Response(data)


# --- Notices API ---
class NoticeListCreateView(generics.ListCreateAPIView):
    queryset = NoticeModel.objects.all().order_by('-created_at')
    serializer_class = NoticeSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Support query params from frontend: ?audience=students|teachers and ?class_name=<name>
        """
        qs = self.get_queryset()
        audience = request.query_params.get('audience')
        # accept both class_name and className for compatibility
        class_name = request.query_params.get('class_name') or request.query_params.get('className')

        if audience:
            if audience == 'teachers':
                qs = qs.filter(target__iexact='Teachers')
            elif audience == 'students':
                # If class_name provided, return notices targeted to that class (case-insensitive, partial match)
                # or student-targeted notices where class_name matches partially.
                if class_name:
                    # Use icontains to be more tolerant of formatting/encoding differences
                    qs = qs.filter(
                        Q(target__iexact='classes', class_name__icontains=class_name) |
                        Q(target__iexact='student', class_name__icontains=class_name) |
                        Q(target__iexact='student', specific_students__icontains=class_name)
                    )
                else:
                    qs = qs.filter(Q(target__iexact='classes') | Q(target__iexact='student'))

        serializer = self.get_serializer(qs.order_by('-created_at'), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data.copy() if isinstance(request.data, dict) else dict(request.data)

        # map frontend keys to model fields
        audience = data.get('audience')
        if audience:
            if audience == 'teachers':
                data['target'] = 'Teachers'
            else:
                if data.get('applicableTo'):
                    data['target'] = 'student'
                else:
                    data['target'] = 'classes'

        if 'className' in data:
            data['class_name'] = data.pop('className')

        if 'applicableDate' in data:
            data['applicable_date'] = data.pop('applicableDate')

        if 'applicableTo' in data:
            at = data.pop('applicableTo')
            if isinstance(at, (list, tuple)):
                data['specific_students'] = ','.join([str(x) for x in at])
            else:
                data['specific_students'] = str(at)

        try:
            if request.user and request.user.is_authenticated:
                data['posted_by'] = request.user.id
            else:
                data['posted_by'] = None
        except Exception:
            data['posted_by'] = None

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # DEBUG: confirm how many stops are saved for this bus
        try:
            created_bus = serializer.instance
            print(f"[BusCreateAPIView] saved bus id={created_bus.id} stops_count=", created_bus.stops.count())
        except Exception:
            pass
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class NoticeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NoticeModel.objects.all()
    serializer_class = NoticeSerializer
    permission_classes = [AllowAny]

    def update(self, request, *args, **kwargs):
        data = request.data.copy() if isinstance(request.data, dict) else dict(request.data)
        if 'audience' in data:
            aud = data.get('audience')
            if aud == 'teachers':
                data['target'] = 'Teachers'
            else:
                if data.get('applicableTo'):
                    data['target'] = 'student'
                else:
                    data['target'] = 'classes'
        if 'className' in data:
            data['class_name'] = data.pop('className')
        if 'applicableDate' in data:
            data['applicable_date'] = data.pop('applicableDate')
        if 'applicableTo' in data:
            at = data.pop('applicableTo')
            if isinstance(at, (list, tuple)):
                data['specific_students'] = ','.join([str(x) for x in at])
            else:
                data['specific_students'] = str(at)

        try:
            instance = self.get_object()
        except Exception:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)



# Mark attendance for all students in class
class MarkAttendanceView(APIView):
    def post(self, request):
        # Accept flexible keys from frontend: 'class_room', 'selected_class', or 'class_id'
        class_id = request.data.get('class_room') or request.data.get('selected_class') or request.data.get('class_id')
        records = request.data.get('records', [])
        # Allow optional date (ISO string) to be sent either at top-level or per-record
        top_date = request.data.get('date')
        try:
            if top_date:
                date = timezone.datetime.fromisoformat(top_date).date()
            else:
                date = timezone.now().date()
        except Exception:
            date = timezone.now().date()

        responses = []
        for record in records:
            student_id = record.get('student')
            status_value = record.get('status')
            # allow per-record date override
            record_date = date
            try:
                if record.get('date'):
                    record_date = timezone.datetime.fromisoformat(record.get('date')).date()
            except Exception:
                record_date = date

            # attendance uniquely identified by student+date
            defaults = {'status': status_value}
            # Try to coerce class id to integer before assigning to FK
            try:
                if class_id is not None:
                    defaults['selected_class_id'] = int(class_id)
            except Exception:
                # ignore invalid class id (do not set selected_class)
                pass

            attendance, created = Attendance.objects.update_or_create(
                student_id=student_id,
                date=record_date,
                defaults=defaults
            )
            responses.append(AttendanceSerializer(attendance).data)

        return Response({"message": "Attendance marked successfully", "data": responses}, status=status.HTTP_201_CREATED)


# GET: /schoolApp/attendance/?student=<id>&from=YYYY-MM-DD&to=YYYY-MM-DD
class AttendanceListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        student_id = request.query_params.get('student')
        class_id = request.query_params.get('class')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = Attendance.objects.all().select_related('student', 'selected_class')

        if student_id:
            try:
                qs = qs.filter(student_id=int(student_id))
            except Exception:
                return Response({'detail': 'Invalid student id'}, status=status.HTTP_400_BAD_REQUEST)

        if class_id:
            try:
                qs = qs.filter(selected_class_id=int(class_id))
            except Exception:
                return Response({'detail': 'Invalid class id'}, status=status.HTTP_400_BAD_REQUEST)

        if from_date:
            d = parse_date(from_date)
            if d:
                qs = qs.filter(date__gte=d)
        if to_date:
            d = parse_date(to_date)
            if d:
                qs = qs.filter(date__lte=d)

        # pagination support
        page = request.query_params.get('page')
        page_size = int(request.query_params.get('page_size') or 50)
        if page:
            try:
                paginator = Paginator(qs.order_by('-date'), page_size)
                paged = paginator.page(int(page))
            except EmptyPage:
                return Response({'count': 0, 'next': None, 'previous': None, 'results': []})
            serializer = AttendanceSerializer(paged.object_list, many=True)
            return Response({
                'count': paginator.count,
                'next': None if not paged.has_next() else f'?page={paged.next_page_number()}',
                'previous': None if not paged.has_previous() else f'?page={paged.previous_page_number()}',
                'results': serializer.data
            })

        serializer = AttendanceSerializer(qs.order_by('-date'), many=True)
        return Response(serializer.data)


# POST: /schoolApp/attendance/batch/  payload: { records: [{student, date(YYYY-MM-DD), status, selected_class}] }
class AttendanceBatchAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        records = data.get('records') or []
        if not isinstance(records, list):
            return Response({'detail': 'records must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        successes = []
        errors = []

        for idx, rec in enumerate(records):
            student_id = rec.get('student')
            status_value = rec.get('status')
            date_str = rec.get('date')
            sel_class = rec.get('selected_class') or rec.get('class') or rec.get('class_room')

            # validate required
            if not student_id:
                errors.append({'index': idx, 'error': 'student is required', 'record': rec})
                continue
            if not status_value:
                errors.append({'index': idx, 'error': 'status is required', 'record': rec})
                continue
            if not date_str:
                errors.append({'index': idx, 'error': 'date is required', 'record': rec})
                continue

            # validate student exists
            try:
                student_obj = StudentProfile.objects.get(pk=int(student_id))
            except Exception:
                errors.append({'index': idx, 'error': f'student {student_id} not found', 'record': rec})
                continue

            # validate date
            d = parse_date(date_str)
            if not d:
                errors.append({'index': idx, 'error': f'invalid date {date_str}', 'record': rec})
                continue

            # validate status value
            if status_value not in ['Present', 'Absent', 'Leave']:
                errors.append({'index': idx, 'error': f'invalid status {status_value}', 'record': rec})
                continue

            defaults = {'status': status_value}
            # validate class id if present
            if sel_class is not None:
                try:
                    class_obj = Class.objects.get(pk=int(sel_class))
                    defaults['selected_class_id'] = class_obj.id
                except Exception:
                    errors.append({'index': idx, 'error': f'invalid class id {sel_class}', 'record': rec})
                    continue

            try:
                attendance, created = Attendance.objects.update_or_create(
                    student_id=student_obj.id,
                    date=d,
                    defaults=defaults
                )
                successes.append(AttendanceSerializer(attendance).data)
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'record': rec})
                continue

        status_code = 201 if successes and not errors else (207 if successes and errors else 400)
        return Response({'message': 'batch processed', 'data': successes, 'errors': errors}, status=status_code)


class AttendanceSummaryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        class_id = request.query_params.get('class')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = Attendance.objects.all().select_related('student')
        if class_id:
            try:
                qs = qs.filter(selected_class_id=int(class_id))
            except Exception:
                return Response({'detail': 'Invalid class id'}, status=status.HTTP_400_BAD_REQUEST)

        if from_date:
            d = parse_date(from_date)
            if d:
                qs = qs.filter(date__gte=d)
        if to_date:
            d = parse_date(to_date)
            if d:
                qs = qs.filter(date__lte=d)

        # aggregate per student
        results = {}
        for a in qs:
            sid = a.student_id
            if sid not in results:
                results[sid] = {'student_id': sid, 'student_name': getattr(a.student, 'student_name', ''), 'present': 0, 'absent': 0, 'leave': 0}
            if a.status == 'Present':
                results[sid]['present'] += 1
            elif a.status == 'Absent':
                results[sid]['absent'] += 1
            elif a.status == 'Leave':
                results[sid]['leave'] += 1

        return Response(list(results.values()))


# ------------------ Teacher Attendance APIs ------------------
class TeacherMarkAttendanceView(APIView):
    def post(self, request):
        # similar to MarkAttendanceView but for teachers
        class_id = request.data.get('class_room') or request.data.get('selected_class') or request.data.get('class_id')
        records = request.data.get('records', [])
        top_date = request.data.get('date')
        try:
            if top_date:
                date = timezone.datetime.fromisoformat(top_date).date()
            else:
                date = timezone.now().date()
        except Exception:
            date = timezone.now().date()

        responses = []
        for record in records:
            teacher_id = record.get('teacher')
            status_value = record.get('status')
            record_date = date
            try:
                if record.get('date'):
                    record_date = timezone.datetime.fromisoformat(record.get('date')).date()
            except Exception:
                record_date = date

            defaults = {'status': status_value}
            try:
                if class_id is not None:
                    defaults['selected_class_id'] = int(class_id)
            except Exception:
                pass

            attendance, created = TeacherAttendance.objects.update_or_create(
                teacher_id=teacher_id,
                date=record_date,
                defaults=defaults
            )
            responses.append(TeacherAttendanceSerializer(attendance).data)

        return Response({"message": "Teacher attendance marked successfully", "data": responses}, status=status.HTTP_201_CREATED)


class TeacherAttendanceListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        teacher_id = request.query_params.get('teacher')
        class_id = request.query_params.get('class')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = TeacherAttendance.objects.all().select_related('teacher', 'selected_class')

        if teacher_id:
            try:
                qs = qs.filter(teacher_id=int(teacher_id))
            except Exception:
                return Response({'detail': 'Invalid teacher id'}, status=status.HTTP_400_BAD_REQUEST)

        if class_id:
            try:
                qs = qs.filter(selected_class_id=int(class_id))
            except Exception:
                return Response({'detail': 'Invalid class id'}, status=status.HTTP_400_BAD_REQUEST)

        if from_date:
            d = parse_date(from_date)
            if d:
                qs = qs.filter(date__gte=d)
        if to_date:
            d = parse_date(to_date)
            if d:
                qs = qs.filter(date__lte=d)

        page = request.query_params.get('page')
        page_size = int(request.query_params.get('page_size') or 50)
        if page:
            try:
                paginator = Paginator(qs.order_by('-date'), page_size)
                paged = paginator.page(int(page))
            except EmptyPage:
                return Response({'count': 0, 'next': None, 'previous': None, 'results': []})
            serializer = TeacherAttendanceSerializer(paged.object_list, many=True)
            return Response({
                'count': paginator.count,
                'next': None if not paged.has_next() else f'?page={paged.next_page_number()}',
                'previous': None if not paged.has_previous() else f'?page={paged.previous_page_number()}',
                'results': serializer.data
            })

        serializer = TeacherAttendanceSerializer(qs.order_by('-date'), many=True)
        return Response(serializer.data)


class TeacherAttendanceBatchAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        records = data.get('records') or []
        if not isinstance(records, list):
            return Response({'detail': 'records must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        successes = []
        errors = []

        from Account.models import TeacherProfile as TP

        for idx, rec in enumerate(records):
            teacher_id = rec.get('teacher')
            status_value = rec.get('status')
            date_str = rec.get('date')
            sel_class = rec.get('selected_class') or rec.get('class') or rec.get('class_room')

            if not teacher_id:
                errors.append({'index': idx, 'error': 'teacher is required', 'record': rec})
                continue
            if not status_value:
                errors.append({'index': idx, 'error': 'status is required', 'record': rec})
                continue
            if not date_str:
                errors.append({'index': idx, 'error': 'date is required', 'record': rec})
                continue

            try:
                teacher_obj = TP.objects.get(pk=int(teacher_id))
            except Exception:
                errors.append({'index': idx, 'error': f'teacher {teacher_id} not found', 'record': rec})
                continue

            d = parse_date(date_str)
            if not d:
                errors.append({'index': idx, 'error': f'invalid date {date_str}', 'record': rec})
                continue

            if status_value not in ['Present', 'Absent', 'Leave']:
                errors.append({'index': idx, 'error': f'invalid status {status_value}', 'record': rec})
                continue

            defaults = {'status': status_value}
            if sel_class is not None:
                try:
                    class_obj = Class.objects.get(pk=int(sel_class))
                    defaults['selected_class_id'] = class_obj.id
                except Exception:
                    errors.append({'index': idx, 'error': f'invalid class id {sel_class}', 'record': rec})
                    continue

            try:
                attendance, created = TeacherAttendance.objects.update_or_create(
                    teacher_id=teacher_obj.id,
                    date=d,
                    defaults=defaults
                )
                successes.append(TeacherAttendanceSerializer(attendance).data)
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'record': rec})
                continue

        status_code = 201 if successes and not errors else (207 if successes and errors else 400)
        return Response({'message': 'batch processed', 'data': successes, 'errors': errors}, status=status_code)


class TeacherAttendanceSummaryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        class_id = request.query_params.get('class')
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        qs = TeacherAttendance.objects.all().select_related('teacher')
        if class_id:
            try:
                qs = qs.filter(selected_class_id=int(class_id))
            except Exception:
                return Response({'detail': 'Invalid class id'}, status=status.HTTP_400_BAD_REQUEST)

        if from_date:
            d = parse_date(from_date)
            if d:
                qs = qs.filter(date__gte=d)
        if to_date:
            d = parse_date(to_date)
            if d:
                qs = qs.filter(date__lte=d)

        results = {}
        for a in qs:
            tid = a.teacher_id
            if tid not in results:
                results[tid] = {'teacher_id': tid, 'teacher_name': getattr(a.teacher, 'teacher_name', ''), 'present': 0, 'absent': 0, 'leave': 0}
            if a.status == 'Present':
                results[tid]['present'] += 1
            elif a.status == 'Absent':
                results[tid]['absent'] += 1
            elif a.status == 'Leave':
                results[tid]['leave'] += 1

        return Response(list(results.values()))



class FeeViewSet(viewsets.ModelViewSet):
    queryset = FeeModel.objects.all().order_by('due_date')
    serializer_class = FeeSerializer

    def get_queryset(self):
        queryset = FeeModel.objects.all().order_by('due_date')
        # filter by student id: /fee/?student=<id>
        student_id = self.request.query_params.get('student')
        if student_id:
            try:
                queryset = queryset.filter(student_id=int(student_id))
            except Exception:
                pass
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        # If due_date is in the past or today, mark Pending
        try:
            if instance.due_date <= date.today():
                instance.status = 'Pending'
                instance.save()
        except Exception:
            pass

class FAQAutoReplyView(APIView):
    def post(self,request):
        query = request.data.get('query','').lower()
        faq = FAQ.objects.filter(question__icontains=query).first()

        if faq:
            return Response({'answer':faq.answer})
        return Response({'answer':'Sorry, I could`t find that. Please contact schoole admin'})

class ClassRoomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAuthenticated]


class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Homework.objects.all().order_by('-created_at')
    serializer_class = HomeworkSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        teacher = None
        try:
            teacher = self.request.user.teacherprofile
        except:
            pass
        serializer.save(Assigned_By_teacher=teacher)


class AdminDashboard(APIView):
    # permission_classes = [IsAdminUser]     

    def get(self,request):
        #Overview counts
        overviews ={
            'total_students':StudentProfile.objects.count(),
            'total_teachers':TeacherProfile.objects.count(),
            'total_staffs':StaffProfile.objects.count(),
            'total_parants':ParentProfile.objects.count(),
            "pending_inquiries": Attendance.objects.count()
        }  
        # Recent admission inquiries (latest 5)
        recent_inquiries = list(
            AdmissionInquiry.objects.order_by('-created_at')[:5].values(
                'id', 'student_name', 'parent_name', 'contact_number', 'email', 'class_name', 'created_at'
            )
        )
         # Teachers list
        teachers_list = list(
            TeacherProfile.objects.select_related('user').values(
                'id', 'user__username', 'subjects'
            )
        )
        # Students list
        students_qs = StudentProfile.objects.select_related('user', 'parent__user')
        students_list = StudentProfileSerializer(students_qs, many=True).data

        # Classes with student count
        classes = []
        for c in Class.objects.all():
            student_count = StudentProfile.objects.filter(class_name=c).count()
            classes.append({
                "id": c.id,
                "class_name": c.class_name,
                "section_name": c.section,
                "student_count": student_count
            })
        # Recent attendance alerts (latest 5 absentees)
        absentees = list(
            Attendance.objects.filter(status='Absent').order_by('-date')[:5].select_related('student').values(
                'id', 'student__username', 'date', 'remark'
            )
        )    
        data = {
            'overviews':overviews,
            'recent_inquiries':recent_inquiries,
            'teachers_list':teachers_list,
            'students_list':students_list,
            'classes':classes,
            'absentees':absentees

        }
        return Response(data)
    
# 📘 Add & List Books
class BookListCreateView(generics.ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


# Detail / Update / Delete for single Book
class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


# 📕 Issue a Book
class IssueBookView(APIView):
    def post(self, request):
        serializer = BookIssueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Book issued successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 📗 Mark Book as Returned
class ReturnBookView(APIView):
    def put(self, request, pk):
        try:
            issue = BookIssue.objects.get(pk=pk)
        except BookIssue.DoesNotExist:
            return Response({"error": "Issue record not found"}, status=404)

        if issue.is_returned:
            return Response({"message": "Book already returned."}, status=400)

        # mark returned and set return date if not provided
        issue.is_returned = True
        if not issue.return_date:
            issue.return_date = timezone.now().date()
        issue.save()

        # Increment available copies on the related Book (do not exceed total quantity)
        try:
            book = issue.book
            current = book.available_copies or 0
            total = book.quantity or 0
            # increment but cap at total quantity
            book.available_copies = min(total, current + 1)
            book.save()
        except Exception:
            # don't fail the return if book update fails; log in server
            pass

        return Response({
            "message": "Book returned successfully",
            "book": issue.book.title,
            "return_date": issue.return_date,
            'issue_date': issue.issue_date,
            'due_date': issue.due_date,
            'available_copies': getattr(issue.book, 'available_copies', None),
        }, status=200)


# 📙 View All Issued Books
class IssuedBookListView(generics.ListAPIView):
    queryset = BookIssue.objects.all()
    serializer_class = BookIssueSerializer    


class IsAdminUserOrReadOnly(BasePermission):
    """
    Allow only admin users to create, update, or delete.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


# 🔹 CREATE (Upload TimeTable)
class TimeTableCreateAPIView(APIView):
    # permission_classes = [IsAdminUserOrReadOnly]

    def post(self, request):
        serializer = TimeTableSerializer(data=request.data)
        if serializer.is_valid():
            # uploaded_by expects a TeacherProfile instance (or None). The frontend
            # may send requests from a plain User, so attempt to resolve the
            # related TeacherProfile; fall back to None to avoid ValueError.
            uploaded_by_profile = None
            try:
                uploaded_by_profile = getattr(request.user, "teacherprofile", None)
            except Exception:
                uploaded_by_profile = None

            serializer.save(uploaded_by=uploaded_by_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔹 LIST (Get All TimeTables - Upload History)
class TimeTableListAPIView(APIView):
    permission_classes = [AllowAny]  # everyone can view

    def get(self, request):
        timetables = TimeTable.objects.all().order_by('-uploaded_on')
        serializer = TimeTableSerializer(timetables, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 🔹 RETRIEVE (Get Single TimeTable by ID)
class TimeTableDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response({'error': 'TimeTable not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TimeTableSerializer(timetable)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 🔹 UPDATE (Full update)
class TimeTableUpdateAPIView(APIView):
    # permission_classes = [IsAdminUserOrReadOnly]

    def put(self, request, pk):
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response({'error': 'TimeTable not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TimeTableSerializer(timetable, data=request.data)
        if serializer.is_valid():
            # same handling as create: try to pass TeacherProfile instance
            uploaded_by_profile = None
            try:
                uploaded_by_profile = getattr(request.user, "teacherprofile", None)
            except Exception:
                uploaded_by_profile = None

            serializer.save(uploaded_by=uploaded_by_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔹 DELETE (Remove TimeTable)
class TimeTableDeleteAPIView(APIView):
    # permission_classes = [IsAdminUserOrReadOnly]

    def delete(self, request, pk):
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response({'error': 'TimeTable not found'}, status=status.HTTP_404_NOT_FOUND)

        timetable.delete()
        return Response({'message': 'TimeTable deleted successfully'}, status=status.HTTP_204_NO_CONTENT)   


from rest_framework import generics
from schoolApp.models import Bus
from schoolApp.serializers import BusSerializer
class BusListAPIView(generics.ListAPIView):
    queryset = Bus.objects.all().prefetch_related("stops")
    serializer_class = BusSerializer


class BusCreateAPIView(generics.CreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

    def create(self, request, *args, **kwargs):
        # make mutable copy of request.data (QueryDict)
        data = request.data.copy()
        stops = data.get("stops")

        # CASE 1: stops is raw JSON string
        if isinstance(stops, str):
            try:
                data["stops"] = json.loads(stops)
            except:
                pass

        # CASE 2: stops arrives as ['[{"name":...}]'] from FormData
        elif isinstance(stops, list) and len(stops) == 1 and isinstance(stops[0], str):
            try:
                data["stops"] = json.loads(stops[0])
            except:
                pass

        # CASE 3: fallback for indexed multipart keys (stops[0][name])
        # Always check for indexed multipart keys (stops[0][field]) and prefer them when present
        pattern = re.compile(r"^stops\[(\d+)\]\[(\w+)\]$")
        assembled = {}

        for k in data.keys():
            m = pattern.match(k)
            if m:
                idx = int(m.group(1))
                field = m.group(2)
                assembled.setdefault(idx, {})[field] = data.get(k)

        if assembled:
            data["stops"] = [assembled[i] for i in sorted(assembled.keys())]

        # DEBUG: print raw incoming keys and values to help diagnose payload shape
        try:
            print("[BusCreateAPIView] raw request.data keys →", list(request.data.keys()))
            for k in request.data.keys():
                try:
                    print("  ", k, "->", request.data.getlist(k))
                except Exception:
                    print("  ", k, "->", request.data.get(k))
        except Exception:
            pass

        # Normalize stops entries further: items may be strings, QueryDicts, or dicts
        def _clean_stops(raw):
            if not raw:
                return []
            cleaned = []
            for item in raw:
                # stringified JSON for a single stop
                if isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            item = parsed
                        else:
                            # if parsed is not a dict, skip
                            continue
                    except:
                        # not JSON, skip
                        continue

                if hasattr(item, 'get'):
                    # item may be QueryDict-like where values are lists
                    name = item.get('name')
                    arrival = item.get('arrivalTime') or item.get('arrival_time')
                    departure = item.get('departureTime') or item.get('departure_time')

                    # if values are lists (from QueryDict), pick first
                    if isinstance(name, (list, tuple)):
                        name = name[0] if name else ''
                    if isinstance(arrival, (list, tuple)):
                        arrival = arrival[0] if arrival else ''
                    if isinstance(departure, (list, tuple)):
                        departure = departure[0] if departure else ''

                    cleaned.append({
                        'name': name or '',
                        'arrivalTime': arrival or '',
                        'departureTime': departure or ''
                    })
                elif isinstance(item, dict):
                    cleaned.append({
                        'name': item.get('name', '') or '',
                        'arrivalTime': item.get('arrivalTime', '') or item.get('arrival_time', '') or '',
                        'departureTime': item.get('departureTime', '') or item.get('departure_time', '') or ''
                    })
            return cleaned

        data['stops'] = _clean_stops(data.get('stops'))

        # DEBUG
        print("[BusCreateAPIView] FINAL stops →", data.get("stops"))

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # return fresh serialized data from the created instance
        try:
            created_bus = serializer.instance
            return Response(self.get_serializer(created_bus).data, status=status.HTTP_201_CREATED)
        except Exception:
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class BusDetailAPIView(generics.RetrieveAPIView):
    queryset = Bus.objects.all().prefetch_related("stops")
    serializer_class = BusSerializer


class BusUpdateAPIView(generics.UpdateAPIView):
    queryset = Bus.objects.all().prefetch_related("stops")
    serializer_class = BusSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        data = request.data.copy()
        stops = data.get("stops")
        print(data, stops)
        # CASE 1: stops raw string "[{…}]"
        if isinstance(stops, str):
            try:
                data["stops"] = json.loads(stops)
            except:
                pass

        # CASE 2: stops = ['[{…}]']
        elif isinstance(stops, list) and len(stops) == 1 and isinstance(stops[0], str):
            try:
                data["stops"] = json.loads(stops[0])
            except:
                pass

        # CASE 3: fallback for indexed keys stops[0][field]
        if not data.get("stops"):
            pattern = re.compile(r"^stops\[(\d+)\]\[(\w+)\]$")
            assembled = {}

            for k in data.keys():
                m = pattern.match(k)
                if m:
                    idx = int(m.group(1))
                    field = m.group(2)
                    assembled.setdefault(idx, {})[field] = data.get(k)

            if assembled:
                data["stops"] = [assembled[i] for i in sorted(assembled.keys())]

        # Normalize stops entries further (same logic as create)
        def _clean_stops(raw):
            if not raw:
                return []
            cleaned = []
            for item in raw:
                if isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            item = parsed
                        else:
                            continue
                    except:
                        continue

                if hasattr(item, 'get'):
                    name = item.get('name')
                    arrival = item.get('arrivalTime') or item.get('arrival_time')
                    departure = item.get('departureTime') or item.get('departure_time')

                    if isinstance(name, (list, tuple)):
                        name = name[0] if name else ''
                    if isinstance(arrival, (list, tuple)):
                        arrival = arrival[0] if arrival else ''
                    if isinstance(departure, (list, tuple)):
                        departure = departure[0] if departure else ''

                    cleaned.append({
                        'name': name or '',
                        'arrivalTime': arrival or '',
                        'departureTime': departure or ''
                    })
                elif isinstance(item, dict):
                    cleaned.append({
                        'name': item.get('name', '') or '',
                        'arrivalTime': item.get('arrivalTime', '') or item.get('arrival_time', '') or '',
                        'departureTime': item.get('departureTime', '') or item.get('departure_time', '') or ''
                    })
            return cleaned

        data['stops'] = _clean_stops(data.get('stops'))

        print("[BusUpdateAPIView] FINAL stops →", data.get("stops"))

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # DEBUG: confirm how many stops are saved after update
        try:
            updated_bus = self.get_object()
            print(f"[BusUpdateAPIView] updated bus id={updated_bus.id} stops_count=", updated_bus.stops.count())
        except Exception:
            pass

        # return fresh serialized data from DB to ensure nested stops are represented correctly
        try:
            return Response(self.get_serializer(self.get_object()).data)
        except Exception:
            return Response(serializer.data)


class BusDeleteAPIView(generics.DestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer        