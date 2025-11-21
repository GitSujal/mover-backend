"""Invoice schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    """Request to create an invoice for a completed booking."""

    booking_id: UUID = Field(description="Booking ID")
    notes: str | None = Field(None, description="Additional notes", max_length=1000)


class InvoiceUpdate(BaseModel):
    """Update invoice status or payment info."""

    status: InvoiceStatus | None = None
    payment_method: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=1000)


class InvoiceLineItem(BaseModel):
    """Single line item on invoice."""

    description: str
    quantity: int
    unit_price: float
    total: float


class InvoiceResponse(BaseModel):
    """Complete invoice details."""

    id: UUID
    booking_id: UUID
    invoice_number: str

    # Amounts
    subtotal: float
    platform_fee: float
    tax_amount: float
    total_amount: float

    # Status
    status: InvoiceStatus
    issued_at: datetime
    paid_at: datetime | None
    due_date: datetime | None
    payment_method: str | None

    # Payment processing
    stripe_invoice_id: str | None
    stripe_payment_intent_id: str | None

    # Document
    pdf_url: str | None
    notes: str | None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceDetailedResponse(InvoiceResponse):
    """Invoice with full booking details for PDF generation."""

    # Customer info
    customer_name: str
    customer_email: str
    customer_phone: str

    # Mover info
    mover_name: str
    mover_email: str
    mover_phone: str | None
    mover_address: str | None

    # Move details
    move_date: datetime
    pickup_address: str
    dropoff_address: str
    estimated_distance_miles: float
    estimated_duration_hours: float

    # Line items for PDF
    line_items: list[InvoiceLineItem]


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    invoices: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class InvoiceStats(BaseModel):
    """Invoice statistics for an organization."""

    total_invoices: int
    total_revenue: float
    paid_invoices: int
    overdue_invoices: int
    draft_invoices: int
    average_invoice_amount: float
