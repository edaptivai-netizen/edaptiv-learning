# utils/ai_integration.py - COMPLETE FIX
"""
D-ID Video Avatar Integration for EDAPTIV
"""

import os
import time
import requests
from typing import Dict, Optional


class DIDVideoGenerator:
    """D-ID API Integration for generating avatar videos"""
    
    def __init__(self):
        self.api_key = os.environ.get('DID_API_KEY')
        self.base_url = "https://api.d-id.com"
        
        if not self.api_key:
            raise ValueError("D-ID API key not found in environment variables")
    
    def get_headers(self):
        """Return headers for D-ID API requests"""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Basic {self.api_key}"
        }
    
    def get_avatar_url(self, subject: str) -> str:
        """
        Get avatar URL - UPLOAD YOUR IMAGE TO AWS FIRST!
        
       
        """
        
        # 🎨  YOUR IMGAGE URL!
        YOUR_URL = 'https://edaptiv-user-avatars.s3.eu-north-1.amazonaws.com/female_tr.png'
        
        # Ensure URL ends with proper extension for D-ID
        if not (YOUR_URL.endswith('.jpg') or 
                YOUR_URL.endswith('.jpeg') or 
                YOUR_URL.endswith('.png')):
            print("⚠️ Warning: URL doesn't have image extension")
            # Try adding .jpg
            YOUR_URL = YOUR_URL.split('?')[0] + '.jpg'
        
        print(f"📸 Using avatar: {YOUR_URL}")
        return YOUR_URL
    
    def get_voice_id(self, subject: str = None) -> str:
        """Get Microsoft voice - en-US-NancyNeural"""
        return 'en-US-NancyNeural'
    
    def create_video(
        self, 
        script: str,
        subject: str,
        student_name: str = "friend"
    ) -> Dict:
        """Create a talking avatar video"""
        
        # Validate script
        if not script or len(script.strip()) < 3:
            return {
                'success': False,
                'error': 'Script is too short or empty',
                'video_url': None,
                'talk_id': None
            }
        
        script = script.strip()
        
        # Get avatar and voice
        avatar_url = self.get_avatar_url(subject)
        voice_id = self.get_voice_id(subject)
        
        # Limit script length
        if len(script) > 3000:
            print(f"⚠️ Script too long ({len(script)} chars), truncating to 3000")
            script = script[:2997] + "..."
        
        # Prepare D-ID API request - FIXED FORMAT
        payload = {
            "source_url": avatar_url,
            "script": {
                "type": "text",
                "input": script,
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id
                }
            },
            "config": {
                "stitch": True,
                "fluent": True,
                "pad_audio": 0.0
            }
        }
        
        print(f"🎬 Creating video for {student_name}...")
        print(f"📚 Subject: {subject}")
        print(f"🎙️ Voice: {voice_id}")
        print(f"👤 Avatar: {avatar_url[:50]}...")
        print(f"📝 Script: {len(script)} chars")
        
        try:
            # FIXED: Correct endpoint (no talk_id in POST)
            response = requests.post(
                f"{self.base_url}/talks",  # ⬅️ THIS WAS THE BUG!
                json=payload,
                headers=self.get_headers()
            )
            
            print(f"📡 API Response: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_detail = response.json()
                print(f"❌ API Error: {error_detail}")
                return {
                    'success': False,
                    'error': f"D-ID API error: {response.status_code} - {error_detail}",
                    'video_url': None,
                    'talk_id': None
                }
            
            result = response.json()
            talk_id = result.get('id')
            
            if not talk_id:
                raise Exception("No talk ID received from D-ID")
            
            print(f"✅ Video job created! ID: {talk_id}")
            print(f"⏳ Generating video (60-120 seconds)...")
            
            # Wait for video to be ready
            video_url = self.wait_for_video(talk_id)
            
            if video_url:
                print(f"🎉 Video ready!")
                return {
                    'success': True,
                    'video_url': video_url,
                    'talk_id': talk_id,
                    'duration': result.get('duration', 0),
                    'avatar_used': avatar_url,
                    'voice_used': voice_id
                }
            else:
                return {
                    'success': False,
                    'error': 'Video generation timed out',
                    'video_url': None,
                    'talk_id': None
                }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"D-ID API error: {str(e)}"
            try:
                error_detail = response.json()
                error_msg = f"{error_msg} - {error_detail}"
            except:
                pass
            
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'video_url': None,
                'talk_id': None
            }
        except Exception as e:
            error_msg = f"Video creation error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'video_url': None,
                'talk_id': None
            }
    
    def wait_for_video(self, talk_id: str, max_wait: int = 180) -> Optional[str]:
        """Poll D-ID API until video is ready"""
        
        start_time = time.time()
        poll_interval = 5
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/talks/{talk_id}",
                    headers=self.get_headers()
                )
                response.raise_for_status()
                
                result = response.json()
                status = result.get('status')
                
                elapsed = int(time.time() - start_time)
                print(f"⏱️ Status: {status} ({elapsed}s)")
                
                if status == 'done':
                    return result.get('result_url')
                elif status == 'error':
                    error = result.get('error', 'Unknown')
                    print(f"❌ Generation failed: {error}")
                    return None
                elif status in ['created', 'started']:
                    time.sleep(poll_interval)
                else:
                    print(f"⚠️ Unknown status: {status}")
                    time.sleep(poll_interval)
                
            except Exception as e:
                print(f"❌ Polling error: {e}")
                return None
        
        print(f"⏰ Timeout after {max_wait}s")
        return None
    
    def get_video_info(self, talk_id: str) -> Dict:
        """Get video information"""
        try:
            response = requests.get(
                f"{self.base_url}/talks/{talk_id}",
                headers=self.get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}


def test_did_connection():
    """Test D-ID API connection"""
    try:
        did = DIDVideoGenerator()
        print("🧪 Testing D-ID connection...")
        
        response = requests.get(
            f"{did.base_url}/talks",
            headers=did.get_headers(),
            params={'limit': 1}
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_video_generation():
    """Test generating a simple video"""
    try:
        print("🧪 Testing video generation...")
        
        did = DIDVideoGenerator()
        
        test_script = "Hello! This is a test video. If you can see this, the D-ID integration is working perfectly!"
        
        result = did.create_video(
            script=test_script,
            subject='mathematics',
            student_name='Test'
        )
        
        if result['success']:
            print(f"✅ Video generated!")
            print(f"🎥 URL: {result['video_url']}")
            return True
        else:
            print(f"❌ Failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False