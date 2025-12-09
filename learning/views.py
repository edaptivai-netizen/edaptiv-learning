from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from .forms import StudentRegistrationForm, TeacherRegistrationForm, StudyMaterialForm, StudentProfileUpdateForm
from .models import (
    User, StudentProfile, TeacherProfile, StudyMaterial, 
    AdaptedContent, StudentProgress, Challenge, ClassGroup, LearningStyle
)
from .ai_tutor import adapt_content_for_student
from learning import models 
from django.utils import timezone
from utils.ai_integration import DIDVideoGenerator
import json
from utils.s3_utils import generate_presigned_url
from django.conf import settings
import boto3
import uuid
from io import BytesIO
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
import requests
from learning.models import AdaptedContent
from learning.models import StudyMaterial, StudentProfile

import logging   
logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone 
from utils.s3_utils import generate_presigned_url
import requests

#-----------
#health
#---------
def health_check(request):
    return JsonResponse({"status": "ok"})


# -------------------------
# Homepage
# -------------------------
def home_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile'):
            return redirect('student-dashboard')
        elif hasattr(request.user, 'teacher_profile'):
            return redirect('teacher-dashboard')
    

    context = {
        'total_students': StudentProfile.objects.count(),
        'total_materials': StudyMaterial.objects.count(),
        'total_teachers': TeacherProfile.objects.count(),
    }
    
    return render(request, 'home.html', context) 


def about(request):
    return render(request, 'about.html')

# -------------------------
# Registration Views
# -------------------------
def register_choice(request):
    """Let user choose between student or teacher registration"""
    return render(request, 'register_choice.html')


def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to EDAPTIV! Your personalized learning journey begins now.')
            return redirect('student-dashboard')
    else:
        form = StudentRegistrationForm()
    
    context = {
        'form': form,
        'challenges': Challenge.objects.all(),
        'learning_styles': LearningStyle.objects.all(),
    }

    return render(request, 'register_student.html',context) 
        

@login_required
def student_materials(request):
    user = request.user
    student_profile = getattr(user, 'student_profile', None)

    if not student_profile:
        # Prevent teachers/admins from using this view
        return render(request, 'error.html', {'message': 'Student profile not found.'})

    # Get student's institution, class groups, and grade
    institution = user.institution
    class_groups = student_profile.class_groups.all()
    grade_level = student_profile.grade_level

    # Start with materials from the same institution
    materials = StudyMaterial.objects.filter(user=request.user)

    # Filter for materials matching class group OR grade level
    materials = materials.filter(
        models.Q(class_group__in=class_groups) |
        models.Q(grade_level=grade_level)
    ).distinct()

    return render(request, 'student_materials.html', {'materials': materials})



def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to EDAPTIV! Start uploading materials for your students.')
            return redirect('teacher-dashboard')
    else:
        form = TeacherRegistrationForm()

    return render(request, 'register_teacher.html', {'form': form})


@login_required
def teacher_materials(request):
    user = request.user
    institution = user.institution
    # Getting all class groups from this institution
    class_groups = ClassGroup.objects.filter(institution=institution)
    # Starts with all materials from this institution
    materials = StudyMaterial.objects.filter(institution=institution)
    # Filter by selected class group (if provided in the query)
    class_group_id = request.GET.get('class_group')
    if class_group_id:
        materials = materials.filter(class_group_id=class_group_id)

    context = {
        'materials': materials,
        'class_groups': class_groups,
        'selected_class': class_group_id,
    }
    return render(request, 'teacher_materials.html', context)


