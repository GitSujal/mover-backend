"""Booking status transition service with notification integration."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking, BookingStatus
from app.models.booking_status_history import BookingStatusHistory
from app.models.user import User
from app.services.notification_templates import EmailTemplates, SMSTemplates
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class InvalidStatusTransitionError(Exception):
    """Raised when attempting an invalid status transition."""

    pass


class BookingNotFoundError(Exception):
    """Raised when booking doesn't exist."""

    pass


class BookingStatusService:
    """Service for managing booking status transitions and notifications."""

    # Define valid state machine transitions
    VALID_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
        BookingStatus.PENDING: {
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
        },
        BookingStatus.CONFIRMED: {
            BookingStatus.IN_PROGRESS,
            BookingStatus.CANCELLED,
        },
        BookingStatus.IN_PROGRESS: {
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
        },
        BookingStatus.COMPLETED: set(),  # Terminal state
        BookingStatus.CANCELLED: set(),  # Terminal state
    }

    @staticmethod
    def is_valid_transition(
        current_status: BookingStatus,
        new_status: BookingStatus,
    ) -> bool:
        """
        Check if status transition is valid.

        Args:
            current_status: Current booking status
            new_status: Target status

        Returns:
            True if transition is allowed
        """
        if current_status == new_status:
            return False  # No transition needed

        valid_next_statuses = BookingStatusService.VALID_TRANSITIONS.get(current_status, set())
        return new_status in valid_next_statuses

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        booking_id: UUID,
        new_status: BookingStatus,
        transitioned_by: User | None = None,
        transitioned_by_type: str = "system",
        transitioned_by_name: str = "System",
        notes: str | None = None,
    ) -> Booking:
        """
        Transition booking to new status with validation and notifications.

        Args:
            db: Database session
            booking_id: Booking ID
            new_status: Target status
            transitioned_by: User performing transition (if applicable)
            transitioned_by_type: Type of actor ('system', 'customer', 'mover', 'platform_admin')
            transitioned_by_name: Name of actor for audit trail
            notes: Optional notes about transition

        Returns:
            Updated booking

        Raises:
            BookingNotFoundError: If booking doesn't exist
            InvalidStatusTransitionError: If transition is not valid
        """
        with tracer.start_as_current_span("booking_status.transition") as span:
            span.set_attribute("booking_id", str(booking_id))
            span.set_attribute("new_status", new_status.value)

            # Fetch booking
            result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalar_one_or_none()

            if not booking:
                raise BookingNotFoundError(f"Booking {booking_id} not found")

            old_status = booking.status
            span.set_attribute("old_status", old_status.value)

            # Validate transition
            if not BookingStatusService.is_valid_transition(old_status, new_status):
                raise InvalidStatusTransitionError(
                    f"Cannot transition from {old_status.value} to {new_status.value}"
                )

            # Update booking status
            booking.status = new_status

            # Create history entry
            history = BookingStatusHistory(
                booking_id=booking_id,
                from_status=old_status,
                to_status=new_status,
                transitioned_by_id=transitioned_by.id if transitioned_by else None,
                transitioned_by_name=transitioned_by_name,
                transitioned_by_type=transitioned_by_type,
                notes=notes,
                transitioned_at=datetime.utcnow(),
            )
            db.add(history)

            # Commit changes
            await db.commit()
            await db.refresh(booking)

            logger.info(
                f"Booking {booking_id} transitioned from {old_status.value} to {new_status.value}",
                extra={
                    "booking_id": str(booking_id),
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "transitioned_by": transitioned_by_name,
                },
            )

            # Send notifications asynchronously (don't block)
            try:
                await BookingStatusService._send_status_notifications(
                    booking=booking,
                    old_status=old_status,
                    new_status=new_status,
                )
            except Exception as e:
                # Log notification errors but don't fail the transition
                logger.error(
                    f"Failed to send notifications for booking {booking_id}: {e}",
                    exc_info=True,
                )

            return booking

    @staticmethod
    async def _send_status_notifications(
        booking: Booking,
        old_status: BookingStatus,
        new_status: BookingStatus,
    ) -> None:
        """
        Send appropriate notifications based on status transition.

        Args:
            booking: Booking object
            old_status: Previous status
            new_status: New status
        """
        with tracer.start_as_current_span("booking_status.send_notifications"):
            notification_service = NotificationService()
            email_templates = EmailTemplates()
            sms_templates = SMSTemplates()

            # Prepare booking details for templates
            booking_details: dict[str, Any] = {
                "booking_id": str(booking.id),
                "customer_name": booking.customer_name,
                "move_date": booking.move_date.strftime("%B %d, %Y at %I:%M %p"),
                "pickup_address": booking.pickup_address,
                "dropoff_address": booking.dropoff_address,
                "estimated_amount": f"{booking.estimated_amount:.2f}",
                "truck_name": getattr(booking.truck, "name", "N/A"),
                "driver_name": getattr(booking.driver, "name", "Not yet assigned"),
            }

            # Get mover details if organization is loaded
            mover_email = None
            mover_name = "Moving Company"
            if booking.organization:
                mover_email = booking.organization.contact_email
                mover_name = booking.organization.business_name

            # Send notifications based on transition
            if new_status == BookingStatus.CONFIRMED:
                # Confirmed: Send to both customer and mover
                subject, html_content = email_templates.booking_confirmed_customer(booking_details)
                await notification_service.send_email(
                    to_email=booking.customer_email,
                    subject=subject,
                    html_content=html_content,
                )

                sms_data = {
                    "customer_name": booking.customer_name,
                    "move_date": booking.move_date.strftime("%b %d"),
                    "mover_name": mover_name,
                    "short_url": f"https://mv.hb/b/{str(booking.id)[:8]}",
                }
                await notification_service.send_sms(
                    to_phone=booking.customer_phone,
                    message=sms_templates.booking_confirmed(sms_data),
                )

                if mover_email:
                    subject, html_content = email_templates.booking_confirmed_mover(booking_details)
                    await notification_service.send_email(
                        to_email=mover_email,
                        subject=subject,
                        html_content=html_content,
                    )

            elif new_status == BookingStatus.IN_PROGRESS:
                # Driver arrived: Notify customer
                arrived_data = {
                    "customer_name": booking.customer_name,
                    "driver_name": booking_details["driver_name"],
                    "driver_phone": getattr(booking.driver, "phone", "N/A"),
                    "truck_info": booking_details["truck_name"],
                }

                subject, html_content = email_templates.driver_arrived(arrived_data)
                await notification_service.send_email(
                    to_email=booking.customer_email,
                    subject=subject,
                    html_content=html_content,
                )

                await notification_service.send_sms(
                    to_phone=booking.customer_phone,
                    message=sms_templates.driver_arrived(arrived_data),
                )

            elif new_status == BookingStatus.COMPLETED:
                # Job completed: Send to customer with rating request
                completed_data = {
                    "customer_name": booking.customer_name,
                    "completed_at": datetime.utcnow().strftime("%I:%M %p"),
                    "actual_duration": "N/A",  # TODO: Calculate actual duration
                    "rating_url": f"https://movehub.com/bookings/{booking.id}/rate",
                }

                subject, html_content = email_templates.job_completed(completed_data)
                await notification_service.send_email(
                    to_email=booking.customer_email,
                    subject=subject,
                    html_content=html_content,
                )

                await notification_service.send_sms(
                    to_phone=booking.customer_phone,
                    message=sms_templates.move_completed(completed_data),
                )

            elif new_status == BookingStatus.CANCELLED:
                # Cancellation: Notify both parties
                cancel_data = {
                    "customer_name": booking.customer_name,
                    "move_date": booking.move_date.strftime("%B %d, %Y"),
                    "original_amount": float(booking.estimated_amount),
                    "refund_amount": 0.0,  # TODO: Get actual refund amount
                    "cancellation_reason": "Cancelled via status update",
                    "refund_processing_time": "5-7 business days",
                    "rebook_url": f"https://movehub.com/book?retry={booking.id}",
                    "offer_rebook": True,
                    "short_url": f"https://mv.hb/c/{str(booking.id)[:8]}",
                }

                subject, html_content = email_templates.cancellation_confirmed(cancel_data)
                await notification_service.send_email(
                    to_email=booking.customer_email,
                    subject=subject,
                    html_content=html_content,
                )

                await notification_service.send_sms(
                    to_phone=booking.customer_phone,
                    message=sms_templates.cancellation_confirmed(cancel_data),
                )

                if mover_email:
                    mover_cancel_data = cancel_data.copy()
                    mover_cancel_data["customer_name"] = mover_name

                    subject, html_content = email_templates.cancellation_confirmed(
                        mover_cancel_data
                    )
                    await notification_service.send_email(
                        to_email=mover_email,
                        subject=subject,
                        html_content=html_content,
                    )

            logger.info(
                f"Notifications sent for booking {booking.id} status change to {new_status.value}"
            )

    @staticmethod
    async def get_status_history(
        db: AsyncSession,
        booking_id: UUID,
    ) -> list[BookingStatusHistory]:
        """
        Get complete status transition history for a booking.

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            List of status history entries, ordered by transition time
        """
        with tracer.start_as_current_span("booking_status.get_history"):
            result = await db.execute(
                select(BookingStatusHistory)
                .where(BookingStatusHistory.booking_id == booking_id)
                .order_by(BookingStatusHistory.transitioned_at.asc())
            )
            return list(result.scalars().all())

    @staticmethod
    async def auto_confirm_booking(
        db: AsyncSession,
        booking_id: UUID,
    ) -> Booking:
        """
        Auto-confirm a pending booking (typically after payment).

        Args:
            db: Database session
            booking_id: Booking ID

        Returns:
            Updated booking
        """
        return await BookingStatusService.transition_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.CONFIRMED,
            transitioned_by_type="system",
            transitioned_by_name="Auto-Confirm System",
            notes="Automatically confirmed after payment",
        )

    @staticmethod
    async def mark_in_progress(
        db: AsyncSession,
        booking_id: UUID,
        driver_user: User,
    ) -> Booking:
        """
        Mark booking as in-progress (driver arrived).

        Args:
            db: Database session
            booking_id: Booking ID
            driver_user: Driver user performing the action

        Returns:
            Updated booking
        """
        return await BookingStatusService.transition_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.IN_PROGRESS,
            transitioned_by=driver_user,
            transitioned_by_type="mover",
            transitioned_by_name=driver_user.name,
            notes="Driver marked as arrived on-site",
        )

    @staticmethod
    async def mark_completed(
        db: AsyncSession,
        booking_id: UUID,
        driver_user: User,
    ) -> Booking:
        """
        Mark booking as completed.

        Args:
            db: Database session
            booking_id: Booking ID
            driver_user: Driver user performing the action

        Returns:
            Updated booking
        """
        return await BookingStatusService.transition_status(
            db=db,
            booking_id=booking_id,
            new_status=BookingStatus.COMPLETED,
            transitioned_by=driver_user,
            transitioned_by_type="mover",
            transitioned_by_name=driver_user.name,
            notes="Job completed by driver",
        )
