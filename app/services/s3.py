"""
S3 service for file uploads with pre-signed URLs.

Provides secure file uploads without exposing AWS credentials to clients.
"""

import logging
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.observability import tracer

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 file operations."""

    def __init__(self) -> None:
        """Initialize S3 service with AWS credentials."""
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region,
        )

    async def generate_presigned_upload_url(
        self,
        file_key: str,
        content_type: str,
        max_size_mb: Optional[int] = None,
    ) -> Dict[str, any]:
        """
        Generate pre-signed POST URL for direct client uploads.

        Args:
            file_key: S3 object key (path)
            content_type: MIME type of file
            max_size_mb: Maximum file size in MB

        Returns:
            Dict with 'url' and 'fields' for POST request
        """
        with tracer.start_as_current_span("s3.generate_presigned_upload_url") as span:
            span.set_attribute("s3.bucket", self.bucket_name)
            span.set_attribute("s3.key", file_key)
            span.set_attribute("s3.content_type", content_type)

            try:
                async with self.session.client("s3") as s3_client:
                    # Build conditions
                    conditions = [
                        {"bucket": self.bucket_name},
                        ["starts-with", "$key", file_key.rsplit("/", 1)[0] + "/"],
                        {"Content-Type": content_type},
                    ]

                    # Add size limit if specified
                    if max_size_mb is None:
                        max_size_mb = settings.MAX_UPLOAD_SIZE_MB

                    max_size_bytes = max_size_mb * 1024 * 1024
                    conditions.append(["content-length-range", 0, max_size_bytes])

                    # Generate pre-signed POST
                    response = await s3_client.generate_presigned_post(
                        Bucket=self.bucket_name,
                        Key=file_key,
                        Fields={"Content-Type": content_type},
                        Conditions=conditions,
                        ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
                    )

                    logger.info(
                        f"Generated pre-signed upload URL for {file_key}",
                        extra={"key": file_key, "content_type": content_type},
                    )

                    return response

            except ClientError as e:
                logger.error(f"Failed to generate pre-signed URL: {e}", exc_info=True)
                raise

    async def generate_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate pre-signed GET URL for downloading files.

        Args:
            file_key: S3 object key
            expires_in: URL expiration in seconds

        Returns:
            Pre-signed download URL
        """
        with tracer.start_as_current_span("s3.generate_presigned_download_url") as span:
            span.set_attribute("s3.bucket", self.bucket_name)
            span.set_attribute("s3.key", file_key)

            try:
                async with self.session.client("s3") as s3_client:
                    url = await s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": file_key},
                        ExpiresIn=expires_in,
                    )

                    logger.info(
                        f"Generated pre-signed download URL for {file_key}",
                        extra={"key": file_key},
                    )

                    return url

            except ClientError as e:
                logger.error(f"Failed to generate download URL: {e}", exc_info=True)
                raise

    @staticmethod
    def generate_file_key(
        category: str,
        org_id: str,
        filename: str,
    ) -> str:
        """
        Generate unique S3 key for file storage.

        Args:
            category: File category (e.g., 'driver_licenses', 'insurance')
            org_id: Organization ID
            filename: Original filename

        Returns:
            S3 object key
        """
        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid4().hex[:8]
        file_ext = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if file_ext:
            new_filename = f"{timestamp}_{unique_id}.{file_ext}"
        else:
            new_filename = f"{timestamp}_{unique_id}"

        # Construct key: category/org_id/filename
        key = f"{category}/{org_id}/{new_filename}"

        return key

    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """
        Validate file extension against allowed types.

        Args:
            filename: Original filename

        Returns:
            True if valid, False otherwise
        """
        if "." not in filename:
            return False

        ext = "." + filename.rsplit(".", 1)[-1].lower()
        return ext in settings.ALLOWED_UPLOAD_EXTENSIONS

    @staticmethod
    def get_content_type(filename: str) -> str:
        """
        Get content type from filename.

        Args:
            filename: Filename

        Returns:
            MIME type
        """
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3.

        Args:
            file_key: S3 object key

        Returns:
            True if successful
        """
        with tracer.start_as_current_span("s3.delete_file") as span:
            span.set_attribute("s3.bucket", self.bucket_name)
            span.set_attribute("s3.key", file_key)

            try:
                async with self.session.client("s3") as s3_client:
                    await s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)

                    logger.info(f"Deleted file from S3: {file_key}", extra={"key": file_key})

                    return True

            except ClientError as e:
                logger.error(f"Failed to delete file: {e}", exc_info=True)
                return False