# -------------------------
# Login & Logout
# -------------------------
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                # redirect based on profile type
                if hasattr(user, 'student_profile'):
                    return redirect('student-dashboard')
                elif hasattr(user, 'teacher_profile'):
                    return redirect('teacher-dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


# -------------------------
# Student Dashboard
# -------------------------
@login_required
def student_dashboard(request):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')
    
    # Get recommended materials based on student's profile
    recommended_materials = StudyMaterial.objects.filter(
    Q(target_learning_styles=profile.learning_style) |
    Q(target_challenges__in=profile.challenges.all()) |
    Q(target_learning_styles__isnull=True) |
    Q(target_challenges__isnull=True)
).distinct()[:6]

    
    # Get student's progress
    progress = StudentProgress.objects.filter(student=request.user).select_related('material')
    
    # Get recently adapted content
    recent_content = AdaptedContent.objects.filter(student=request.user).order_by('-created_at')[:5]
    
    # Calculate overall progress
    total_progress = progress.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0
    
    context = {
        'profile': profile,
        'challenges': profile.challenges.all(),
        'learning_style': profile.learning_style,
        'recommended_materials': recommended_materials,
        'progress': progress,
        'recent_content': recent_content,
        'total_progress': round(total_progress, 2),
        'total_materials': progress.count(),
    }
    
    return render(request, 'student_dashboard.html', context)


# -------------------------
# Teacher Dashboard
# -------------------------
@login_required
def teacher_dashboard(request):
    """Teacher Dashboard - Fixed Version"""
    
    # Check if user has teacher profile
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('home')
    
    try:
        profile = request.user.teacher_profile
    except Exception as e:
        messages.error(request, f'Error loading teacher profile: {str(e)}')
        return redirect('home')
    
    # Get materials uploaded by THIS USER (not profile)
    materials = StudyMaterial.objects.filter(
        uploaded_by=request.user  # Use request.user, NOT profile
    ).order_by('-uploaded_at')
    
    # Count total materials
    total_materials = materials.count()
    
    # Count unique students who accessed these materials
    # Use request.user, NOT profile
    total_students_reached = StudentProgress.objects.filter(
        material__uploaded_by=request.user
    ).values('student').distinct().count()
    
    # Debug prints (remove these later)
    print(f"👤 Teacher: {request.user.username}")
    print(f"📚 Materials: {total_materials}")
    print(f"👨‍🎓 Students reached: {total_students_reached}")
    
    context = {
        'profile': profile,
        'materials': materials,
        'total_materials': total_materials,
        'total_students_reached': total_students_reached,
    }
    
    return render(request, 'teacher_dashboard.html', context)

# -------------------------
# Study Materials
# -------------------------
@login_required
def materials_library(request):
    """Browse all available study materials"""
    materials = StudyMaterial.objects.all().order_by('-uploaded_at')
    
    # Filter by subject
    subject = request.GET.get('subject')
    if subject:
        materials = materials.filter(subject=subject)
    
    # Filter by learning style (for students)
    if hasattr(request.user, 'student_profile'):
        profile = request.user.student_profile
        if profile.learning_style:
            materials = materials.filter(target_learning_styles=profile.learning_style)
    
    context = {
        'materials': materials,
        'subjects': StudyMaterial.SUBJECT_CHOICES,
    }
    
    return render(request, 'materials_library.html', context)

@login_required
def materials_view(request):
    user_institution = request.user.institution
    materials = StudyMaterial.objects.filter(institution=user_institution)

    return render(request, "materials_library.html", {"materials": materials})

@login_required
def material_detail(request, material_id):

    material = get_object_or_404(StudyMaterial, id=material_id)
    progress = None
    adapted_content = None

    if hasattr(request.user, "student_profile"):
        progress, _ = StudentProgress.objects.get_or_create(
            student=request.user, material=material
        )

        adapted_content, _ = AdaptedContent.objects.get_or_create(
            original_material=material,
            student=request.user,
        )

    # ALWAYS create fresh URL each time with 6 hour expiration
    video_url = None
    if adapted_content and adapted_content.video_s3_key:
        from utils.s3_utils import generate_presigned_url
        
        video_url = generate_presigned_url(adapted_content.video_s3_key, expires_in=21600)

    return render(request, "material_detail.html", {
        "material": material,
        "progress": progress,
        "adapted_content": adapted_content,
        "video_url": video_url,
    })

@login_required
def generate_video(request, material_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=400)

    material = get_object_or_404(StudyMaterial, id=material_id)
    student = request.user

    adapted = get_object_or_404(AdaptedContent, original_material=material, student=student)

    # If already completed, return fast
    if adapted.video_s3_key and adapted.video_generation_status == "completed":
        return JsonResponse({"success": True, "status": "completed", "talk_id": adapted.video_talk_id})

    # mark generating
    adapted.video_generation_status = "generating"
    adapted.video_error_message = None
    adapted.save(update_fields=["video_generation_status", "video_error_message"])

    script = (adapted.adapted_text or "").strip()
    if len(script) < 10:
        script = f"Hello! Let's learn about {material.title}. {material.description or ''}"

    try:
        did = DIDVideoGenerator()
        filename_key = f"videos/{material.id}_{uuid.uuid4().hex[:12]}.mp4"
        res = did.create_and_stream_to_s3(script, material.subject, s3_key=filename_key, timeout_sec=240)
        if not res.get("success"):
            adapted.video_generation_status = "failed"
            adapted.video_error_message = res.get("error")
            adapted.save(update_fields=["video_generation_status", "video_error_message"])
            return JsonResponse({"success": False, "error": adapted.video_error_message}, status=500)

        # success: save key + metadata
        adapted.video_s3_key = res.get("s3_key")
        adapted.video_talk_id = res.get("talk_id")
        adapted.video_generated_at = timezone.now()
        adapted.video_generation_status = "completed"
        adapted.video_error_message = None
        adapted.save(update_fields=[
            "video_s3_key", "video_talk_id", "video_generated_at",
            "video_generation_status", "video_error_message"
        ])
        return JsonResponse({"success": True, "status": "completed", "talk_id": adapted.video_talk_id})
    except Exception as exc:
        logger.exception("generate_video error")
        adapted.video_generation_status = "failed"
        adapted.video_error_message = str(exc)
        adapted.save(update_fields=["video_generation_status", "video_error_message"])
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
    
@login_required
def get_fresh_video(request, material_id):
    material = get_object_or_404(StudyMaterial, id=material_id)
    adapted = get_object_or_404(AdaptedContent, original_material=material, student=request.user)

    if not adapted.video_s3_key:
        return JsonResponse({"success": False, "error": "Video not generated"}, status=404)

    url = generate_presigned_url(adapted.video_s3_key, expires_in=21600)
    return JsonResponse({"success": True, "video_url": url, "talk_id": adapted.video_talk_id})


# Add this new view to check video status
@login_required
def check_video_status(request, material_id):
    material = get_object_or_404(StudyMaterial, id=material_id)
    adapted = get_object_or_404(AdaptedContent, original_material=material, student=request.user)

    if adapted.video_generation_status == "failed":
        return JsonResponse({"success": False, "status": "failed", "error": adapted.video_error_message})
    if adapted.video_generation_status == "completed" and adapted.video_s3_key:
        # Use 6-hour expiration 
        return JsonResponse({"success": True, "status": "completed", "video_url": generate_presigned_url(adapted.video_s3_key, expires_in=21600)})
    return JsonResponse({"success": True, "status": "generating"})

@login_required
def upload_material(request):
    """Teachers upload study materials"""
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, 'Only teachers can upload materials.')
        return redirect('home')
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user  # Use request.user
            material.institution = request.user.institution
            material.save()
            form.save_m2m()
            messages.success(request, f'Material "{material.title}" uploaded successfully!')
            return redirect('teacher-dashboard')
    else:
        form = StudyMaterialForm()
    
    return render(request, 'upload_material.html', {'form': form})



