"""Invoice generation service with PDF export."""

import io
import logging
from datetime import datetime, timedelta
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.services.notification_templates import EmailTemplates
from app.services.notifications import NotificationService
from app.services.s3 import S3Service

logger = logging.getLogger(__name__)


class InvoiceError(Exception):
    """Base exception for invoice errors."""

    pass


class InvoiceAlreadyExistsError(InvoiceError):
    """Raised when invoice already exists for booking."""

    pass


class BookingNotCompletedError(InvoiceError):
    """Raised when trying to invoice incomplete booking."""

    pass


class InvoiceService:
    """Service for invoice generation, PDF export, and management."""

    @staticmethod
    async def generate_invoice_number(db: AsyncSession, org_id: UUID) -> str:
        """
        Generate unique invoice number.

        Format: INV-{YEAR}-{ORG_SHORT}-{SEQUENCE}
        Example: INV-2025-ABC-00123

        Args:
            db: Database session
            org_id: Organization ID

        Returns:
            Formatted invoice number
        """
        # Get organization code (first 3 letters of ID)
        org_code = str(org_id)[:8].upper()

        # Get current year
        year = datetime.utcnow().year

        # Get count of invoices for this organization this year
        result = await db.execute(
            select(func.count(Invoice.id))
            .join(Booking)
            .where(Booking.org_id == org_id)
            .where(func.extract("year", Invoice.created_at) == year)
        )
        count = result.scalar_one() or 0

        # Format sequence number with leading zeros
        sequence = str(count + 1).zfill(5)

        return f"INV-{year}-{org_code}-{sequence}"

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        booking_id: UUID,
        notes: str | None = None,
    ) -> Invoice:
        """
        Create invoice for a completed booking.

        Args:
            db: Database session
            booking_id: Booking ID
            notes: Optional invoice notes

        Returns:
            Created invoice

        Raises:
            BookingNotCompletedError: If booking not completed
            InvoiceAlreadyExistsError: If invoice already exists
        """
        with tracer.start_as_current_span("invoice.create") as span:
            span.set_attribute("booking_id", str(booking_id))

            # Fetch booking with organization
            result = await db.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()

            if not booking:
                raise InvoiceError(f"Booking {booking_id} not found")

            # Verify booking is completed
            if booking.status != BookingStatus.COMPLETED:
                raise BookingNotCompletedError(
                    f"Booking {booking_id} is not completed. Current status: {booking.status.value}"
                )

            # Check if invoice already exists
            existing_result = await db.execute(
                select(Invoice).where(Invoice.booking_id == booking_id)
            )
            existing_invoice = existing_result.scalar_one_or_none()

            if existing_invoice:
                raise InvoiceAlreadyExistsError(
                    f"Invoice already exists for booking {booking_id}: {existing_invoice.invoice_number}"
                )

            # Generate invoice number
            invoice_number = await InvoiceService.generate_invoice_number(
                db=db,
                org_id=booking.org_id,
            )

            # Use final_amount if set, otherwise estimated_amount
            subtotal = float(booking.final_amount or booking.estimated_amount)
            platform_fee = float(booking.platform_fee)

            # Calculate tax (simplified - would use tax service in production)
            tax_amount = 0.0  # TODO: Implement proper tax calculation

            total_amount = subtotal + tax_amount

            # Calculate due date (30 days from now)
            due_date = datetime.utcnow() + timedelta(days=30)

            # Create invoice
            invoice = Invoice(
                booking_id=booking_id,
                invoice_number=invoice_number,
                subtotal=subtotal,
                platform_fee=platform_fee,
                tax_amount=tax_amount,
                total_amount=total_amount,
                status=InvoiceStatus.ISSUED,
                due_date=due_date,
                stripe_payment_intent_id=booking.stripe_payment_intent_id,
                notes=notes,
            )

            db.add(invoice)
            await db.commit()
            await db.refresh(invoice)

            logger.info(
                f"Invoice created: {invoice_number} for booking {booking_id}",
                extra={
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice_number,
                    "booking_id": str(booking_id),
                    "total_amount": total_amount,
                },
            )

            # Generate PDF
            try:
                pdf_url = await InvoiceService.generate_and_upload_pdf(
                    db=db,
                    invoice=invoice,
                )
                invoice.pdf_url = pdf_url
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to generate PDF for invoice {invoice.id}: {e}")
                # Continue - invoice created even if PDF fails

            # Send invoice email
            try:
                await InvoiceService.send_invoice_email(
                    db=db,
                    invoice=invoice,
                )
            except Exception as e:
                logger.error(f"Failed to send invoice email: {e}")

            return invoice

    @staticmethod
    async def generate_pdf(
        invoice: Invoice,
        booking: Booking,
    ) -> bytes:
        """
        Generate PDF invoice document.

        Args:
            invoice: Invoice object
            booking: Booking object

        Returns:
            PDF bytes
        """
        with tracer.start_as_current_span("invoice.generate_pdf"):
            buffer = io.BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
            )

            # Container for PDF elements
            elements = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
            )

            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
            )

            # Title
            title = Paragraph("INVOICE", title_style)
            elements.append(title)

            # Invoice details
            invoice_info = [
                ["Invoice Number:", invoice.invoice_number],
                ["Invoice Date:", invoice.created_at.strftime("%B %d, %Y")],
                [
                    "Due Date:",
                    invoice.due_date.strftime("%B %d, %Y")
                    if invoice.due_date
                    else "Upon receipt",
                ],
                ["Status:", invoice.status.value.upper()],
            ]

            invoice_table = Table(invoice_info, colWidths=[2 * inch, 3 * inch])
            invoice_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                        ("ALIGN", (1, 0), (1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(invoice_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Customer information
            elements.append(Paragraph("Bill To:", heading_style))
            customer_info = [
                [booking.customer_name],
                [booking.customer_email],
                [booking.customer_phone],
            ]
            customer_table = Table(customer_info, colWidths=[5 * inch])
            customer_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ]
                )
            )
            elements.append(customer_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Move details
            elements.append(Paragraph("Move Details:", heading_style))
            move_info = [
                ["Move Date:", booking.move_date.strftime("%B %d, %Y at %I:%M %p")],
                ["From:", booking.pickup_address],
                ["To:", booking.dropoff_address],
                [
                    "Distance:",
                    f"{float(booking.estimated_distance_miles):.1f} miles",
                ],
                [
                    "Duration:",
                    f"{float(booking.estimated_duration_hours):.1f} hours",
                ],
            ]
            move_table = Table(move_info, colWidths=[1.5 * inch, 4 * inch])
            move_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            elements.append(move_table)
            elements.append(Spacer(1, 0.4 * inch))

            # Line items
            elements.append(Paragraph("Charges:", heading_style))
            line_items = [
                ["Description", "Amount"],
                ["Moving Service", f"${invoice.subtotal:.2f}"],
            ]

            if invoice.tax_amount > 0:
                line_items.append(["Tax", f"${invoice.tax_amount:.2f}"])

            line_items.append(["", ""])  # Separator
            line_items.append(["Total Amount Due", f"${invoice.total_amount:.2f}"])

            line_table = Table(line_items, colWidths=[4 * inch, 1.5 * inch])
            line_table.setStyle(
                TableStyle(
                    [
                        # Header row
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        # Content rows
                        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -2), 10),
                        # Total row
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, -1), (-1, -1), 12),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f0f0f0")),
                        # Alignment
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        # Grid
                        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.black),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                        ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
                        ("LINEBELOW", (0, -1), (-1, -1), 2, colors.black),
                    ]
                )
            )
            elements.append(line_table)
            elements.append(Spacer(1, 0.5 * inch))

            # Notes
            if invoice.notes:
                elements.append(Paragraph("Notes:", heading_style))
                notes = Paragraph(invoice.notes, styles["Normal"])
                elements.append(notes)
                elements.append(Spacer(1, 0.3 * inch))

            # Footer
            footer = Paragraph(
                "Thank you for your business!<br/>For questions about this invoice, please contact the moving company.",
                styles["Normal"],
            )
            elements.append(footer)

            # Build PDF
            doc.build(elements)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

    @staticmethod
    async def generate_and_upload_pdf(
        db: AsyncSession,
        invoice: Invoice,
    ) -> str:
        """
        Generate PDF and upload to S3.

        Args:
            db: Database session
            invoice: Invoice object

        Returns:
            S3 URL for PDF
        """
        with tracer.start_as_current_span("invoice.generate_and_upload_pdf"):
            # Get booking
            result = await db.execute(
                select(Booking).where(Booking.id == invoice.booking_id)
            )
            booking = result.scalar_one()

            # Generate PDF
            pdf_bytes = await InvoiceService.generate_pdf(
                invoice=invoice,
                booking=booking,
            )

            # Upload to S3
            s3_service = S3Service()
            filename = f"invoices/{invoice.invoice_number}.pdf"

            pdf_url = await s3_service.upload_file(
                file_data=pdf_bytes,
                filename=filename,
                content_type="application/pdf",
            )

            logger.info(
                f"Invoice PDF uploaded: {invoice.invoice_number}",
                extra={
                    "invoice_id": str(invoice.id),
                    "pdf_url": pdf_url,
                },
            )

            return pdf_url

    @staticmethod
    async def send_invoice_email(
        db: AsyncSession,
        invoice: Invoice,
    ) -> None:
        """
        Send invoice email to customer.

        Args:
            db: Database session
            invoice: Invoice object
        """
        with tracer.start_as_current_span("invoice.send_email"):
            # Get booking
            result = await db.execute(
                select(Booking).where(Booking.id == invoice.booking_id)
            )
            booking = result.scalar_one()

            notification_service = NotificationService()
            email_templates = EmailTemplates()

            booking_details = {
                "booking_id": str(booking.id),
                "invoice_number": invoice.invoice_number,
                "total_amount": f"{invoice.total_amount:.2f}",
                "due_date": invoice.due_date.strftime("%B %d, %Y")
                if invoice.due_date
                else "Upon receipt",
                "pdf_url": invoice.pdf_url or "#",
            }

            await notification_service.send_email(
                to_email=booking.customer_email,
                subject=f"Invoice {invoice.invoice_number} - MoveHub",
                html_content=email_templates.invoice_sent(
                    customer_name=booking.customer_name,
                    booking_details=booking_details,
                ),
            )

            logger.info(
                f"Invoice email sent: {invoice.invoice_number} to {booking.customer_email}"
            )

    @staticmethod
    async def mark_invoice_paid(
        db: AsyncSession,
        invoice_id: UUID,
        payment_method: str = "stripe",
    ) -> Invoice:
        """
        Mark invoice as paid.

        Args:
            db: Database session
            invoice_id: Invoice ID
            payment_method: Payment method used

        Returns:
            Updated invoice
        """
        with tracer.start_as_current_span("invoice.mark_paid"):
            result = await db.execute(
                select(Invoice).where(Invoice.id == invoice_id)
            )
            invoice = result.scalar_one_or_none()

            if not invoice:
                raise InvoiceError(f"Invoice {invoice_id} not found")

            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.utcnow()
            invoice.payment_method = payment_method

            await db.commit()
            await db.refresh(invoice)

            logger.info(
                f"Invoice marked as paid: {invoice.invoice_number}",
                extra={
                    "invoice_id": str(invoice.id),
                    "payment_method": payment_method,
                },
            )

            return invoice
