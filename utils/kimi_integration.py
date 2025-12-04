# utils/kimi_integration.py
"""
Kimi K2 Integration via OpenRouter
Generates teaching scripts for primary school students
"""

import os
import requests
from typing import Dict, List


class KimiAdapter:
    """Kimi K2 API Integration via OpenRouter"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.site_url = os.environ.get('SITE_URL', 'https://edaptiv.com')
        self.site_name = "EDAPTIV"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    def get_headers(self):
        """Return headers for OpenRouter API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name
        }
    
    def create_teaching_prompt(
        self,
        original_content: str,
        learning_style: str,
        challenges: List[str],
        student_name: str,
        subject: str
    ) -> str:
        """Create a prompt for Kimi to generate teaching script"""
        
        # Build learning style description
        style_instructions = {
            'visual': 'Use visual descriptions: "Imagine...", "Picture this...", "Think of..."',
            'auditory': 'Use sound words and verbal cues. Encourage saying things out loud.',
            'kinesthetic': 'Include actions: "Try this...", "Let\'s move...", "Use your hands..."',
            'reading_writing': 'Encourage taking notes and writing things down.'
        }
        
        style_text = style_instructions.get(learning_style, 'Use clear explanations')
        
        # Build challenges accommodations
        challenge_instructions = {
            'dyslexia': 'Use VERY short sentences (10 words or less). Avoid complex words.',
            'adhd': 'Break into tiny chunks. Use attention-grabbing words. Include energy.',
            'autism': 'Be literal and concrete. Use predictable structure. Be very clear.'
        }
        
        challenges_text = " ".join([
            challenge_instructions.get(c.lower(), '') 
            for c in challenges if c.lower() in challenge_instructions
        ])
        
        prompt = f"""You are a warm, friendly primary school teacher creating a video lesson for {student_name}, a {learning_style} learner.

STUDENT INFO:
- Name: {student_name}
- Age: 6-12 years (primary school)
- Learning Style: {learning_style}
- Special Needs: {challenges_text if challenges_text else 'None'}
- Subject: {subject}

ORIGINAL CONTENT TO TEACH:
{original_content[:1500]}

YOUR TASK:
Create a 2-3 minute teaching script that a video avatar will speak to {student_name}.

REQUIREMENTS:
1. Start with warm greeting: "Hi {student_name}! I'm excited to teach you about..."
2. Use SIMPLE words (primary school level)
3. Keep sentences SHORT (under 15 words each)
4. Be conversational - use "you", "we", "let's"
5. {style_text}
6. {challenges_text if challenges_text else 'Use clear language'}
7. Include encouragement: "You're doing great!", "Awesome!"
8. End with summary and positive note
9. Total length: 300-500 words maximum

IMPORTANT:
- Write ONLY what the teacher will say
- NO stage directions, NO notes, NO explanations
- Just the natural speaking script
- Use "..." for natural pauses
- Make it sound like a real teacher talking to a child

Generate the teaching script now:"""

        return prompt
    
    def generate_script(
        self,
        original_content: str,
        learning_style: str,
        challenges: List[str],
        student_name: str,
        subject: str
    ) -> Dict:
        """
        Call Kimi K2 API to generate teaching script
        
        Returns:
            Dictionary with:
            - success: bool
            - teaching_script: str
            - error: str (if failed)
        """
        
        try:
            # Create the prompt
            prompt = self.create_teaching_prompt(
                original_content=original_content,
                learning_style=learning_style,
                challenges=challenges,
                student_name=student_name,
                subject=subject
            )
            
            print(f"🤖 Calling Kimi K2 to generate script...")
            
            # Call OpenRouter API with Kimi K2
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.get_headers(),
                json={
                    "model": "moonshotai/kimi-k2:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
            )
            
            print(f"📡 API Response: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.json()
                print(f"❌ API Error: {error_detail}")
                raise Exception(f"Kimi API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            # Extract the teaching script
            teaching_script = result['choices'][0]['message']['content'].strip()
            
            # Clean up formatting
            teaching_script = teaching_script.replace("**", "")
            teaching_script = teaching_script.replace("##", "")
            teaching_script = teaching_script.replace("```", "")
            
            print(f"✅ Script generated! Length: {len(teaching_script)} chars")
            print(f"Preview: {teaching_script[:100]}...")
            
            return {
                'success': True,
                'teaching_script': teaching_script,
                'tokens_used': result.get('usage', {}).get('total_tokens', 0)
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Kimi API error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'teaching_script': ''
            }
        except Exception as e:
            error_msg = f"Script generation error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'teaching_script': ''
            }


def test_kimi_connection():
    """Test Kimi API connection via OpenRouter"""
    try:
        adapter = KimiAdapter()
        print("🧪 Testing Kimi K2 connection...")
        
        response = requests.post(
            f"{adapter.base_url}/chat/completions",
            headers=adapter.get_headers(),
            json={
                "model": "moonshotai/kimi-k2:free",
                "messages": [
                    {"role": "user", "content": "Say hello in one word"}
                ],
                "max_tokens": 10
            }
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Kimi connection successful!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False