# utils/middleware/refresh_presigned.py
import datetime
from django.utils import timezone
from learning.models import AvatarVideo


class RefreshPresignedURLMiddleware:
    """
    Auto-refresh S3 presigned video URLs when they are older than X minutes.
    Ensures videos never expire for the user.
    """

    REFRESH_AFTER_MINUTES = 50  # presigned URLs usually last 60 mins

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only refresh on HTML GET page loads
        if request.method != "GET":
            return response

        # Refresh URLs if stale
        cutoff = timezone.now() - datetime.timedelta(minutes=self.REFRESH_AFTER_MINUTES)

        stale_videos = AvatarVideo.objects.filter(last_refreshed_at__lt=cutoff)

        for video in stale_videos:
            video.refresh_presigned_url()

        return response
