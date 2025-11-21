"""Invoice API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_customer_session
from app.core.database import get_db
from app.models.booking import Booking
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import CustomerSession, User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceStats,
    InvoiceUpdate,
)
from app.services.invoice import (
    BookingNotCompletedError,
    InvoiceAlreadyExistsError,
    InvoiceError,
    InvoiceService,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("", response_model=InvoiceResponse)
async def create_invoice(
    invoice_create: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceResponse:
    """
    Create invoice for a completed booking.

    Requires mover authentication.
    Automatically generates PDF and sends email to customer.
    """
    try:
        # Verify booking belongs to user's organization
        result = await db.execute(
            select(Booking).where(Booking.id == invoice_create.booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {invoice_create.booking_id} not found",
            )

        if booking.org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create invoices for your organization's bookings",
            )

        # Create invoice
        invoice = await InvoiceService.create_invoice(
            db=db,
            booking_id=invoice_create.booking_id,
            notes=invoice_create.notes,
        )

        logger.info(
            f"Invoice created by {current_user.email}: {invoice.invoice_number}",
            extra={
                "invoice_id": str(invoice.id),
                "user_email": current_user.email,
                "booking_id": str(invoice_create.booking_id),
            },
        )

        return InvoiceResponse(
            id=invoice.id,
            booking_id=invoice.booking_id,
            invoice_number=invoice.invoice_number,
            subtotal=invoice.subtotal,
            platform_fee=invoice.platform_fee,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            status=invoice.status,
            issued_at=invoice.created_at,
            paid_at=invoice.paid_at,
            due_date=invoice.due_date,
            payment_method=invoice.payment_method,
            stripe_invoice_id=invoice.stripe_invoice_id,
            stripe_payment_intent_id=invoice.stripe_payment_intent_id,
            pdf_url=invoice.pdf_url,
            notes=invoice.notes,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

    except InvoiceAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except BookingNotCompletedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except InvoiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invoice: {str(e)}",
        ) from e


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceResponse:
    """
    Get invoice by ID.

    Requires mover authentication.
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Verify invoice belongs to user's organization
    booking_result = await db.execute(
        select(Booking).where(Booking.id == invoice.booking_id)
    )
    booking = booking_result.scalar_one()

    if booking.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return InvoiceResponse(
        id=invoice.id,
        booking_id=invoice.booking_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        platform_fee=invoice.platform_fee,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status,
        issued_at=invoice.created_at,
        paid_at=invoice.paid_at,
        due_date=invoice.due_date,
        payment_method=invoice.payment_method,
        stripe_invoice_id=invoice.stripe_invoice_id,
        stripe_payment_intent_id=invoice.stripe_payment_intent_id,
        pdf_url=invoice.pdf_url,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


@router.get("/booking/{booking_id}", response_model=InvoiceResponse | None)
async def get_invoice_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> InvoiceResponse | None:
    """
    Get invoice for a booking.

    Requires customer session authentication.
    Returns None if no invoice exists.
    """
    # Get booking
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found",
        )

    # Verify customer owns booking
    if booking.customer_email != customer_session.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get invoice
    result = await db.execute(
        select(Invoice).where(Invoice.booking_id == booking_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        return None

    return InvoiceResponse(
        id=invoice.id,
        booking_id=invoice.booking_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        platform_fee=invoice.platform_fee,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status,
        issued_at=invoice.created_at,
        paid_at=invoice.paid_at,
        due_date=invoice.due_date,
        payment_method=invoice.payment_method,
        stripe_invoice_id=invoice.stripe_invoice_id,
        stripe_payment_intent_id=invoice.stripe_payment_intent_id,
        pdf_url=invoice.pdf_url,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_update: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceResponse:
    """
    Update invoice status or details.

    Requires mover authentication.
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_id} not found",
        )

    # Verify invoice belongs to user's organization
    booking_result = await db.execute(
        select(Booking).where(Booking.id == invoice.booking_id)
    )
    booking = booking_result.scalar_one()

    if booking.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update fields
    if invoice_update.status is not None:
        invoice.status = invoice_update.status
    if invoice_update.payment_method is not None:
        invoice.payment_method = invoice_update.payment_method
    if invoice_update.notes is not None:
        invoice.notes = invoice_update.notes

    await db.commit()
    await db.refresh(invoice)

    logger.info(
        f"Invoice updated: {invoice.invoice_number}",
        extra={
            "invoice_id": str(invoice.id),
            "user_email": current_user.email,
        },
    )

    return InvoiceResponse(
        id=invoice.id,
        booking_id=invoice.booking_id,
        invoice_number=invoice.invoice_number,
        subtotal=invoice.subtotal,
        platform_fee=invoice.platform_fee,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status,
        issued_at=invoice.created_at,
        paid_at=invoice.paid_at,
        due_date=invoice.due_date,
        payment_method=invoice.payment_method,
        stripe_invoice_id=invoice.stripe_invoice_id,
        stripe_payment_intent_id=invoice.stripe_payment_intent_id,
        pdf_url=invoice.pdf_url,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: UUID,
    payment_method: str = "stripe",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceResponse:
    """
    Mark invoice as paid.

    Requires mover authentication.
    """
    try:
        invoice = await InvoiceService.mark_invoice_paid(
            db=db,
            invoice_id=invoice_id,
            payment_method=payment_method,
        )

        return InvoiceResponse(
            id=invoice.id,
            booking_id=invoice.booking_id,
            invoice_number=invoice.invoice_number,
            subtotal=invoice.subtotal,
            platform_fee=invoice.platform_fee,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            status=invoice.status,
            issued_at=invoice.created_at,
            paid_at=invoice.paid_at,
            due_date=invoice.due_date,
            payment_method=invoice.payment_method,
            stripe_invoice_id=invoice.stripe_invoice_id,
            stripe_payment_intent_id=invoice.stripe_payment_intent_id,
            pdf_url=invoice.pdf_url,
            notes=invoice.notes,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )

    except InvoiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/organization/{org_id}/list", response_model=InvoiceListResponse)
async def list_organization_invoices(
    org_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: InvoiceStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceListResponse:
    """
    List invoices for an organization.

    Requires mover authentication.
    """
    # Verify user belongs to organization
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Build query
    query = (
        select(Invoice)
        .join(Booking)
        .where(Booking.org_id == org_id)
        .order_by(Invoice.created_at.desc())
    )

    if status_filter:
        query = query.where(Invoice.status == status_filter)

    # Get total count
    count_result = await db.execute(
        select(func.count(Invoice.id)).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Get page
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    invoices = result.scalars().all()

    return InvoiceListResponse(
        invoices=[
            InvoiceResponse(
                id=inv.id,
                booking_id=inv.booking_id,
                invoice_number=inv.invoice_number,
                subtotal=inv.subtotal,
                platform_fee=inv.platform_fee,
                tax_amount=inv.tax_amount,
                total_amount=inv.total_amount,
                status=inv.status,
                issued_at=inv.created_at,
                paid_at=inv.paid_at,
                due_date=inv.due_date,
                payment_method=inv.payment_method,
                stripe_invoice_id=inv.stripe_invoice_id,
                stripe_payment_intent_id=inv.stripe_payment_intent_id,
                pdf_url=inv.pdf_url,
                notes=inv.notes,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
            )
            for inv in invoices
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/organization/{org_id}/stats", response_model=InvoiceStats)
async def get_organization_invoice_stats(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvoiceStats:
    """
    Get invoice statistics for an organization.

    Requires mover authentication.
    """
    # Verify user belongs to organization
    if current_user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get all invoices for organization
    result = await db.execute(
        select(Invoice)
        .join(Booking)
        .where(Booking.org_id == org_id)
    )
    invoices = result.scalars().all()

    total_invoices = len(invoices)
    total_revenue = sum(float(inv.total_amount) for inv in invoices)
    paid_invoices = sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID)
    overdue_invoices = sum(
        1 for inv in invoices if inv.status == InvoiceStatus.OVERDUE
    )
    draft_invoices = sum(1 for inv in invoices if inv.status == InvoiceStatus.DRAFT)

    average_invoice_amount = total_revenue / total_invoices if total_invoices > 0 else 0

    return InvoiceStats(
        total_invoices=total_invoices,
        total_revenue=total_revenue,
        paid_invoices=paid_invoices,
        overdue_invoices=overdue_invoices,
        draft_invoices=draft_invoices,
        average_invoice_amount=average_invoice_amount,
    )


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Download invoice PDF.

    Public endpoint - uses invoice ID as access token.
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()

    if not invoice or not invoice.pdf_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice PDF not found",
        )

    # In production, this would redirect to S3 presigned URL
    # For now, return PDF URL in response header
    return Response(
        content=f"Redirect to: {invoice.pdf_url}",
        media_type="text/plain",
        headers={
            "Location": invoice.pdf_url,
        },
        status_code=302,
    )
