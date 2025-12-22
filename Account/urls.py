

from django.urls import path
from Account import views  

urlpatterns = [
    
    path('register/', views.RegisterView.as_view(), name='register'),       # POST
    path('register/<int:pk>/', views.RegisterView.as_view(), name='user-detail'),  # GET
    path('login/', views.LoginView.as_view(), name='jwt-login'),
    path('logout/', views.LogoutView.as_view(), name='jwt-logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile-detail'),  # GET
    # path('profile/', views.ProfileView.as_view(), name='profile-detail'),  # POST
    # path('student_profile/<int:pk>/', views.StudentProfileView.as_view(), name='student-profile-detail'), # GET
    # path('student_profile/', views.StudentProfileView.as_view(), name='student-profile-detail'),  # POST

    # Student CRUD endpoints
    path('students/', views.StudentListAPIView.as_view(), name='student-list'),
    path('students/create/', views.StudentCreateAPIView.as_view(), name='student-create'),
    path('students/<int:pk>/', views.StudentDetailAPIView.as_view(), name='student-detail'),
    path('students/<int:pk>/update/', views.StudentUpdateAPIView.as_view(), name='student-update'),
    path('students/<int:pk>/delete/', views.StudentDeleteAPIView.as_view(), name='student-delete'), 
    path('students/search/', views.StudentSearchView.as_view(), name='student-search'),

    path('teachers/', views.TeacherListAPIView.as_view(), name='teacher-list'),
    path('teachers/create/',views.TeacherCreateAPIView.as_view(), name='teacher-create'),
    path('teachers/<int:pk>/', views.TeacherDetailAPIView.as_view(), name='teacher-detail'),
    path('teachers/<int:pk>/update/', views.TeacherUpdateAPIView.as_view(), name='teacher-update'),
    path('teachers/<int:pk>/delete/', views.TeacherDeleteAPIView.as_view(), name='teacher-delete'),
    path('teachers/search/', views.TeacherSearchView.as_view(), name='teacher-search'),    

    path('parent_profile/<int:pk>/', views.ParentProfileView.as_view(), name='parent-profile-detail'),  # GET
    path('parent_profile/', views.ParentProfileView.as_view(), name='parent-profile-detail'),  # POST

    path('staff_profile/<int:pk>/', views.StaffProfileView.as_view(), name='staff-profile-detail'),  # GET
    path('staff_profile/', views.StaffProfileView.as_view(), name='staff-profile-detail'),  # POST

      
]

