from rest_framework import serializers
from .models import (
    User, Challenge, LearningStyle, StudentProfile, TeacherProfile,
    StudyMaterial, AdaptedContent, StudentProgress, Assessment, AssessmentResult
)


# -------------------------
# User Serializers
# -------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'is_student']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'user_type']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


# -------------------------
# Challenge & Learning Style Serializers
# -------------------------
class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['id', 'name', 'description', 'accommodation_strategy']


class LearningStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningStyle
        fields = ['id', 'name', 'description']


# -------------------------
# Student Profile Serializers
# -------------------------
class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    challenges = ChallengeSerializer(many=True, read_only=True)
    learning_style = LearningStyleSerializer(read_only=True)
    challenge_ids = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Challenge.objects.all(), 
        source='challenges', 
        write_only=True
    )
    learning_style_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningStyle.objects.all(), 
        source='learning_style', 
        write_only=True,
        required=False
    )

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'challenges', 'learning_style', 'bio', 'grade_level',
            'challenge_ids', 'learning_style_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# -------------------------
# Teacher Profile Serializers
# -------------------------
class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'subject_specialization', 'bio', 'created_at']
        read_only_fields = ['id', 'created_at']


# -------------------------
# Study Material Serializers
# -------------------------
class StudyMaterialSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    target_challenges = ChallengeSerializer(many=True, read_only=True)
    target_learning_styles = LearningStyleSerializer(many=True, read_only=True)
    
    challenge_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Challenge.objects.all(),
        source='target_challenges',
        write_only=True,
        required=False
    )
    learning_style_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=LearningStyle.objects.all(),
        source='target_learning_styles',
        write_only=True,
        required=False
    )

    class Meta:
        model = StudyMaterial
        fields = [
            'id', 'title', 'subject', 'description', 'file', 'uploaded_by',
            'uploaded_at', 'target_challenges', 'target_learning_styles',
            'grade_level', 'challenge_ids', 'learning_style_ids'
        ]
        read_only_fields = ['id', 'uploaded_at']


# -------------------------
# Adapted Content Serializers
# -------------------------
class AdaptedContentSerializer(serializers.ModelSerializer):
    original_material = StudyMaterialSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    applied_learning_style = LearningStyleSerializer(read_only=True)
    applied_challenges = ChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = AdaptedContent
        fields = [
            'id', 'original_material', 'student', 'adapted_text',
            'adaptation_notes', 'created_at', 'applied_learning_style',
            'applied_challenges'
        ]
        read_only_fields = ['id', 'created_at']


# -------------------------
# Progress Tracking Serializers
# -------------------------
class StudentProgressSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    material = StudyMaterialSerializer(read_only=True)

    class Meta:
        model = StudentProgress
        fields = [
            'id', 'student', 'material', 'completion_percentage',
            'time_spent_minutes', 'last_accessed', 'notes'
        ]
        read_only_fields = ['id', 'last_accessed']


# -------------------------
# Assessment Serializers
# -------------------------
class AssessmentSerializer(serializers.ModelSerializer):
    material = StudyMaterialSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'material', 'title', 'description', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_at']


class AssessmentResultSerializer(serializers.ModelSerializer):
    assessment = AssessmentSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentResult
        fields = [
            'id', 'assessment', 'student', 'score', 'max_score',
            'percentage', 'completed_at', 'feedback'
        ]
        read_only_fields = ['id', 'completed_at']

    def get_percentage(self, obj):
        if obj.max_score > 0:
            return round((obj.score / obj.max_score) * 100, 2)
        return 0