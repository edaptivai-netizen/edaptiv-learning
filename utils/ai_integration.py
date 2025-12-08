# utils/ai_integration.py
import os
import time
import requests
import uuid
import logging
from typing import Dict, Optional
from io import BytesIO
from tempfile import NamedTemporaryFile
from django.conf import settings
from django.utils import timezone
import boto3

from django.conf import settings


from .s3 import generate_presigned_url

# Import your models (adjust path if different)
from learning.models import AvatarVideo, AdaptedContent

logger = logging.getLogger(__name__)


class DIDVideoGenerator:
    """
    D-ID API integration that:
      - creates /talks
      - polls until result URL is ready
      - streams the MP4 from D-ID directly into S3 (memory-safe)
      - creates AvatarVideo and updates AdaptedContent with permanent S3 URL
    """

    def __init__(self):
        self.api_key = os.environ.get("DID_API_KEY")
        self.base_url = "https://api.d-id.com"
        if not self.api_key:
            raise ValueError("D-ID API key missing (set DID_API_KEY env var)")

        # boto3 client (uses keys from settings)
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def get_headers(self):
        # If your D-ID plan needs 'Bearer' change accordingly
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Basic {self.api_key}",
        }

    def get_avatar_url(self, subject=None):
        # default avatar; you can make this dynamic by subject
        return "https://edaptiv-user-avatars.s3.eu-north-1.amazonaws.com/female_tr.png"

    def get_voice_id(self, subject=None):
        # adjust mapping as needed
        return "en-US-NancyNeural"

    # --------------------
    # API helpers
    # --------------------
    def _create_talk(self, script: str, subject: Optional[str] = None) -> Dict:
        payload = {
            "source_url": self.get_avatar_url(subject),
            "script": {
                "type": "text",
                "input": script,
                "provider": {"type": "microsoft", "voice_id": self.get_voice_id(subject)},
            },
            "config": {"stitch": True, "fluent": True},
        }
        resp = requests.post(f"{self.base_url}/talks", json=payload, headers=self.get_headers(), timeout=30)
        if resp.status_code not in (200, 201):
            logger.warning("D-ID create talk failed: %s %s", resp.status_code, resp.text)
            return {"success": False, "status_code": resp.status_code, "text": resp.text}
        return {"success": True, "data": resp.json()}

    def _wait_for_video_url(self, talk_id: str, timeout: int = 300) -> Optional[str]:
        """Poll /talks/<id> until result.url or result_url appears or timeout"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = requests.get(f"{self.base_url}/talks/{talk_id}", headers=self.get_headers(), timeout=20)
            except Exception as e:
                logger.debug("D-ID poll exception (continuing): %s", e)
                time.sleep(2)
                continue

            if resp.status_code != 200:
                time.sleep(2)
                continue

            data = resp.json()
            # newer API: data['result']['url']
            result = data.get("result")
            if isinstance(result, dict):
                url = result.get("url")
                if url:
                    return url
            # older API:
            if data.get("result_url"):
                return data.get("result_url")

            # still not ready
            time.sleep(2)
        return None

    # --------------------
    # Streaming upload helper
    # --------------------
    def _stream_to_s3(self, response: requests.Response, s3_key: str) -> None:
        """
        Attempt to stream response.raw into S3 using upload_fileobj.
        If that fails, fall back to writing to a temporary file then uploading.
        """
        # set decode_content so boto can stream compressed bodies
        try:
            response.raw.decode_content = True
            # upload_fileobj reads from a file-like object
            self.s3.upload_fileobj(response.raw, self.bucket, s3_key, ExtraArgs={"ContentType": "video/mp4"})
            return
        except Exception as e:
            logger.warning("Direct stream upload failed (%s). Falling back to tempfile.", e)

        # fallback: write chunks to a NamedTemporaryFile (disk) then upload
        with NamedTemporaryFile(delete=True) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp.flush()
            tmp.seek(0)
            self.s3.upload_fileobj(tmp, self.bucket, s3_key, ExtraArgs={"ContentType": "video/mp4"})

    # --------------------
    # Public: compat signature (script, subject, s3_key)
    # --------------------
    def create_and_upload(self, script: str, subject: str, s3_key: str, timeout_sec: int = 300) -> Dict:
        """
        Backwards-compatible signature: create D-ID talk from script+subject,
        wait for video, stream to S3 under s3_key, create AvatarVideo and update AdaptedContent NOT done here.
        Returns dict with success,talk_id,s3_key,video_url (permanent S3 http url)
        """
        if not script:
            return {"success": False, "error": "Empty script"}

        # 1) create talk
        create_resp = self._create_talk(script, subject)
        if not create_resp.get("success"):
            return {"success": False, "error": f"Create talk failed: {create_resp.get('text')}"}

        data = create_resp["data"]
        talk_id = data.get("id")
        if not talk_id:
            return {"success": False, "error": "D-ID response missing talk id"}

        # 2) wait for the D-ID to produce a downloadable URL
        video_url = self._wait_for_video_url(talk_id, timeout=timeout_sec)
        if not video_url:
            return {"success": False, "error": "Timed out waiting for D-ID video", "talk_id": talk_id}

        # 3) stream download -> upload to s3
        try:
            with requests.get(video_url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                self._stream_to_s3(resp, s3_key)
        except Exception as e:
            logger.exception("Stream/download/upload error")
            return {"success": False, "error": f"Stream/download/upload error: {e}", "talk_id": talk_id}

        # 4) build permanent S3 URL (public or presigned depending on your setup)
        # If you're serving files via django-storages S3Boto3Storage, AvatarVideo FileField.url will give the URL.
        # As a quick return, construct a presigned URL for immediate consumption (short lived).
        try:
            presigned = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=300,
            )
        except Exception:
            presigned = None

        return {"success": True, "talk_id": talk_id, "s3_key": s3_key, "video_url": presigned}

    # --------------------
    # Public: convenience for AdaptedContent object
    # --------------------
    
def generate_video_for_adapted_content(ac: AdaptedContent):
    """
    Full end-to-end pipeline:
    - generate S3 key
    - call D-ID create_and_upload()
    - create AvatarVideo entry
    - update AdaptedContent fields
    """

    did = DIDVideoGenerator()

    # --- 1. Generate S3 key
    s3_key = f"videos/adapted_{uuid.uuid4().hex}.mp4"

    # --- 2. Call D‑ID (stream → S3)
    subject = ac.original_material.subject
    res = did.create_and_upload(ac.adapted_text, ac.original_material.subject, s3_key)

    if not res["success"]:
        ac.video_generation_status = "failed"
        ac.video_error_message = res.get("error", "Unknown error")
        ac.save(update_fields=["video_generation_status", "video_error_message"])
        return res

    talk_id = res["talk_id"]

    # --- 3. Build presigned URL for playback
    presigned_url = generate_presigned_url(s3_key)

    # --- 4. Create or update AvatarVideo record
    video_obj, created = AvatarVideo.objects.update_or_create(
        adapted_content=ac,
        defaults={
            "talk_id": talk_id,
            "s3_key": s3_key,
            "video_url": presigned_url,
            "last_refreshed_at": timezone.now(),
        }
    )

    # --- 5. Update AdaptedContent with correct video metadata
    ac.video_s3_key = s3_key
    ac.video_url = presigned_url
    ac.video_talk_id = talk_id
    ac.video_generated_at = timezone.now()
    ac.video_generation_status = "completed"
    ac.video_error_message = None
    ac.video_duration = None  # Optional: fill later if you want

    ac.save()

    return {
        "success": True,
        "talk_id": talk_id,
        "s3_key": s3_key,
        "video_url": presigned_url,
        "avatar_video_id": video_obj.id,
    }
