"""Document upload schemas."""

from pydantic import BaseModel, Field


class UploadURLRequest(BaseModel):
    """Request for presigned upload URL."""

    filename: str = Field(description="Original filename", min_length=1, max_length=255)
    content_type: str = Field(description="MIME type of file")
    category: str = Field(
        description="Document category (e.g., 'driver_licenses', 'insurance', 'vehicle_registration')"
    )
    max_size_mb: int | None = Field(
        None, description="Maximum file size in MB", ge=1, le=100
    )


class UploadURLResponse(BaseModel):
    """Presigned upload URL response."""

    upload_url: str = Field(description="URL to POST file to")
    upload_fields: dict[str, str] = Field(
        description="Form fields to include in POST request"
    )
    file_key: str = Field(description="S3 object key for the file")
    expires_in: int = Field(description="URL expiration in seconds")


class UploadCompleteRequest(BaseModel):
    """Notification that upload completed."""

    file_key: str = Field(description="S3 object key")
    document_type: str | None = Field(
        None, description="Type of document for verification"
    )


class UploadCompleteResponse(BaseModel):
    """Response after upload completion."""

    file_url: str = Field(description="Public URL or presigned download URL")
    file_key: str = Field(description="S3 object key")
    success: bool = Field(description="Upload verification status")


class DownloadURLRequest(BaseModel):
    """Request for presigned download URL."""

    file_key: str = Field(description="S3 object key")
    expires_in: int = Field(
        default=3600, description="URL expiration in seconds", ge=60, le=86400
    )


class DownloadURLResponse(BaseModel):
    """Presigned download URL response."""

    download_url: str = Field(description="Presigned GET URL")
    expires_in: int = Field(description="URL expiration in seconds")
