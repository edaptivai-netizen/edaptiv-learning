from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from config import settings 
import random
import string
from datetime import datetime



# -------------------------
# Institution Model
# -------------------------
class Institution(models.Model):
    name = models.CharField(max_length=255)
    institution_id  = models.CharField(max_length=20, unique=True, help_text="Unique institution id", editable=False, null=True, blank=True)
    address = models.TextField()
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    institution_code = models.CharField(max_length=20, unique=True, help_text= "Unique Institution code (e.g. TECH2024)", blank=True)
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free Trial'),
            ('small', 'Small (<100 students)'),
            ('medium', 'Medium (100-500 students)'),
            ('large', 'Large (500-1000 students)'),
            ('enterprise', 'Enterprise (1000+ students)'),
        ],
        default='free'
    )
    subscription_active_until = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def is_subscription_active(self):
        """Check if subscription is still active"""
        if not self.subscription_active_until:
            return False
        return self.subscription_active_until >= timezone.now().date()

    def generate_institution_code(self):
        """Generate a unique code like TECH2024 or HOPE2025."""
        prefix = ''.join([c for c in self.name.upper() if c.isalpha()])[:4]
        year = str(datetime.now().year)
        code = f"{prefix}{year}"

        while Institution.objects.filter(institution_code=code).exists():
            suffix = ''.join(random.choices(string.digits, k=2))
            code = f"{prefix}{year}{suffix}"
        return code

    def save(self, *args, **kwargs):
        if not self.institution_code:
            self.institution_code = self.generate_institution_code()
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.institution_id:
            last_institution = Institution.objects.order_by('-id').first()
            next_id = (last_institution.id + 1) if last_institution else 1
            self.institution_id = f"INST{next_id:03d}"  # e.g. INST001, INST002
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

#Class Group

class ClassGroup(models.Model):
    name = models.CharField(max_length=100)
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE,related_name='class_groups')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL ,on_delete=models.SET_NULL,null=True,blank=True,related_name='class_groups')
    students = models.ManyToManyField('StudentProfile',blank=True,related_name='class_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.institution.name})"


# -------------------------
# Custom User Model
# -------------------------
class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
        ('institution_admin', 'Institution Admin'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(default=False, unique=True, max_length=255)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.user_type})"


# -------------------------
# Learning Challenges (ADHD, Dyslexia, Autism, etc.)
# -------------------------
class Challenge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    accommodation_strategy = models.TextField(blank=True, help_text="AI adaptation strategy for this challenge")

    def __str__(self):
        return self.name


# -------------------------
#Institution Admin Profile
# -------------------------
class InstitutionAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    institution = models.ForeignKey('Institution', on_delete=models.CASCADE, related_name='admins')
    contact_phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)  # e.g., "Principal", "Dean", "Director"
    can_manage_teachers = models.BooleanField(default=True)
    can_manage_students = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.institution.name}"
    
    def get_total_students(self):
        """Get count of students in this institution"""
        return StudentProfile.objects.filter(institution=self.institution).count()
    
    def get_total_teachers(self):
        """Get count of teachers in this institution"""
        return TeacherProfile.objects.filter(institution=self.institution).count()
    
    def get_total_materials(self):
        """Get count of study materials uploaded by teachers in this institution"""
        return StudyMaterial.objects.filter(
            uploaded_by__institution=self.institution
        ).count()
    
    def get_active_students(self):
        """Get students who have logged in within last 30 days"""
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return StudentProfile.objects.filter(
            institution=self.institution,
            user__last_login__gte=thirty_days_ago
        ).count()
    
    def get_completion_rate(self):
        """Calculate average completion rate for all students"""
        students = StudentProfile.objects.filter(institution=self.institution)
        if not students.exists():
            return 0
        
        total_completion = 0
        for student in students:
            progress = StudentProgress.objects.filter(student=student)
            if progress.exists():
                avg_completion = progress.aggregate(
                    models.Avg('completion_percentage')
                )['completion_percentage__avg']
                total_completion += avg_completion or 0
        
        return round(total_completion / students.count(), 2) if students.count() > 0 else 0


