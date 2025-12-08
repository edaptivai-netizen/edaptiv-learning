# utils/s3.py
import boto3
from django.conf import settings
from botocore.client import Config


# Create a reusable S3 client (uses settings)
def _s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
        aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
        region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
        config=Config(signature_version="s3v4")
    )

def upload_fileobj(file_obj, key):
    """
    Uploads a file-like object (BytesIO or resp.raw) to S3 under the given key.
    Returns the key on success.
    """
    s3 = _s3_client()
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    # reset stream position if possible
    try:
        file_obj.seek(0)
    except Exception:
        pass
    s3.upload_fileobj(Fileobj=file_obj, Bucket=bucket, Key=key, ExtraArgs={"ContentType": "video/mp4"})
    return key

def generate_presigned_url(s3_key, expires=300):
    s3 = _s3_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expires
    )
    return url

def upload_fileobj(file_obj, key):
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    s3.upload_fileobj(file_obj, bucket, key)
    return key