# from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics,status, filters
from rest_framework.generics import GenericAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import RegisterSerializer,LoginSerializer,ChangePasswordSerializer,StudentProfileSerializer,TeacherProfileSerializer,StaffProfileSerializer,ParentProfileSerializer
from rest_framework_simplejwt.views import TokenRefreshView
from .models import User,StudentProfile,TeacherProfile,StaffProfile,ParentProfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login , logout

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Only include a matching TeacherProfile for users who registered as teachers.
            resp = RegisterSerializer(user).data
            if getattr(user, 'role', None) == 'teacher':
                try:
                    teacher = TeacherProfile.objects.filter(email=user.email).first()
                    if teacher:
                        resp['teacher_profile'] = TeacherProfileSerializer(teacher, context={'request': request}).data
                except Exception:
                    pass
            return Response(resp, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None):
        if pk is None:
    # optional: return list of users or just an info payload
            users = User.objects.all()
            serializer = RegisterSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        try:
            user = User.objects.get(pk=pk)
            serializer = RegisterSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

# Login API
# ---------------------------

class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        # Only include a matching TeacherProfile for users with teacher role.
        teacher_profile = None
        if getattr(user, 'role', None) == 'teacher':
            try:
                teacher = TeacherProfile.objects.filter(email=user.email).first()
                if teacher:
                    teacher_profile = TeacherProfileSerializer(teacher, context={'request': request}).data
            except Exception:
                teacher_profile = None
        payload = {
            "message": "Login successful",
            "username": user.username,
            "role": user.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
        if teacher_profile:
            payload['teacher_profile'] = teacher_profile

        return Response(payload, status=status.HTTP_200_OK)
# logged out 
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

    
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
# ---------- CREATE ----------
@method_decorator(csrf_exempt,name='dispatch')
# permission_classes = [AllowAny] 
class StudentCreateAPIView(APIView):
    permission_classes = [AllowAny] 
    def post(self, request):
        serializer = StudentProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Enrollment number auto-generated via signal
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- READ ALL (LIST) ----------
class StudentListAPIView(APIView):
    def get(self, request):
        students = StudentProfile.objects.all().select_related('class_name')

        # Optional filtering, searching, ordering via query params
        class_name = request.query_params.get('class_name')
        section_name = request.query_params.get('section_name')
        gender = request.query_params.get('gender')
        is_active = request.query_params.get('is_active')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering', '-created_at')

        if class_name:
            students = students.filter(class_name=class_name)
        if section_name:
            students = students.filter(section_name=section_name)
        if gender:
            students = students.filter(gender=gender)
        if is_active:
            students = students.filter(is_active=is_active)
        if search:
            students = students.filter(
                student_name__icontains=search
            ) | students.filter(
                email__icontains=search
            ) | students.filter(
                enrollement_no__icontains=search
            ) | students.filter(
                parent_name__icontains=search
            )

        students = students.order_by(ordering)
        serializer = StudentProfileSerializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------- READ SINGLE (DETAIL) ----------
class StudentDetailAPIView(APIView):
    def get(self, request, pk):
        student = get_object_or_404(StudentProfile.objects.select_related('class_name'), pk=pk)
        serializer = StudentProfileSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------- UPDATE ----------
class StudentUpdateAPIView(APIView):
    def put(self, request, pk):
        student = get_object_or_404(StudentProfile, pk=pk)
        serializer = StudentProfileSerializer(student, data=request.data)
        if serializer.is_valid():
            # Prevent updating read-only fields
            serializer.validated_data.pop('enrollement_no', None)
            serializer.validated_data.pop('created_at', None)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        student = get_object_or_404(StudentProfile, pk=pk)
        serializer = StudentProfileSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.validated_data.pop('enrollement_no', None)
            serializer.validated_data.pop('created_at', None)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- DELETE ----------
class StudentDeleteAPIView(APIView):
    def delete(self, request, pk):
        student = get_object_or_404(StudentProfile, pk=pk)
        student.delete()
        return Response({"message": "Student deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class StudentSearchView(generics.ListAPIView):
    serializer_class = StudentProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['student_name', 'email', 'enrollement_no']

    def get_queryset(self):
        queryset = StudentProfile.objects.all().select_related('class_name')
        
        # Additional filtering by class if provided
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
            
        return queryset
    

    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer

    def perform_update(self, serializer):
        # Prevent updating read-only fields
        read_only_fields = ['staff_id', 'created_at', 'updated_at']
        for field in read_only_fields:
            if field in serializer.validated_data:
                del serializer.validated_data[field]
        serializer.save()

class TeacherSearchView(generics.ListAPIView):
    serializer_class = TeacherProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['teacher_name', 'email', 'staff_id', 'specialization']

    def get_queryset(self):
        queryset = TeacherProfile.objects.all()
        
        # Additional filtering by department if provided
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        return queryset

# ---------- CREATE ----------
class TeacherCreateAPIView(APIView):
    def post(self, request):
        serializer = TeacherProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            # Return a fresh serialization with request context so profile_picture_url is present
            out = TeacherProfileSerializer(instance, context={'request': request}).data
            return Response(out, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- LIST (READ ALL) ----------
class TeacherListAPIView(APIView):
    def get(self, request):
        teachers = TeacherProfile.objects.all()

        # Optional filters
        department = request.query_params.get('department')
        gender = request.query_params.get('gender')
        specialization = request.query_params.get('specialization')
        is_active = request.query_params.get('is_active')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering', '-joining_date')

        # Apply filters
        if department:
            teachers = teachers.filter(department=department)
        if gender:
            teachers = teachers.filter(gender=gender)
        if specialization:
            teachers = teachers.filter(specialization=specialization)
        if is_active:
            teachers = teachers.filter(is_active=is_active)
        if search:
            teachers = teachers.filter(
                teacher_name__icontains=search
            ) | teachers.filter(
                email__icontains=search
            ) | teachers.filter(
                staff_id__icontains=search
            ) | teachers.filter(
                department__icontains=search
            ) | teachers.filter(
                specialization__icontains=search
            )

        teachers = teachers.order_by(ordering)
        serializer = TeacherProfileSerializer(teachers, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------- DETAIL (READ SINGLE) ----------
class TeacherDetailAPIView(APIView):
    def get(self, request, pk):
        teacher = get_object_or_404(TeacherProfile.objects.all(), pk=pk)
        serializer = TeacherProfileSerializer(teacher, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------- UPDATE ----------
class TeacherUpdateAPIView(APIView):
    def put(self, request, pk):
        teacher = get_object_or_404(TeacherProfile, pk=pk)
        serializer = TeacherProfileSerializer(teacher, data=request.data, context={'request': request})
        if serializer.is_valid():
            # Prevent updating read-only fields
            for field in ['staff_id', 'updated_at']:
                serializer.validated_data.pop(field, None)
            instance = serializer.save()
            out = TeacherProfileSerializer(instance, context={'request': request}).data
            return Response(out, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        teacher = get_object_or_404(TeacherProfile, pk=pk)
        serializer = TeacherProfileSerializer(teacher, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            for field in ['staff_id', 'updated_at']:
                serializer.validated_data.pop(field, None)
            instance = serializer.save()
            out = TeacherProfileSerializer(instance, context={'request': request}).data
            return Response(out, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------- DELETE ----------
class TeacherDeleteAPIView(APIView):
    def delete(self, request, pk):
        teacher = get_object_or_404(TeacherProfile, pk=pk)
        teacher.delete()
        return Response({"message": "Teacher deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@method_decorator(csrf_exempt,name='dispatch')
class ParentProfileView(APIView):
    authentication_classes = []        # Disable SessionAuthentication (CSRF)
    permission_classes = [AllowAny]     # Allow public access for now
    def get(self, request, pk):
        try:
            profile = ParentProfile.objects.get(pk=pk)
            serializer = ParentProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ParentProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},   # no serializer here
                status=status.HTTP_404_NOT_FOUND
            )
   
    def put(self,request,pk):
        try:
            profile = ParentProfile.objects.get(pk=pk)
            serializer = ParentProfileSerializer(profile,data = request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
        except ParentProfile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)        
    
    def delete(self,request,pk):
            profile = ParentProfile.objects.get(pk=pk)
            profile.delete()
            return Response("Parent Profile Deleted")

@method_decorator(csrf_exempt, name='dispatch')
class TeacherProfileView(APIView):
    authentication_classes = []        # Disable SessionAuthentication (CSRF)
    permission_classes = [AllowAny]     # Allow public access for now

    def get(self, request, pk):
        try:
            profile = TeacherProfile.objects.get(pk=pk)
            serializer = TeacherProfileSerializer(profile, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        try:
            profile = TeacherProfile.objects.get(pk=pk)
            serializer = TeacherProfileSerializer(profile, data=request.data, context={'request': request})
            if serializer.is_valid():
                instance = serializer.save()
                out = TeacherProfileSerializer(instance, context={'request': request}).data
                return Response(out, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
@method_decorator(csrf_exempt, name='dispatch')

            
class StaffProfileView(APIView):
    authentication_classes = []        # Disable SessionAuthentication (CSRF)
    permission_classes = [AllowAny]    # Allow public access for now
    def get(self, request, pk):
        try:
            profile = StaffProfile.objects.get(pk=pk)
            serializer = StaffProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StaffProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},   # no serializer here
                status=status.HTTP_404_NOT_FOUND
            )
   
    def put(self,request,pk):
        try:
            profile = StaffProfile.objects.get(pk=pk)
            serializer = StaffProfileSerializer(profile,data = request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
        except StaffProfile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)        

    def delete(self,request,pk):
            profile = StaffProfile.objects.get(pk=pk)
            profile.delete()
            return Response("StaffProfile  Deleted") 