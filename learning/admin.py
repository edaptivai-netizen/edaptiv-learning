from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from learning.models import (
    User, Challenge, LearningStyle, StudentProfile, TeacherProfile,
    StudyMaterial, AdaptedContent, StudentProgress, Assessment, AssessmentResult
)



# -------------------------
# Custom User Admin
# -------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_staff', 'is_active']
    list_filter = ['user_type', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('EDAPTIV Custom Fields', {
            'fields': ('user_type',)
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('EDAPTIV Custom Fields', {
            'fields': ('user_type',)
        }),
    )


# -------------------------
# Challenge Admin
# -------------------------
@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']


# -------------------------
# Learning Style Admin
# -------------------------
@admin.register(LearningStyle)
class LearningStyleAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'description']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Learning Style'


# -------------------------
# Student Profile Admin
# -------------------------
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_style', 'grade_level', 'created_at']
    list_filter = ['learning_style', 'grade_level', 'created_at']
    search_fields = ['user_username', 'useremail', 'userfirst_name', 'user_last_name']
    filter_horizontal = ['challenges']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Learning Profile', {
            'fields': ('learning_style', 'challenges', 'grade_level')
        }),
        ('Additional Information', {
            'fields': ('bio',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


# -------------------------
# Teacher Profile Admin
# -------------------------
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject_specialization', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user_username', 'user_email', 'subject_specialization']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('subject_specialization', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


# -------------------------
# Study Material Admin
# -------------------------
@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'uploaded_by', 'grade_level', 'uploaded_at']
    list_filter = ['subject', 'uploaded_at', 'grade_level']
    search_fields = ['title', 'description', 'uploaded_by__username']
    filter_horizontal = ['target_challenges', 'target_learning_styles']
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subject', 'description', 'file', 'uploaded_by')
        }),
        ('Target Audience', {
            'fields': ('grade_level', 'target_learning_styles', 'target_challenges')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['uploaded_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# -------------------------
# Adapted Content Admin
# -------------------------
@admin.register(AdaptedContent)
class AdaptedContentAdmin(admin.ModelAdmin):
    list_display = ['original_material', 'student', 'applied_learning_style', 'created_at']
    list_filter = ['applied_learning_style', 'created_at']
    search_fields = ['student_username', 'original_material_title']
    filter_horizontal = ['applied_challenges']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Source Information', {
            'fields': ('original_material', 'student')
        }),
        ('Adaptation Details', {
            'fields': ('applied_learning_style', 'applied_challenges', 'adaptation_notes')
        }),
        ('Adapted Content', {
            'fields': ('adapted_text',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


# -------------------------
# Student Progress Admin
# -------------------------
@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'material', 'completion_percentage', 'time_spent_minutes', 'last_accessed']
    list_filter = ['completion_percentage', 'last_accessed']
    search_fields = ['student_username', 'material_title']
    ordering = ['-last_accessed']
    
    fieldsets = (
        ('Student & Material', {
            'fields': ('student', 'material')
        }),
        ('Progress Details', {
            'fields': ('completion_percentage', 'time_spent_minutes', 'notes')
        }),
        ('Timestamps', {
            'fields': ('last_accessed',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_accessed']


# -------------------------
# Assessment Admin
# -------------------------
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'material', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'material_title', 'created_by_username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'material', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


# -------------------------
# Assessment Result Admin
# -------------------------
@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'score', 'max_score', 'get_percentage', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['student_username', 'assessment_title']
    ordering = ['-completed_at']
    
    fieldsets = (
        ('Assessment Information', {
            'fields': ('assessment', 'student')
        }),
        ('Results', {
            'fields': ('score', 'max_score', 'feedback')
        }),
        ('Timestamps', {
            'fields': ('completed_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['completed_at']
    
    def get_percentage(self, obj):
        if obj.max_score > 0:
            return f"{(obj.score / obj.max_score) * 100:.1f}%"
        return "0%"
    get_percentage.short_description = 'Percentage'


# -------------------------
# Customize Admin Site
# -------------------------
admin.site.site_header = "EDAPTIV Admin Portal"
admin.site.site_title = "EDAPTIV Admin"
admin.site.index_title = "Welcome to EDAPTIV Administration"