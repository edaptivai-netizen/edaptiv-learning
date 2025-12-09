ai_integration

# utils/ai_integration.py - COMPLETE FIX
"""
D-ID Video Avatar Integration for EDAPTIV
"""

import os
import time
import requests
from typing import Dict, Optional


import os
import time
import requests
from typing import Dict

class DIDVideoGenerator:
    """D-ID API Integration with STREAMING video download."""

    def __init__(self):
        self.api_key = os.environ.get('DID_API_KEY')
        self.base_url = "https://api.d-id.com"

        if not self.api_key:
            raise ValueError("D-ID API key missing")

    def get_headers(self):
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Basic {self.api_key}"
        }

    def get_avatar_url(self, subject):
        url = "https://edaptiv-user-avatars.s3.eu-north-1.amazonaws.com/female_tr.png"
        return url

    def get_voice_id(self, subject=None):
        return "en-US-NancyNeural"

    def create_video(self, script: str, subject: str, student_name: str = "friend") -> Dict:
        """Create video and return STREAM for downloading."""
        if not script:
            return {"success": False, "error": "Script empty"}

        payload = {
            "source_url": self.get_avatar_url(subject),
            "script": {
                "type": "text",
                "input": script,
                "provider": {
                    "type": "microsoft",
                    "voice_id": self.get_voice_id()
                }
            },
            "config": {"stitch": True, "fluent": True}
        }

        # Create video job
        resp = requests.post(f"{self.base_url}/talks", json=payload, headers=self.get_headers())
        if resp.status_code not in (200, 201):
            return {"success": False, "error": resp.text}

        data = resp.json()
        talk_id = data.get("id")
        if not talk_id:
            return {"success": False, "error": "Missing talk ID"}

        video_url = self.wait_for_video(talk_id)
        if not video_url:
            return {"success": False, "error": "Timed out"}

        # STREAM the video instead of downloading into memory
        stream_resp = requests.get(video_url, stream=True)
        stream_resp.raise_for_status()

        return {
            "success": True,
            "talk_id": talk_id,
            "duration": data.get("duration", 0),
            "video_stream": stream_resp.raw,  # STREAM OBJECT
            "video_url": video_url,
        }

    def wait_for_video(self, talk_id: str, timeout: int = 150) -> str:
        """Poll D-ID until video ready."""
        for _ in range(timeout):
            resp = requests.get(f"{self.base_url}/talks/{talk_id}", headers=self.get_headers())
            data = resp.json()


            result = data.get("result")
            if result and isinstance(result, dict):
                url= result.get("url")
                if url:
                    return result_url
            
            #Older API fallback
            if "result_url" in data:
                return data["result_url"]

            time.sleep(2)

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

# Add this method to your DIDVideoGenerator class
def create_and_stream_to_s3(self, script: str, subject: str, s3_key: str, timeout_sec: int = 240) -> Dict:
    """Create video and stream directly to S3"""
    import boto3
    from django.conf import settings
    
    # Create video with D-ID
    result = self.create_video(script, subject)
    
    if not result.get("success"):
        return result
    
    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    
    # Stream video directly to S3
    try:
        video_stream = result.get("video_stream")
        if not video_stream:
            return {"success": False, "error": "No video stream available"}
        
        # Upload stream to S3
        s3.upload_fileobj(
            video_stream,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        return {
            "success": True,
            "talk_id": result.get("talk_id"),
            "s3_key": s3_key
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}