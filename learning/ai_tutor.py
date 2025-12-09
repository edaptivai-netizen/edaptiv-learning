"""
AI Tutor Module - Content Adaptation Engine
Adapts study materials based on student's learning style and challenges
"""

import re
from typing import Dict, List
from .models import StudyMaterial, User, AdaptedContent, Challenge, LearningStyle
from django.db.models import Q
from . models import StudentProfile, StudyMaterial
from openai import OpenAI


# -------------------------
# Adaptation Strategies
# -------------------------

def extract_text_from_material(material: StudyMaterial) -> str:
    """
    Extract text content from uploaded material
    For now, assumes text files. Can be extended to handle PDFs, DOCX, etc.
    """
    try:
        with material.file.open('r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def adapt_for_visual_learner(content: str) -> Dict[str, str]:
    """
    Adapt content for visual learners
    - Add visual cues and structure
    - Suggest diagrams and charts
    - Use formatting and highlights
    """
    adapted = content
    
    # Add visual structure markers
    adapted = "📊 VISUAL LEARNING MODE\n\n" + adapted
    
    # Identify key concepts and highlight them
    sentences = adapted.split('.')
    adapted_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Add emoji markers for important concepts
            if any(word in sentence.lower() for word in ['important', 'key', 'main', 'critical']):
                sentence = f"⭐ {sentence}"
            elif any(word in sentence.lower() for word in ['example', 'instance', 'like']):
                sentence = f"💡 {sentence}"
            elif any(word in sentence.lower() for word in ['remember', 'note', 'warning']):
                sentence = f"⚠ {sentence}"
            
            adapted_sentences.append(sentence)
    
    adapted = ". ".join(adapted_sentences)
    
    # Add visual learning tips
    tips = """

📌 VISUAL LEARNING TIPS:
• Create mind maps of the key concepts
• Draw diagrams to represent relationships
• Use color coding for different themes
• Watch related videos or animations
• Create flashcards with images
• Display charts or graphs to visualize data
• Highlight important text with different colors

"""
    
    return {
        'adapted_text': adapted + tips,
        'notes': 'Content adapted with visual cues, emojis, and structured formatting'
    }


def adapt_for_auditory_learner(content: str) -> Dict[str, str]:
    """
    Adapt content for auditory learners
    - Conversational tone
    - Read-aloud friendly
    - Discussion prompts
    """
    adapted = "🎧 AUDITORY LEARNING MODE\n\n" + content
    
    # Make content more conversational
    adapted = adapted.replace("is defined as", "can be understood as")
    adapted = adapted.replace("therefore", "so")
    adapted = adapted.replace("however", "but")
    
    # Add auditory learning tips
    tips = """

🎵 AUDITORY LEARNING TIPS:
• Read this content aloud to yourself
• Record yourself reading and listen back
• Discuss these concepts with a study partner
• Create songs or rhymes to remember key points
• Listen to podcasts on related topics
• Explain the concepts to someone else
"""
    
    return {
        'adapted_text': adapted + tips,
        'notes': 'Content adapted with conversational tone and auditory learning strategies'
    }


def adapt_for_kinesthetic_learner(content: str) -> Dict[str, str]:
    """
    Adapt content for kinesthetic/hands-on learners
    - Action-oriented language
    - Practical exercises
    - Physical activities
    """
    adapted = "✋ KINESTHETIC LEARNING MODE\n\n" + content
    
    # Add action words
    sections = adapted.split('\n\n')
    adapted_sections = []
    
    for section in sections:
        if section.strip():
            # Add activity suggestions
            adapted_sections.append(section)
            adapted_sections.append("🏃 Try this: Act out or demonstrate this concept physically")
    
    adapted = '\n\n'.join(adapted_sections)
    
    # Add kinesthetic learning tips
    tips = """

🎯 KINESTHETIC LEARNING TIPS:
• Take frequent breaks to move around
• Use physical objects to represent concepts
• Act out processes or events
• Build models or create hands-on projects
• Walk while reviewing material
• Use gestures when explaining concepts
• Practice with real-world applications
"""
    
    return {
        'adapted_text': adapted + tips,
        'notes': 'Content adapted with action-oriented language and hands-on activities'
    }


def adapt_for_reading_writing_learner(content: str) -> Dict[str, str]:
    """
    Adapt content for reading/writing learners
    - Well-structured text
    - Note-taking prompts
    - Writing exercises
    """
    adapted = "📝 READING/WRITING LEARNING MODE\n\n" + content
    
    # Add structured sections
    sections = adapted.split('\n\n')
    numbered_sections = []
    
    for i, section in enumerate(sections, 1):
        if section.strip():
            numbered_sections.append(f"{i}. {section}")
    
    adapted = '\n\n'.join(numbered_sections)
    
    # Add reading/writing tips
    tips = """

📚 READING/WRITING LEARNING TIPS:
• Take detailed notes in your own words
• Create written summaries after each section
• Make lists and outlines of key concepts
• Write practice questions and answers
• Keep a learning journal
• Rewrite concepts in different formats
• Create glossaries of important terms
"""
    
    return {
        'adapted_text': adapted + tips,
        'notes': 'Content adapted with structured text and writing prompts'
    }


# -------------------------
# Challenge-Specific Adaptations
# -------------------------

def adapt_for_dyslexia(content: str) -> str:
    """
    Adapt content for learners with dyslexia
    - Shorter sentences
    - Simpler vocabulary
    - More spacing
    """
    # Break long sentences
    sentences = content.split('.')
    adapted_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 100:  # Break long sentences
            # Find natural break points
            if ',' in sentence:
                parts = sentence.split(',')
                adapted_sentences.extend([p.strip() + '.' for p in parts if p.strip()])
            else:
                adapted_sentences.append(sentence + '.')
        elif sentence:
            adapted_sentences.append(sentence + '.')
    
    adapted = '\n\n'.join(adapted_sentences)  # More spacing
    
    # Add dyslexia-friendly notes
    note = """

♿ DYSLEXIA ACCOMMODATIONS:
• Text formatted with extra spacing for easier reading
• Sentences broken into shorter chunks
• Use a reading ruler or finger to track lines
• Adjust font size if needed
• Take your time - there's no rush
"""
    
    return adapted + note


def adapt_for_adhd(content: str) -> str:
    """
    Adapt content for learners with ADHD
    - Chunked information
    - Frequent breaks
    - Clear highlights
    """
    # Break into small chunks
    paragraphs = content.split('\n\n')
    chunked = []
    
    for i, para in enumerate(paragraphs, 1):
        if para.strip():
            chunked.append(f"📦 CHUNK {i}:\n{para}")
            if i % 2 == 0:  # Suggest breaks
                chunked.append("\n⏸ Take a 2-minute break here!\n")
    
    adapted = '\n\n'.join(chunked)
    
    # Add ADHD-friendly notes
    note = """

♿ ADHD ACCOMMODATIONS:
• Content broken into manageable chunks
• Take breaks between sections
• Use a timer (Pomodoro technique: 25 min work, 5 min break)
• Eliminate distractions in your environment
• Move around during breaks
• Use fidget tools if helpful
"""
    
    return adapted + note


def adapt_for_autism(content: str) -> str:
    """
    Adapt content for learners with autism
    - Clear structure
    - Literal language
    - Predictable format
    """
    # Add clear structure
    adapted = "📋 CLEAR STRUCTURE\n\n" + content
    
    # Make language more literal and concrete
    adapted = adapted.replace("for example", "here is an example")
    adapted = adapted.replace("in other words", "this means")
    
    # Add autism-friendly notes
    note = """

♿ AUTISM ACCOMMODATIONS:
• Content structured with clear sections
• Language is direct and literal
• Predictable format throughout
• Take breaks in a quiet space if needed
• Use noise-canceling headphones if helpful
• Follow your own pace - no social pressure
"""
    
    return adapted + note


# -------------------------
# Main Adaptation Function
# -------------------------

def adapt_content_for_student(material: StudyMaterial, user: User) -> AdaptedContent:
    """Generate adapted content using Kimi K2"""
    
    try:
        profile = user.student_profile
    except:
        return None
    
    # Extract original content
    original_text = extract_text_from_material(material)
    
    # Get student details
    learning_style = profile.learning_style.name if profile.learning_style else 'visual'
    challenges = [c.name for c in profile.challenges.all()]
    
    # Generate script with Kimi
    from utils.kimi_integration import KimiAdapter
    
    kimi = KimiAdapter()
    result = kimi.generate_script(
        original_content=original_text,
        learning_style=learning_style,
        challenges=challenges,
        student_name=user.first_name,
        subject=material.subject
    )
    
    if result['success']:
        adapted_text = result['teaching_script']
        adaptation_notes = f"Generated with Kimi K2 for {learning_style} learner"
    else:
        # Fallback to basic adaptation
        adapted_text = f"Hi {user.first_name}! Let me teach you about {material.title}. {original_text[:500]}"
        adaptation_notes = "Used fallback script"
    
    # Create or update adapted content
    adapted_content, created = AdaptedContent.objects.update_or_create(
        original_material=material,
        student=user,
        defaults={
            'adapted_text': adapted_text,
            'adaptation_notes': adaptation_notes,
            'applied_learning_style': profile.learning_style,
        }
    )
    
    # Add challenges
    if profile.challenges.exists():
        adapted_content.applied_challenges.set(profile.challenges.all())
    
    return adapted_content


# ################# THE VIDEO GENERATION #####################
# """
# we shall collect the following
# 1 studentdetails
#      1 learning style
#      2 challenges
# 2 get the study material
# 3 aggreagte the student details and teh teaching material
# 4 generate the video using the aggregated data


# for this, we need to access the student model and collect student.lrearning_style 
# and student.challenges
# to get the learning material from study_material.adapted_content 
# the join them as the aggreagtae data and pass to deepsek to create the adapted laerning materioal for the 
# specific student
# we then pass the adapted material created by deeepsek to the video generation module 
# to create the video

# we shall prompt deepseeek to generate the timed stamped script for the video generation and pick the
#  script for video generation of two minutes each in a loop and generate the video accordingly.

# we shal then show the first two minutes to the student as we generate the next two minutes of teh video 


# """
# ###def collect_student_details(user: User) -> Dict:
#     """
#     Collect student details including learning style and challenges
#     """
#     try:
#         profile = user.student_profile
#     except:
#         return {}
    
#     learning_style = profile.learning_style.name if profile.learning_style else None
#     challenges = [challenge.name for challenge in profile.challenges.all()]
    
#     return {
#         'learning_style': learning_style,
#         'challenges': challenges
#     }
# def get_study_material(material: StudyMaterial) -> str:
#     """
#     Get the study material content
#     get the study material from the model StudyMaterial.adapted_content
#     """
#     return extract_text_from_material(StudyMaterial.adapted_content)

# def aggregate_data(user: User, material: StudyMaterial) -> Dict:    
#     """
#     Aggregate student details and study material
#     """
#     student_details = collect_student_details(user)
#     study_material = get_study_material(material)
    
#     return {
#         'student_details': student_details,
#         'study_material': study_material
#     }

# def generate_video_script(aggregated_data: Dict) -> str:    
#     """
#     Generate a timed script for video generation using DeepSeek
#     """
#     # Placeholder for DeepSeek API call
#     # In real implementation, this would involve sending aggregated_data to DeepSeek and receiving the script
#     script = f"Video Script based on {aggregated_data['student_details']} and material: {aggregated_data['study_material'][:100]}..."
#     return script

# def generate_learning_video(user: User, material: StudyMaterial) -> str:    
#     """
#     Main function to generate learning video for the student
#     """
#     aggregated_data = aggregate_data(user, material)
#     video_script = generate_video_script(aggregated_data)
    
#     # Placeholder for video generation logic
#     # In real implementation, this would involve using the script to create a video file
#     video_file_path = f"/path/to/generated/video_for_{user.id}.mp4"
    
#     return video_file_path

# def deepseek_generate_script(aggregated_data: Dict) -> str:
#     #kimi k2 model from openrouter
#     api_key = "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"
    

#     client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key="<OPENROUTER_API_KEY>",
#     )

#     completion = client.chat.completions.create(
#     extra_headers={
#         "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
#         "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
#     },
#     extra_body={},
#     model="moonshotai/kimi-k2:free",
#     messages=[
#                 {
#                     "role": "user",
#                     "content": script = f"Generated Script based on {aggregated_data['student_details']} and material: {aggregated_data['study_material'][:100]}..."
#                 }
#                 ]
#     )
#     return completion.choices[0].message.content
# # we now generate the learning video using the deepseek generated script as prompt to the DID API
# # the DID 
    