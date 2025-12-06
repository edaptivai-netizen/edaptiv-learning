from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from learning.models import AvatarVideo, AdaptedContent
from utils.ai_integration import DIDVideoGenerator
import uuid


class Command(BaseCommand):
    help = 'Regenerate expired videos and save them permanently'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate ALL videos (even ones with files)',
        )
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Only regenerate videos without permanent files',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Starting video regeneration...'))
        
        # Get videos that need regeneration
        if options['all']:
            videos = AvatarVideo.objects.all()
            self.stdout.write(f"📹 Found {videos.count()} total videos")
        else:
            # Only videos without permanent files
            videos = AvatarVideo.objects.filter(video_file='')
            self.stdout.write(f"📹 Found {videos.count()} videos without permanent files")
        
        if videos.count() == 0:
            self.stdout.write(self.style.SUCCESS('✅ No videos need regeneration!'))
            return
        
        # Confirm before proceeding
        if not options['all']:
            confirm = input(f"Regenerate {videos.count()} videos? This will use D-ID credits. (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('❌ Cancelled'))
                return
        
        did = DIDVideoGenerator()
        success_count = 0
        error_count = 0
        
        for video in videos:
            try:
                self.stdout.write(f"\n🎬 Processing: {video.avatar_name}")
                
                # Get the adapted content
                adapted_content = video.adapted_content
                material = adapted_content.original_material
                
                # Check if we have a teaching script
                if not adapted_content.teaching_script:
                    self.stdout.write(self.style.WARNING(f"⚠  No teaching script found, skipping..."))
                    continue
                
                # Generate new video
                self.stdout.write(f"🤖 Generating video for {material.title}...")
                
                video_result = did.create_video(
                    script=adapted_content.teaching_script,
                    subject=material.subject,
                    student_name="Student"
                )
                
                if video_result['success']:
                    # Download video content
                    video_content = video_result['video_content']
                    
                    if video_content:
                        # Create filename
                        filename = f"{material.id}_{uuid.uuid4().hex[:8]}.mp4"
                        
                        # Save to video model
                        video.video_file.save(
                            filename,
                            ContentFile(video_content),
                            save=False
                        )
                        
                        # Update other fields
                        video.talk_id = video_result['talk_id']
                        video.duration = video_result.get('duration', 0)
                        video.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"✅ Saved to: media/videos/{filename}"))
                        success_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Failed to download video"))
                        error_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Error: {video_result.get('error')}"))
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Exception: {e}"))
                error_count += 1
                import traceback
                traceback.print_exc()
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n📊 Summary:"))
        self.stdout.write(f"✅ Success: {success_count}")
        self.stdout.write(f"❌ Errors: {error_count}")
        self.stdout.write(f"💰 Estimated cost: ${success_count * 1.13:.2f}")