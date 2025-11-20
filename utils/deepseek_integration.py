# utils/deepseek_integration.py
"""
DeepSeek R1 Integration for EDAPTIV
Simplifies and adapts content for primary school students based on learning preferences
"""

import os
import requests
import json
from typing import Dict, List
from learning.ai_tutor

class DeepSeekAdapter:
    """
    DeepSeek R1 API Integration
    Adapts content for different learning styles and challenges
    """
    
    def __init__(self):
        self.api_key = os.environ.get('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1"
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
    
    def get_headers(self):
        """Return headers for DeepSeek API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_adaptation_prompt(
        self,
        original_content: str,
        learning_styles: List[str],
        challenges: List[str],
        student_name: str,
        subject: str
    ) -> str:
        """
        Create a comprehensive prompt for DeepSeek R1 to adapt content
        
        Args:
            original_content: The original study material text
            learning_styles: List of learning style names (e.g., ['visual', 'auditory'])
            challenges: List of challenges (e.g., ['dyslexia', 'adhd'])
            student_name: Student's first name for personalization
            subject: Subject area (mathematics, science, english, etc.)
        
        Returns:
            Formatted prompt string for DeepSeek
        """
        
        # Build learning style description
        style_descriptions = {
            'visual': 'Visual learner - prefers pictures, diagrams, colors, and visual cues',
            'auditory': 'Auditory learner - learns best through listening and verbal explanations',
            'reading_writing': 'Reading/Writing learner - prefers text, notes, and written materials',
            'kinesthetic': 'Kinesthetic learner - learns through hands-on activities and movement'
        }
        
        styles_text = ", ".join([style_descriptions.get(s.lower(), s) for s in learning_styles])
        
        # Build challenges description
        challenge_descriptions = {
            'dyslexia': 'has dyslexia (needs shorter sentences, simpler words, more spacing)',
            'adhd': 'has ADHD (needs chunked information, frequent breaks, clear highlights)',
            'autism': 'is on the autism spectrum (needs clear structure, literal language, predictable format)',
            
        }
        
        challenges_text = ", and ".join([challenge_descriptions.get(c.lower(), c) for c in challenges]) if challenges else "no specific learning challenges"
        
        prompt = f"""You are an expert primary school teacher adapting educational content for a student named {student_name}.

STUDENT PROFILE:
- Grade Level: Primary School (ages 6-12)
- Learning Style: {styles_text}
- Challenges: {challenges_text}
- Subject: {subject}

ORIGINAL CONTENT:
{original_content}

TASK:
Adapt this content into a warm, friendly teaching script that a video avatar teacher will speak directly to {student_name}. 

REQUIREMENTS:
1. **Primary School Level**: Use simple, age-appropriate language for 6-12 year olds
2. **Conversational**: Write like you're speaking directly to the student (use "you", "we", "let's")
3. **Engaging**: Make it fun, enthusiastic, and encouraging
4. **Length**: Keep the script to 300-500 words (2-3 minutes of speaking time)
5. **Structure**: Break into short, clear sections with natural pauses

LEARNING STYLE ADAPTATIONS:
{self._get_style_instructions(learning_styles)}

CHALLENGE ACCOMMODATIONS:
{self._get_challenge_instructions(challenges)}

SCRIPT FORMAT:
- Start with a warm greeting: "Hi {student_name}! I'm so excited to teach you about..."
- Break complex ideas into simple steps
- Use examples the student can relate to
- Include encouragement: "You're doing great!", "Let me show you..."
- End with a summary and positive note

IMPORTANT:
- Keep sentences SHORT (under 15 words)
- Use SIMPLE vocabulary (primary school level)
- NO technical jargon
- Include natural pauses with "..." 
- Make it sound like a friendly teacher talking, not reading

Generate ONLY the teaching script that will be spoken by the video avatar. Give explanations or notes."""

        return prompt
    
    def _get_style_instructions(self, learning_styles: List[str]) -> str:
        """Generate specific instructions based on learning styles"""
        instructions = []
        
        if 'visual' in [s.lower() for s in learning_styles]:
            instructions.append("- Describe things VISUALLY: 'Imagine a...', 'Picture this...', 'Think of it like...'")
            instructions.append("- Use color words and visual descriptions")
            instructions.append("- Suggest drawing or looking at pictures")
        
        if 'auditory' in [s.lower() for s in learning_styles]:
            instructions.append("- Use sound words and verbal cues")
            instructions.append("- Encourage saying things out loud")
            instructions.append("- Use rhythm and repetition")
        
        if 'kinesthetic' in [s.lower() for s in learning_styles]:
            instructions.append("- Include actions: 'Try this...', 'Let's move...', 'Use your fingers...'")
            instructions.append("- Suggest hands-on activities")
            instructions.append("- Use movement and gestures in explanations")
        
        if 'reading_writing' in [s.lower() for s in learning_styles]:
            instructions.append("- Encourage taking notes")
            instructions.append("- Suggest writing things down")
            instructions.append("- Use lists and structured information")
        
        return "\n".join(instructions) if instructions else "- Use clear, straightforward explanations"
    
    def _get_challenge_instructions(self, challenges: List[str]) -> str:
        """Generate specific instructions based on challenges"""
        instructions = []
        
        if any('dyslexia' in c.lower() for c in challenges):
            instructions.append("- Use VERY short sentences (10 words or less)")
            instructions.append("- Avoid complex words - use simple alternatives")
            instructions.append("- Repeat key concepts in different ways")
            instructions.append("- Add LOTS of pauses between ideas")
        
        if any('adhd' in c.lower() for c in challenges):
            instructions.append("- Break information into TINY chunks")
            instructions.append("- Include energy and enthusiasm")
            instructions.append("- Suggest quick movements or breaks")
            instructions.append("- Use attention-grabbing words: 'Hey!', 'Look!', 'Guess what!'")
        
        if any('autism' in c.lower() for c in challenges):
            instructions.append("- Be VERY literal and concrete (no idioms or abstract language)")
            instructions.append("- Use predictable structure")
            instructions.append("- Be clear and direct")
            instructions.append("- Explain things step-by-step in order")
        
        return "\n".join(instructions) if instructions else "- Use clear, accessible language"
    
    def adapt_content(
        self,
        original_content: str,
        learning_styles: List[str],
        challenges: List[str],
        student_name: str,
        subject: str
    ) -> Dict:
        """
        Call DeepSeek R1 API to adapt content
        
        Returns:
            Dictionary with:
            - success: bool
            - teaching_script: str (the script for D-ID video)
            - adapted_text: str (same as teaching_script for now)
            - error: str (if failed)
        """
        
        try:
            # Create the prompt
            prompt = self.create_adaptation_prompt(
                original_content=original_content,
                learning_styles=learning_styles,
                challenges=challenges,
                student_name=student_name,
                subject=subject
            )
            
            # Call DeepSeek API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.get_headers(),
                json={
                    "model": "deepseek-reasoner",  # DeepSeek R1
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7,  # Balance between creativity and consistency
                    "stream": False
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the teaching script
            teaching_script = result['choices'][0]['message']['content'].strip()
            
            # Clean up any extra formatting
            teaching_script = teaching_script.replace("**", "")  # Remove markdown bold
            teaching_script = teaching_script.replace("##", "")  # Remove headers
            
            return {
                'success': True,
                'teaching_script': teaching_script,
                'adapted_text': teaching_script,  # Same content for both
                'tokens_used': result.get('usage', {}).get('total_tokens', 0),
                'cost_estimate': result.get('usage', {}).get('total_tokens', 0) * 0.000001  # Rough estimate
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"DeepSeek API error: {str(e)}",
                'teaching_script': '',
                'adapted_text': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Adaptation error: {str(e)}",
                'teaching_script': '',
                'adapted_text': ''
            }


def adapt_content_for_student(material, learning_styles, challenges, student):
    """
    Main function to adapt content using DeepSeek R1
    This replaces your existing ai_tutor.py logic with AI-powered adaptation
    
    Args:
        material: StudyMaterial object
        learning_styles: QuerySet of LearningStyle objects
        challenges: QuerySet of Challenge objects
        student: StudentProfile object
    
    Returns:
        Dictionary with adaptation results
    """
    
    try:
        # Extract text from material
        from learning.ai_tutor import extract_text_from_material
        original_content = extract_text_from_material(material)
        
        # Get learning style names
        style_names = [style.name for style in learning_styles]
        
        # Get challenge names
        challenge_names = [challenge.name for challenge in challenges]
        
        # Initialize DeepSeek adapter
        adapter = DeepSeekAdapter()
        
        # Adapt the content
        result = adapter.adapt_content(
            original_content=original_content,
            learning_styles=style_names,
            challenges=challenge_names,
            student_name=student.user.first_name,
            subject=material.subject
        )
        
        if result['success']:
            print(f"✅ Content adapted successfully!")
            print(f"📊 Tokens used: {result['tokens_used']}")
           
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'teaching_script': '',
            'adapted_text': ''
        }


def test_deepseek_connection():
    """
    Test DeepSeek API connection
    
    Returns:
        Boolean indicating if connection is successful
    """
    try:
        adapter = DeepSeekAdapter()
        
        # Simple test request
        response = requests.post(
            f"{adapter.base_url}/chat/completions",
            headers=adapter.get_headers(),
            json={
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "user", "content": "Say 'Hello' in one word"}
                ],
                "max_tokens": 10
            }
        )
        
        if response.status_code == 200:
            print("✅ DeepSeek API connection successful!")
            return True
        else:
            print(f"❌ DeepSeek API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False