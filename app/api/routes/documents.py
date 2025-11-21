"""Document upload API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.document_upload import (
    DownloadURLRequest,
    DownloadURLResponse,
    UploadCompleteRequest,
    UploadCompleteResponse,
    UploadURLRequest,
    UploadURLResponse,
)
from app.services.s3 import S3Service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(
    upload_request: UploadURLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UploadURLResponse:
    """
    Get presigned URL for direct file upload to S3.

    Client uploads file directly to S3 using the returned URL and fields.
    No file data passes through backend - secure and scalable.

    Requires mover authentication.
    """
    # Validate file type
    if not S3Service.validate_file_type(upload_request.filename):
        allowed_exts = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed extensions: {allowed_exts}",
        )

    # Generate unique S3 key
    file_key = S3Service.generate_file_key(
        category=upload_request.category,
        org_id=str(current_user.org_id),
        filename=upload_request.filename,
    )

    # Generate presigned upload URL
    s3_service = S3Service()

    try:
        presigned_data = await s3_service.generate_presigned_upload_url(
            file_key=file_key,
            content_type=upload_request.content_type,
            max_size_mb=upload_request.max_size_mb,
        )

        logger.info(
            f"Generated upload URL for {current_user.email}: {file_key}",
            extra={
                "user_email": current_user.email,
                "file_key": file_key,
                "category": upload_request.category,
            },
        )

        return UploadURLResponse(
            upload_url=presigned_data["url"],
            upload_fields=presigned_data["fields"],
            file_key=file_key,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
        )

    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL",
        ) from e


@router.post("/upload-complete", response_model=UploadCompleteResponse)
async def notify_upload_complete(
    upload_complete: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UploadCompleteResponse:
    """
    Notify that upload completed.

    Client calls this after successfully uploading to S3.
    Can trigger post-upload processing (e.g., virus scan, thumbnail generation).

    Requires mover authentication.
    """
    # Verify file exists in S3 (optional - adds latency)
    # In production, this would be handled by S3 event notifications

    # Generate download URL
    s3_service = S3Service()

    try:
        download_url = await s3_service.generate_presigned_download_url(
            file_key=upload_complete.file_key,
            expires_in=86400,  # 24 hours
        )

        logger.info(
            f"Upload completed for {current_user.email}: {upload_complete.file_key}",
            extra={
                "user_email": current_user.email,
                "file_key": upload_complete.file_key,
                "document_type": upload_complete.document_type,
            },
        )

        return UploadCompleteResponse(
            file_url=download_url,
            file_key=upload_complete.file_key,
            success=True,
        )

    except Exception as e:
        logger.error(f"Failed to process upload completion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload completion",
        ) from e


@router.post("/download-url", response_model=DownloadURLResponse)
async def get_download_url(
    download_request: DownloadURLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DownloadURLResponse:
    """
    Get presigned URL for downloading a file from S3.

    Requires mover authentication.
    """
    s3_service = S3Service()

    try:
        download_url = await s3_service.generate_presigned_download_url(
            file_key=download_request.file_key,
            expires_in=download_request.expires_in,
        )

        logger.info(
            f"Generated download URL for {current_user.email}: {download_request.file_key}",
            extra={
                "user_email": current_user.email,
                "file_key": download_request.file_key,
            },
        )

        return DownloadURLResponse(
            download_url=download_url,
            expires_in=download_request.expires_in,
        )

    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL",
        ) from e
