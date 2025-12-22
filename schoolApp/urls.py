
from django.urls import path
from schoolApp import views 
from rest_framework.routers import DefaultRouter
from .views import HomeworkViewSet, ClassRoomViewSet,SubjectAPIView,ClassRoomAPIView,ClassAPIView, FeeViewSet

router = DefaultRouter()
router.register(r'classrooms', ClassRoomViewSet)
router.register(r'homeworks', HomeworkViewSet)
router.register('fee', FeeViewSet, basename='fee')

urlpatterns = [
    path('admission_inquiries/', views.AdmissionInquiryView.as_view(), name='admission-inquiry-list-create'),
    path('admission_inquiries/<int:pk>/', views.AdmissionInquiryView.as_view(), name='admission-inquiry-detail'),
    
    path('subjects/', SubjectAPIView.as_view(), name='subject-list'), #for crud operations on subjects
    path('subjects/<int:pk>/', SubjectAPIView.as_view(), name='subject-detail'),

    path('classrooms/', ClassRoomAPIView.as_view(), name='classroom-list'),
    path('classrooms/<int:pk>/', ClassRoomAPIView.as_view(), name='classroom-detail'), 

    # GET /attendance/class/1/students/
    path('class/<int:class_id>/students/', views.ClassStudentsView.as_view(), name='class-students'),
    path('mark/', views.MarkAttendanceView.as_view(), name='mark-attendance'),
    path('mark/teacher/', views.TeacherMarkAttendanceView.as_view(), name='mark-teacher-attendance'),
    path('attendance/', views.AttendanceListAPIView.as_view(), name='attendance-list'),
    path('attendance/batch/', views.AttendanceBatchAPIView.as_view(), name='attendance-batch'),
    path('attendance/summary/', views.AttendanceSummaryAPIView.as_view(), name='attendance-summary'),
    path('teacher-attendance/', views.TeacherAttendanceListAPIView.as_view(), name='teacher-attendance-list'),
    path('teacher-attendance/batch/', views.TeacherAttendanceBatchAPIView.as_view(), name='teacher-attendance-batch'),
    path('teacher-attendance/summary/', views.TeacherAttendanceSummaryAPIView.as_view(), name='teacher-attendance-summary'),

    # Class APIs
    path('classes/', ClassAPIView.as_view(), name='class-list'),
    path('classes/<int:pk>/', ClassAPIView.as_view(), name='class-detail'),

    # path('attendence', views.AttendanceView.as_view(), name='attendance'),
    path('approve_inquiry', views.approve_inquiry, name='approve_inquiry'),
    path('notices/', views.NoticeListCreateView.as_view(), name='notice-list'),
    path('notices/<int:pk>/', views.NoticeDetailView.as_view(), name='notice-detail'),
    #path('fee', views.FeeView.as_view(), name='fee'),
    path('faq', views.FAQAutoReplyView.as_view(), name='faq-auto-reply'),
    path('admin_dashboard', views.AdminDashboard.as_view(), name='admin_dashboard'),
  
    # Library management
    path('books/', views.BookListCreateView.as_view(), name='book-list-create'),     # GET, POST
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),     # GET, PUT, DELETE
    path('issue/', views.IssueBookView.as_view(), name='issue-book'),                # POST
    path('return/<int:pk>/', views.ReturnBookView.as_view(), name='return-book'),    # PUT
    path('issued/', views.IssuedBookListView.as_view(), name='issued-books'),        # GET

    # TimeTable
    path('timetables/', views.TimeTableListAPIView.as_view(), name='timetable-list'),
    path('timetables/create/', views.TimeTableCreateAPIView.as_view(), name='timetable-create'),
    path('timetables/<int:pk>/', views.TimeTableDetailAPIView.as_view(), name='timetable-detail'),
    path('timetables/<int:pk>/update/',views.TimeTableUpdateAPIView.as_view(), name='timetable-update'),
    path('timetables/<int:pk>/delete/', views.TimeTableDeleteAPIView.as_view(), name='timetable-delete'),
    # BUs
    path('buses/', views.BusListAPIView.as_view(), name='bus-list'),
    path('buses/create/', views.BusCreateAPIView.as_view(), name='bus-create'),
    path('buses/<int:pk>/', views.BusDetailAPIView.as_view(), name='bus-detail'),
    path('buses/<int:pk>/update/', views.BusUpdateAPIView.as_view(), name='bus-update'),
    path('buses/<int:pk>/delete/', views.BusDeleteAPIView.as_view(), name='bus-delete'),
    
]

# ✅ Combine with router URLs
urlpatterns += router.urls