# -------------------------
# Learning Style
# -------------------------
class LearningStyle(models.Model):
    STYLE_CHOICES = [
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('reading_writing', 'Reading/Writing'),
        ('kinesthetic', 'Kinesthetic'),
    ]

    name = models.CharField(max_length=50, choices=STYLE_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.get_name_display()


# -------------------------
# Student Profile
# -------------------------
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    challenges = models.ManyToManyField(Challenge, blank=True, related_name='students')
    learning_style = models.ForeignKey(LearningStyle, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    bio = models.TextField(blank=True)
    grade_level = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.SET_NULL, null=True, blank=True)
    institution_code= models.CharField(max_length=100, null=False, default='UNKNOWN')
    def __str__(self):
        return f"{self.user.username}'s Profile"


# -------------------------
# Teacher Profile
# -------------------------
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    institution= models.ForeignKey(Institution, on_delete= models.CASCADE, related_name='teachers', null=True, blank=True)
    institution_code= models.CharField(max_length=50)
    subject_specialization = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    students = models.ManyToManyField('StudentProfile', blank=True, related_name='teachers')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically link teacher’s institution from their registration info
        if not self.institution and self.user and self.user.institution:
            self.institution = self.user.institution
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Teacher: {self.user.username}"


# -------------------------
# Study Materials (Uploaded by Teachers)
# -------------------------
class StudyMaterial(models.Model):
    SUBJECT_CHOICES = [
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('history', 'History'),
        ('social_studies', 'Social Studies'),
        ('compuer', 'Computer'),
        ('art', 'Art'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='other')
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="materials/")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_materials')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='materials',null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    institution_code = models.CharField(max_length=50)
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='materials', null=True, blank=True)
    
    # Target audience
    target_challenges = models.ManyToManyField('Challenge', blank=True, related_name='materials')
    target_learning_styles = models.ManyToManyField('LearningStyle', blank=True, related_name='materials')
    grade_level = models.CharField(max_length=50, blank=True)


    def save(self, *args, **kwargs):
        if not self.institution and self.uploaded_by.institution:
            self.institution = self.uploaded_by.institution
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# -------------------------
# Adapted Content (AI-Generated)
# -------------------------
class AdaptedContent(models.Model):
    original_material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='adapted_versions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='adapted_content')
    adapted_text = models.TextField()
    adaptation_notes = models.TextField(blank=True, help_text="Explanation of adaptations made")
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_content',
        null=True,
        blank=True
       
    )
    
    applied_learning_style = models.ForeignKey(LearningStyle, on_delete=models.SET_NULL, null=True, blank=True)
    applied_challenges = models.ManyToManyField(Challenge, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='adapted_content', null=True, blank=True)

    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="D-ID generated video URL")
    video_talk_id = models.CharField(max_length=100, blank=True, null=True, help_text="D-ID talk ID for reference")
    video_generated_at = models.DateTimeField(null=True, blank=True, help_text="When video was generated")
    video_duration = models.FloatField(null=True, blank=True, help_text="Video duration in seconds")
    video_generation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('generating', 'Generating'),
            ('ready', 'Ready'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    video_error_message = models.TextField(blank=True, null=True, help_text="Error if video generation failed")




    def save(self, *args, **kwargs):
        if not self.institution and self.uploaded_by and getattr(self.uploaded_by, "institution", None):
            self.institution = self.uploaded_by.institution
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Adapted: {self.original_material.title} for {self.student.username}"

    @classmethod
    def find_matching_video(cls, material, learning_style, challenges):
        """
        Find existing adapted content with video for same material and preferences
        This allows video sharing across students with same needs
        """
        # Find adapted content for this material with same learning style
        matching_content = cls.objects.filter(
            original_material=material,
            applied_learning_style=learning_style,
            video_url__isnull=False,  # Must have a video
            video_generation_status='ready'  # Video must be ready
        )
        
        # Filter by challenges (students with exact same challenges)
        if challenges:
            challenge_ids = [c.id for c in challenges]
            for content in matching_content:
                content_challenges = set(content.applied_challenges.values_list('id', flat=True))
                if content_challenges == set(challenge_ids):
                    return content
        else:
            # No challenges - find content with no challenges
            for content in matching_content:
                if not content.applied_challenges.exists():
                    return content
        
        return None


# -------------------------
# Progress Tracking
# -------------------------
class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='student_progress')
    completion_percentage = models.IntegerField(default=0)
    time_spent_minutes = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'material']

    def __str__(self):
        return f"{self.student.username} - {self.material.title} ({self.completion_percentage}%)"


# -------------------------
# Quiz/Assessment
# -------------------------
class Assessment(models.Model):
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='assessments') 
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='assessments', null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.institution and self.created_by and self.created_by.institution:
            self.institution = self.created_by.institution
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class AssessmentResult(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_results')
    score = models.FloatField()
    max_score = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.assessment.title}: {self.score}/{self.max_score}"
    

    