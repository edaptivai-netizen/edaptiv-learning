

import threading
from django.core.files.base import ContentFile
from .models import AvatarVideo, AdaptedContent, StudyMaterial, StudentProfile
import uuid


def generate_video_background(adapted_content_id):
    """
    Background task to generate and save video
    This runs in a separate thread to avoid timeout
    """
    try:
        print(f"🔄 Background video generation started for adapted_content {adapted_content_id}")
        
        # Get adapted content
        adapted_content = AdaptedContent.objects.get(id=adapted_content_id)
        material = adapted_content.original_material
        
        # Create placeholder video record
        avatar_video = AvatarVideo.objects.create(
            adapted_content=adapted_content,
            avatar_name=f"{material.subject} Teacher",
            status='processing'
        )
        
        print(f"📝 Created placeholder video record: {avatar_video.id}")
        
        # Import here to avoid circular imports
        from utils.ai_integration import DIDVideoGenerator
        
        # Generate video
        did = DIDVideoGenerator()
        
        print(f"🎬 Calling D-ID API...")
        video_result = did.create_video(
            script=adapted_content.teaching_script,
            subject=material.subject,
            student_name="Student"
        )
        
        if video_result['success']:
            print(f"✅ Video generated successfully!")
            
            # Download video
            video_content = video_result.get('video_content')
            
            if video_content:
                # Save to permanent storage
                filename = f"{material.id}_{uuid.uuid4().hex[:8]}.mp4"
                avatar_video.video_file.save(
                    filename,
                    ContentFile(video_content),
                    save=False
                )
                
                avatar_video.status = 'completed'
                avatar_video.talk_id = video_result.get('talk_id', '')
                avatar_video.duration = video_result.get('duration', 0)
                avatar_video.save()
                
                print(f"💾 Video saved permanently: {filename}")
            else:
                avatar_video.status = 'failed'
                avatar_video.error_message = 'Failed to download video content'
                avatar_video.save()
                print(f"❌ Failed to download video")
        else:
            avatar_video.status = 'failed'
            avatar_video.error_message = video_result.get('error', 'Unknown error')
            avatar_video.save()
            print(f"❌ Video generation failed: {avatar_video.error_message}")
            
    except Exception as e:
        print(f"❌ Background generation error: {e}")
        try:
            avatar_video.status = 'failed'
            avatar_video.error_message = str(e)
            avatar_video.save()
        except:
            pass
        import traceback
        traceback.print_exc()

def start_video_generation_thread(adapted_content_id):
    thread = threading.Thread(target=generate_video_background, args=(adapted_content_id,))
    thread.start()