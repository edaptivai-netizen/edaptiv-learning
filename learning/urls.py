from django.urls import path
from . import views
from .views import health_check

urlpatterns = [
    # Homepage
    path('', views.home_view, name='home'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_choice, name='register-choice'),
    path('register/student/', views.register_student, name='register-student'),
    path('register/teacher/', views.register_teacher, name='register-teacher'),
    
    # Student Routes
    path('student/dashboard/', views.student_dashboard, name='student-dashboard'),
    path('student/profile/edit/', views.edit_profile, name='edit-profile'),
    path('student/progress/', views.my_progress, name='my-progress'),
    path('student-materials/', views.student_materials, name='student-materials'),

    # Material detail page (SINGLE ENTRY - choose one format)
    path('material/<int:material_id>/', views.material_detail, name='material-detail'),
    
    # Video generation endpoints (use consistent pattern)
    path('material/<int:material_id>/generate-video/', views.generate_video, name='generate-video'),
    path('material/<int:material_id>/video-status/', views.check_video_status, name='check-video-status'),
    path('material/<int:material_id>/get-fresh-video/', views.get_fresh_video, name='get-fresh-video'),
    path('material/<int:material_id>/update-progress/', views.update_progress, name='update-progress'),
    
    # Health Check
    path('health/', health_check, name='health'),

    # Teacher Routes
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher-dashboard'),
    path('teacher/upload/', views.upload_material, name='upload-material'),
    path('teacher/material/<int:material_id>/edit/', views.edit_material, name='edit-material'),
    path('teacher/material/<int:material_id>/delete/', views.delete_material, name='delete-material'),
    path('teacher-materials/', views.teacher_materials, name='teacher-materials'),

    # Study Materials Library
    path('materials/', views.materials_library, name='materials-library'),
    
    # Progress Tracking (AJAX)
    path('progress/update/<int:material_id>/', views.update_progress, name='update-progress'),

    # About page
    path('about/', views.about, name='about'),
]