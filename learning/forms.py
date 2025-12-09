forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, TeacherProfile, StudyMaterial, Challenge, LearningStyle


# -------------------------
# Student Registration Form
# -------------------------
class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    grade_level = forms.CharField(max_length=50, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    # Define fields with empty querysets initially
    challenges = forms.ModelMultipleChoiceField(
        queryset=Challenge.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select any learning challenges you have"
    )
    learning_style = forms.ModelChoiceField(
        queryset=LearningStyle.objects.none(),
        required=True,
        help_text="Select your preferred learning style"
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        """
        Dynamically populate querysets each time form is loaded.
        This prevents empty or outdated dropdowns and ensures
        all Challenge and LearningStyle records appear.
        """
        super().__init__(*args, **kwargs)
        self.fields['challenges'].queryset = Challenge.objects.all().order_by('name')
        self.fields['learning_style'].queryset = LearningStyle.objects.all().order_by('name')

        # Optional: nicer checkbox labels and styling
        self.fields['challenges'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['learning_style'].widget.attrs.update({'class': 'form-select'})

    def save(self, commit=True):
        """
        Save the user and create an associated StudentProfile.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 'student'
        user.is_student = False

        if commit:
            user.save()
            # Create student profile
            profile = StudentProfile.objects.create(
                user=user,
                learning_style=self.cleaned_data.get('learning_style'),
                grade_level=self.cleaned_data.get('grade_level', ''),
                bio=self.cleaned_data.get('bio', '')
            )
            # Assign selected challenges
            if self.cleaned_data.get('challenges'):
                profile.challenges.set(self.cleaned_data['challenges'])
        return user
# -------------------------
# Teacher Registration Form
# -------------------------
class TeacherRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    subject_specialization = forms.CharField(max_length=200, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 'teacher'
        user.is_student = False
        
        if commit:
            user.save()
            
            # Create teacher profile
            TeacherProfile.objects.create(
                user=user,
                subject_specialization=self.cleaned_data.get('subject_specialization', ''),
                bio=self.cleaned_data.get('bio', '')
            )
            
        return user


# -------------------------
# Study Material Upload Form
# -------------------------
class StudyMaterialForm(forms.ModelForm):
    target_challenges = forms.ModelMultipleChoiceField(
        queryset=Challenge.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select challenges this material addresses"
    )
    target_learning_styles = forms.ModelMultipleChoiceField(
        queryset=LearningStyle.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select learning styles this material supports"
    )

    class Meta:
        model = StudyMaterial
        fields = [
            'title', 'subject', 'description', 'file', 
            'target_challenges', 'target_learning_styles', 'grade_level', 'class_group'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


# -------------------------
# Student Profile Update Form
# -------------------------
class StudentProfileUpdateForm(forms.ModelForm):
    challenges = forms.ModelMultipleChoiceField(
        queryset=Challenge.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = StudentProfile
        fields = ['challenges', 'learning_style', 'grade_level', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }