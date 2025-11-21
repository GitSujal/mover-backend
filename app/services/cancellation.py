"""Booking cancellation service with refund processing."""

import logging
from datetime import datetime
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.cancellation import (
    BookingCancellation,
    CancellationSource,
    RefundStatus,
)
from app.services.booking_status import BookingStatusService
from app.services.notification_templates import EmailTemplates, SMSTemplates
from app.services.notifications import NotificationService
from app.services.payments import PaymentService

logger = logging.getLogger(__name__)


class CancellationError(Exception):
    """Base exception for cancellation errors."""

    pass


class BookingAlreadyCancelledError(CancellationError):
    """Raised when trying to cancel already cancelled booking."""

    pass


class BookingNotCancellableError(CancellationError):
    """Raised when booking cannot be cancelled."""

    pass


class CancellationService:
    """Service for handling booking cancellations and refunds."""

    # Refund policy tiers based on hours before move
    REFUND_POLICY = {
        72: 100,  # 72+ hours: Full refund (100%)
        48: 75,  # 48-72 hours: 75% refund
        24: 50,  # 24-48 hours: 50% refund
        0: 0,  # <24 hours: No refund
    }

    @staticmethod
    def calculate_refund_percentage(hours_before_move: float) -> int:
        """
        Calculate refund percentage based on cancellation timing.

        Refund policy:
        - 72+ hours before: 100% refund
        - 48-72 hours: 75% refund
        - 24-48 hours: 50% refund
        - <24 hours: 0% refund

        Args:
            hours_before_move: Hours between cancellation and scheduled move

        Returns:
            Refund percentage (0-100)
        """
        for threshold, percentage in sorted(
            CancellationService.REFUND_POLICY.items(), reverse=True
        ):
            if hours_before_move >= threshold:
                return percentage
        return 0

    @staticmethod
    def calculate_refund_amount(
        original_amount: float,
        hours_before_move: float,
    ) -> tuple[float, int]:
        """
        Calculate refund amount based on timing and original amount.

        Args:
            original_amount: Original booking amount
            hours_before_move: Hours before scheduled move

        Returns:
            Tuple of (refund_amount, refund_percentage)
        """
        percentage = CancellationService.calculate_refund_percentage(hours_before_move)
        refund_amount = round(original_amount * (percentage / 100), 2)
        return refund_amount, percentage

    @staticmethod
    async def cancel_booking(
        db: AsyncSession,
        booking_id: UUID,
        reason: str,
        cancelled_by: CancellationSource,
        cancelled_by_name: str = "User",
    ) -> BookingCancellation:
        """
        Cancel a booking and process refund.

        Args:
            db: Database session
            booking_id: Booking ID
            reason: Cancellation reason
            cancelled_by: Who initiated cancellation
            cancelled_by_name: Name of cancelling party

        Returns:
            BookingCancellation record

        Raises:
            BookingAlreadyCancelledError: If booking already cancelled
            BookingNotCancellableError: If booking cannot be cancelled
            CancellationError: For other cancellation errors
        """
        with tracer.start_as_current_span("cancellation.cancel_booking") as span:
            span.set_attribute("booking_id", str(booking_id))
            span.set_attribute("cancelled_by", cancelled_by.value)

            # Fetch booking
            result = await db.execute(
                select(Booking).where(Booking.id == booking_id)
            )
            booking = result.scalar_one_or_none()

            if not booking:
                raise CancellationError(f"Booking {booking_id} not found")

            # Check if already cancelled
            if booking.status == BookingStatus.CANCELLED:
                raise BookingAlreadyCancelledError(
                    f"Booking {booking_id} is already cancelled"
                )

            # Check if booking can be cancelled (completed bookings cannot be cancelled)
            if booking.status == BookingStatus.COMPLETED:
                raise BookingNotCancellableError(
                    "Completed bookings cannot be cancelled. Please create a support ticket for refund requests."
                )

            # Calculate timing
            cancelled_at = datetime.utcnow()
            hours_before_move = (booking.move_date - cancelled_at).total_seconds() / 3600
            hours_before_move = max(0, hours_before_move)  # Cannot be negative

            span.set_attribute("hours_before_move", hours_before_move)

            # Calculate refund
            refund_amount, refund_percentage = CancellationService.calculate_refund_amount(
                original_amount=float(booking.estimated_amount),
                hours_before_move=hours_before_move,
            )

            span.set_attribute("refund_amount", refund_amount)
            span.set_attribute("refund_percentage", refund_percentage)

            # Determine refund reason
            if refund_percentage == 100:
                refund_reason = "Full refund - cancelled 72+ hours before move"
            elif refund_percentage == 75:
                refund_reason = "Partial refund (75%) - cancelled 48-72 hours before move"
            elif refund_percentage == 50:
                refund_reason = "Partial refund (50%) - cancelled 24-48 hours before move"
            else:
                refund_reason = "No refund - cancelled less than 24 hours before move"

            # Determine if rebook should be offered (mover or platform cancellations)
            rebook_offered = cancelled_by in [
                CancellationSource.MOVER,
                CancellationSource.PLATFORM,
            ]

            # Create cancellation record
            cancellation = BookingCancellation(
                booking_id=booking_id,
                org_id=booking.org_id,
                cancelled_by=cancelled_by,
                cancelled_at=cancelled_at,
                cancellation_reason=reason,
                hours_before_move=hours_before_move,
                original_amount=float(booking.estimated_amount),
                platform_fee_paid=float(booking.platform_fee),
                refund_amount=refund_amount,
                refund_reason=refund_reason,
                refund_status=RefundStatus.NO_REFUND
                if refund_amount == 0
                else RefundStatus.PENDING,
                customer_name=booking.customer_name,
                customer_email=booking.customer_email,
                rebook_offered=rebook_offered,
            )

            db.add(cancellation)

            # Process Stripe refund if applicable
            if refund_amount > 0 and booking.stripe_payment_intent_id:
                try:
                    cancellation.refund_status = RefundStatus.PROCESSING

                    refund = await PaymentService.refund_payment(
                        payment_intent_id=booking.stripe_payment_intent_id,
                        amount=refund_amount,
                        reason="requested_by_customer"
                        if cancelled_by == CancellationSource.CUSTOMER
                        else "fraudulent",
                    )

                    cancellation.stripe_refund_id = refund.id
                    cancellation.refund_status = RefundStatus.COMPLETED
                    cancellation.refund_processed_at = datetime.utcnow()

                    logger.info(
                        f"Refund processed for booking {booking_id}: ${refund_amount:.2f}",
                        extra={
                            "booking_id": str(booking_id),
                            "refund_id": refund.id,
                            "amount": refund_amount,
                        },
                    )

                except stripe.error.StripeError as e:
                    logger.error(
                        f"Stripe refund failed for booking {booking_id}: {e}",
                        exc_info=True,
                    )
                    cancellation.refund_status = RefundStatus.FAILED

            # Update booking status to CANCELLED
            try:
                await BookingStatusService.transition_status(
                    db=db,
                    booking_id=booking_id,
                    new_status=BookingStatus.CANCELLED,
                    transitioned_by_type="customer"
                    if cancelled_by == CancellationSource.CUSTOMER
                    else cancelled_by.value,
                    transitioned_by_name=cancelled_by_name,
                    notes=f"Cancellation: {reason}",
                )
            except Exception as e:
                logger.error(
                    f"Failed to update booking status to cancelled: {e}",
                    exc_info=True,
                )
                # Continue - cancellation record is created

            # Commit all changes
            await db.commit()
            await db.refresh(cancellation)

            logger.info(
                f"Booking {booking_id} cancelled by {cancelled_by.value}",
                extra={
                    "booking_id": str(booking_id),
                    "cancelled_by": cancelled_by.value,
                    "refund_amount": refund_amount,
                    "refund_percentage": refund_percentage,
                },
            )

            # Send notifications
            try:
                await CancellationService._send_cancellation_notifications(
                    booking=booking,
                    cancellation=cancellation,
                    refund_percentage=refund_percentage,
                )
            except Exception as e:
                logger.error(
                    f"Failed to send cancellation notifications: {e}",
                    exc_info=True,
                )

            return cancellation

    @staticmethod
    async def _send_cancellation_notifications(
        booking: Booking,
        cancellation: BookingCancellation,
        refund_percentage: int,
    ) -> None:
        """
        Send cancellation and refund notifications.

        Args:
            booking: Booking object
            cancellation: Cancellation record
            refund_percentage: Refund percentage
        """
        with tracer.start_as_current_span("cancellation.send_notifications"):
            notification_service = NotificationService()
            email_templates = EmailTemplates()
            sms_templates = SMSTemplates()

            # Prepare booking details
            booking_details = {
                "booking_id": str(booking.id),
                "customer_name": booking.customer_name,
                "move_date": booking.move_date.strftime("%B %d, %Y at %I:%M %p"),
                "pickup_address": booking.pickup_address,
                "dropoff_address": booking.dropoff_address,
                "estimated_amount": f"{booking.estimated_amount:.2f}",
            }

            # Prepare refund info
            if refund_percentage == 100:
                refund_message = "You will receive a full refund"
            elif refund_percentage > 0:
                refund_message = (
                    f"You will receive a {refund_percentage}% refund "
                    f"(${cancellation.refund_amount:.2f})"
                )
            else:
                refund_message = (
                    "No refund will be issued due to late cancellation "
                    "(less than 24 hours before move)"
                )

            refund_info = f"{refund_message}. Refunds are processed within 5-7 business days."

            # Send customer notification
            await notification_service.send_email(
                to_email=booking.customer_email,
                subject=f"Booking Cancelled - {booking.move_date.strftime('%B %d')}",
                html_content=email_templates.cancellation_confirmed(
                    customer_name=booking.customer_name,
                    booking_details=booking_details,
                    refund_info=refund_info,
                ),
            )

            await notification_service.send_sms(
                to_phone=booking.customer_phone,
                message=sms_templates.booking_cancelled(
                    customer_name=booking.customer_name,
                    move_date=booking.move_date.strftime("%b %d"),
                ),
            )

            # Notify mover organization if booking was confirmed/in-progress
            if booking.organization and booking.status in [
                BookingStatus.CONFIRMED,
                BookingStatus.IN_PROGRESS,
            ]:
                mover_email = booking.organization.contact_email
                mover_name = booking.organization.business_name

                await notification_service.send_email(
                    to_email=mover_email,
                    subject=f"Booking Cancelled - {booking.move_date.strftime('%B %d')}",
                    html_content=email_templates.cancellation_confirmed(
                        customer_name=mover_name,
                        booking_details=booking_details,
                        refund_info=f"Customer cancellation: {cancellation.cancellation_reason}",
                    ),
                )

            logger.info(f"Cancellation notifications sent for booking {booking.id}")

    @staticmethod
    async def get_refund_policy_info(
        original_amount: float,
        move_date: datetime,
    ) -> dict:
        """
        Get refund policy information for a given move date.

        Args:
            original_amount: Original booking amount
            move_date: Scheduled move date

        Returns:
            Dictionary with refund tiers and amounts
        """
        now = datetime.utcnow()
        hours_until_move = (move_date - now).total_seconds() / 3600
        hours_until_move = max(0, hours_until_move)

        current_refund_amount, current_percentage = (
            CancellationService.calculate_refund_amount(
                original_amount=original_amount,
                hours_before_move=hours_until_move,
            )
        )

        return {
            "current_refund": {
                "hours_before_move": round(hours_until_move, 1),
                "refund_percentage": current_percentage,
                "refund_amount": current_refund_amount,
            },
            "policy_tiers": [
                {
                    "min_hours": 72,
                    "refund_percentage": 100,
                    "refund_amount": original_amount,
                    "description": "Full refund - cancel 72+ hours before move",
                },
                {
                    "min_hours": 48,
                    "refund_percentage": 75,
                    "refund_amount": round(original_amount * 0.75, 2),
                    "description": "75% refund - cancel 48-72 hours before move",
                },
                {
                    "min_hours": 24,
                    "refund_percentage": 50,
                    "refund_amount": round(original_amount * 0.50, 2),
                    "description": "50% refund - cancel 24-48 hours before move",
                },
                {
                    "min_hours": 0,
                    "refund_percentage": 0,
                    "refund_amount": 0,
                    "description": "No refund - cancel less than 24 hours before move",
                },
            ],
        }

    @staticmethod
    async def process_failed_refunds(db: AsyncSession) -> int:
        """
        Retry failed refunds (for background job).

        Args:
            db: Database session

        Returns:
            Number of refunds successfully processed
        """
        with tracer.start_as_current_span("cancellation.retry_failed_refunds"):
            # Get failed refunds
            result = await db.execute(
                select(BookingCancellation)
                .where(BookingCancellation.refund_status == RefundStatus.FAILED)
                .where(BookingCancellation.refund_amount > 0)
            )
            failed_cancellations = result.scalars().all()

            processed_count = 0

            for cancellation in failed_cancellations:
                # Get booking
                booking_result = await db.execute(
                    select(Booking).where(Booking.id == cancellation.booking_id)
                )
                booking = booking_result.scalar_one_or_none()

                if not booking or not booking.stripe_payment_intent_id:
                    continue

                try:
                    cancellation.refund_status = RefundStatus.PROCESSING

                    refund = await PaymentService.refund_payment(
                        payment_intent_id=booking.stripe_payment_intent_id,
                        amount=cancellation.refund_amount,
                        reason="requested_by_customer",
                    )

                    cancellation.stripe_refund_id = refund.id
                    cancellation.refund_status = RefundStatus.COMPLETED
                    cancellation.refund_processed_at = datetime.utcnow()

                    processed_count += 1

                    logger.info(
                        f"Retried refund successful for booking {booking.id}",
                        extra={
                            "booking_id": str(booking.id),
                            "refund_id": refund.id,
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Retry refund failed for booking {booking.id}: {e}",
                        exc_info=True,
                    )
                    cancellation.refund_status = RefundStatus.FAILED

            await db.commit()

            return processed_count
