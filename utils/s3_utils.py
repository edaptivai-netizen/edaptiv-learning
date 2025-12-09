"""
S3 Utilities for EDAPTIV
"""

import boto3
from django.conf import settings


def generate_presigned_url(file_key, expires_in=3600):
    """
    Generate a pre-signed URL for an S3 object
    
    Args:
        file_key: S3 object key (e.g., 'videos/material_1_abc123.mp4')
        expires_in: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Pre-signed URL string
    """
    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    
    # Generate pre-signed URL
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": file_key
        },
        ExpiresIn=expires_in,
    )
    
    return url


def upload_to_s3(file_obj, file_key, content_type='video/mp4'):
    """
    Upload a file to S3
    
    Args:
        file_obj: File object or bytes
        file_key: S3 object key
        content_type: MIME type of the file
    
    Returns:
        Boolean indicating success
    """
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        
        s3.upload_fileobj(
            file_obj,
            settings.AWS_STORAGE_BUCKET_NAME,
            file_key,
            ExtraArgs={'ContentType': content_type}
        )
        
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False