@login_required
def edit_material(request, material_id):
    """Edit existing study material"""
    # Use request.user, not profile
    material = get_object_or_404(
        StudyMaterial, 
        id=material_id, 
        uploaded_by=request.user  # Use request.user
    )
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material "{material.title}" updated successfully!')
            return redirect('teacher-dashboard')
    else:
        form = StudyMaterialForm(instance=material)
    
    return render(request, 'edit_material.html', {'form': form, 'material': material})


@login_required
def delete_material(request, material_id):
    """Delete study material"""
    # Use request.user, not profile
    material = get_object_or_404(
        StudyMaterial, 
        id=material_id, 
        uploaded_by=request.user  # Use request.user
    )
    
    if request.method == 'POST':
        material_title = material.title
        material.delete()
        messages.success(request, f'Material "{material_title}" deleted successfully!')
        return redirect('teacher-dashboard')
    
    return render(request, 'delete_material.html', {'material': material})
# -------------------------
# Student Profile Management
# -------------------------
@login_required
def edit_profile(request):
    """Edit student profile"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Profile not found.')
        return redirect('home')
    
    profile = request.user.student_profile
    
    if request.method == 'POST':
        form = StudentProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student-dashboard')
    else:
        form = StudentProfileUpdateForm(instance=profile)
    
    return render(request, 'edit_profile.html', {'form': form})


# -------------------------
# Progress Tracking
# -------------------------
@login_required
def update_progress(request, material_id):
    """Update student progress on a material (AJAX)"""
    if request.method == 'POST':
        material = get_object_or_404(StudyMaterial, id=material_id)
        progress, created = StudentProgress.objects.get_or_create(
            student=request.user,
            material=material
        )
        
        completion = int(request.POST.get('completion_percentage', progress.completion_percentage))
        time_spent = int(request.POST.get('time_spent', 0))
        
        progress.completion_percentage = completion
        progress.time_spent_minutes += time_spent
        progress.save()
        
        return JsonResponse({
            'success': True,
            'completion': progress.completion_percentage,
            'time_spent': progress.time_spent_minutes
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def my_progress(request):
    """View all student progress"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    progress_list = StudentProgress.objects.filter(
        student=request.user
    ).select_related('material').order_by('-last_accessed')
    
    # Calculate statistics
    total_materials = progress_list.count()
    completed_materials = progress_list.filter(completion_percentage=100).count()
    total_time = sum(p.time_spent_minutes for p in progress_list)
    avg_completion = progress_list.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0
    
    context = {
        'progress_list': progress_list,
        'total_materials': total_materials,
        'completed_materials': completed_materials,
        'total_time_hours': round(total_time / 60, 1),
        'avg_completion': round(avg_completion, 1),
    }
    
    return render(request, 'my_progress.html', context)

# views.py - Optimize health check
from django.http import JsonResponse
import time

def health_check(request):
    """Ultra-fast health check"""
    start_time = time.time()
    
    # Do minimal work
    data = {
        "status": "healthy",
        "timestamp": start_time,
        "response_time_ms": 0
    }
    
    # Calculate response time
    data["response_time_ms"] = (time.time() - start_time) * 1000
    
    return JsonResponse(data)