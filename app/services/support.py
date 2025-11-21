"""Support ticket service."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import tracer
from app.models.booking import Booking
from app.models.support import IssueComment, IssueStatus, IssuePriority, IssueType, SupportIssue
from app.models.user import User
from app.services.notification_templates import EmailTemplates
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class SupportError(Exception):
    """Base exception for support ticket errors."""

    pass


class SupportTicketService:
    """Service for support ticket management."""

    @staticmethod
    async def create_support_ticket(
        db: AsyncSession,
        booking_id: UUID,
        issue_type: IssueType,
        title: str,
        description: str,
        reporter_name: str,
        reporter_email: str,
        reporter_phone: str | None = None,
        evidence_urls: list[str] | None = None,
        priority: IssuePriority = IssuePriority.MEDIUM,
    ) -> SupportIssue:
        """
        Create a new support ticket.

        Args:
            db: Database session
            booking_id: Related booking ID
            issue_type: Type of issue
            title: Issue title
            description: Detailed description
            reporter_name: Name of person reporting
            reporter_email: Email of reporter
            reporter_phone: Optional phone
            evidence_urls: Optional evidence URLs
            priority: Issue priority

        Returns:
            Created support ticket
        """
        with tracer.start_as_current_span("support.create_ticket") as span:
            span.set_attribute("booking_id", str(booking_id))
            span.set_attribute("issue_type", issue_type.value)

            # Get booking to get org_id
            result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalar_one_or_none()

            if not booking:
                raise SupportError(f"Booking {booking_id} not found")

            # Auto-escalate certain issue types
            if issue_type in [IssueType.DAMAGE, IssueType.RUDE_BEHAVIOR]:
                priority = IssuePriority.HIGH

            # Create ticket
            ticket = SupportIssue(
                booking_id=booking_id,
                org_id=booking.org_id,
                issue_type=issue_type,
                priority=priority,
                status=IssueStatus.OPEN,
                title=title,
                description=description,
                evidence_urls=evidence_urls or [],
                reporter_name=reporter_name,
                reporter_email=reporter_email,
                reporter_phone=reporter_phone,
            )

            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)

            logger.info(
                f"Support ticket created: {ticket.id} for booking {booking_id}",
                extra={
                    "ticket_id": str(ticket.id),
                    "booking_id": str(booking_id),
                    "issue_type": issue_type.value,
                    "priority": priority.value,
                },
            )

            # Send notifications
            try:
                await SupportTicketService._send_ticket_created_notifications(
                    db=db,
                    ticket=ticket,
                    booking=booking,
                )
            except Exception as e:
                logger.error(f"Failed to send ticket creation notifications: {e}")

            return ticket

    @staticmethod
    async def _send_ticket_created_notifications(
        db: AsyncSession,
        ticket: SupportIssue,
        booking: Booking,
    ) -> None:
        """Send notifications when ticket is created."""
        notification_service = NotificationService()
        email_templates = EmailTemplates()

        # Notify customer
        await notification_service.send_email(
            to_email=ticket.reporter_email,
            subject=f"Support Ticket Created - #{ticket.id}",
            html_content=email_templates.support_ticket_created(
                customer_name=ticket.reporter_name,
                ticket_id=str(ticket.id),
                issue_type=ticket.issue_type.value,
                description=ticket.description,
            ),
        )

        # Notify mover organization
        if booking.organization:
            await notification_service.send_email(
                to_email=booking.organization.contact_email,
                subject=f"New Support Ticket - #{ticket.id}",
                html_content=email_templates.support_ticket_created(
                    customer_name=booking.organization.business_name,
                    ticket_id=str(ticket.id),
                    issue_type=ticket.issue_type.value,
                    description=ticket.description,
                ),
            )

    @staticmethod
    async def add_comment(
        db: AsyncSession,
        issue_id: UUID,
        author_id: UUID | None,
        author_name: str,
        author_type: str,
        comment_text: str,
        attachment_urls: list[str] | None = None,
        is_internal: bool = False,
    ) -> IssueComment:
        """
        Add comment to support ticket.

        Args:
            db: Database session
            issue_id: Ticket ID
            author_id: User ID if authenticated
            author_name: Name of commenter
            author_type: 'customer', 'mover', or 'platform'
            comment_text: Comment text
            attachment_urls: Optional attachments
            is_internal: Internal comment (platform only)

        Returns:
            Created comment
        """
        with tracer.start_as_current_span("support.add_comment"):
            # Verify ticket exists
            result = await db.execute(select(SupportIssue).where(SupportIssue.id == issue_id))
            ticket = result.scalar_one_or_none()

            if not ticket:
                raise SupportError(f"Support ticket {issue_id} not found")

            # Create comment
            comment = IssueComment(
                issue_id=issue_id,
                author_id=author_id,
                author_name=author_name,
                author_type=author_type,
                comment_text=comment_text,
                attachment_urls=attachment_urls or [],
                is_internal=is_internal,
            )

            db.add(comment)
            await db.commit()
            await db.refresh(comment)

            logger.info(
                f"Comment added to ticket {issue_id} by {author_name}",
                extra={
                    "ticket_id": str(issue_id),
                    "author_name": author_name,
                    "author_type": author_type,
                },
            )

            return comment

    @staticmethod
    async def update_ticket(
        db: AsyncSession,
        issue_id: UUID,
        status: IssueStatus | None = None,
        priority: IssuePriority | None = None,
        assigned_to: UUID | None = None,
        resolution_notes: str | None = None,
        refund_amount: float | None = None,
        resolved_by: UUID | None = None,
    ) -> SupportIssue:
        """
        Update support ticket.

        Args:
            db: Database session
            issue_id: Ticket ID
            status: New status
            priority: New priority
            assigned_to: Assign to user
            resolution_notes: Resolution notes
            refund_amount: Refund amount if applicable
            resolved_by: User resolving ticket

        Returns:
            Updated ticket
        """
        with tracer.start_as_current_span("support.update_ticket"):
            result = await db.execute(select(SupportIssue).where(SupportIssue.id == issue_id))
            ticket = result.scalar_one_or_none()

            if not ticket:
                raise SupportError(f"Support ticket {issue_id} not found")

            old_status = ticket.status

            # Update fields
            if status is not None:
                ticket.status = status
                if status == IssueStatus.RESOLVED:
                    ticket.resolved_at = datetime.utcnow().isoformat()
                    ticket.resolved_by = resolved_by

            if priority is not None:
                ticket.priority = priority

            if assigned_to is not None:
                ticket.assigned_to = assigned_to

            if resolution_notes is not None:
                ticket.resolution_notes = resolution_notes

            if refund_amount is not None:
                ticket.refund_amount = refund_amount
                ticket.refund_issued_at = datetime.utcnow().isoformat()

            await db.commit()
            await db.refresh(ticket)

            logger.info(
                f"Ticket {issue_id} updated from {old_status.value} to {ticket.status.value}",
                extra={
                    "ticket_id": str(issue_id),
                    "old_status": old_status.value,
                    "new_status": ticket.status.value,
                },
            )

            # Send notification if resolved
            if status == IssueStatus.RESOLVED and old_status != IssueStatus.RESOLVED:
                try:
                    await SupportTicketService._send_resolution_notification(db=db, ticket=ticket)
                except Exception as e:
                    logger.error(f"Failed to send resolution notification: {e}")

            return ticket

    @staticmethod
    async def _send_resolution_notification(
        db: AsyncSession,
        ticket: SupportIssue,
    ) -> None:
        """Send notification when ticket is resolved."""
        notification_service = NotificationService()

        resolution_message = ticket.resolution_notes or "Your issue has been resolved."

        # Simple email (would use template in production)
        html_content = f"""
        <html>
        <body>
            <h2>Support Ticket Resolved</h2>
            <p>Dear {ticket.reporter_name},</p>
            <p>Your support ticket has been resolved.</p>
            <p><strong>Ticket ID:</strong> {ticket.id}</p>
            <p><strong>Issue Type:</strong> {ticket.issue_type.value}</p>
            <p><strong>Resolution:</strong> {resolution_message}</p>
            {f'<p><strong>Refund Amount:</strong> ${ticket.refund_amount:.2f}</p>' if ticket.refund_amount else ''}
            <p>Thank you for your patience.</p>
        </body>
        </html>
        """

        await notification_service.send_email(
            to_email=ticket.reporter_email,
            subject=f"Support Ticket Resolved - #{ticket.id}",
            html_content=html_content,
        )

    @staticmethod
    async def escalate_ticket(
        db: AsyncSession,
        issue_id: UUID,
        escalated_by: UUID,
    ) -> SupportIssue:
        """
        Escalate support ticket to higher priority.

        Args:
            db: Database session
            issue_id: Ticket ID
            escalated_by: User escalating

        Returns:
            Updated ticket
        """
        return await SupportTicketService.update_ticket(
            db=db,
            issue_id=issue_id,
            status=IssueStatus.ESCALATED,
            priority=IssuePriority.URGENT,
        )

    @staticmethod
    async def get_ticket_with_comments(
        db: AsyncSession,
        issue_id: UUID,
    ) -> tuple[SupportIssue, list[IssueComment]]:
        """
        Get ticket with full comment history.

        Args:
            db: Database session
            issue_id: Ticket ID

        Returns:
            Tuple of (ticket, comments)
        """
        # Get ticket
        ticket_result = await db.execute(select(SupportIssue).where(SupportIssue.id == issue_id))
        ticket = ticket_result.scalar_one_or_none()

        if not ticket:
            raise SupportError(f"Support ticket {issue_id} not found")

        # Get comments
        comments_result = await db.execute(
            select(IssueComment)
            .where(IssueComment.issue_id == issue_id)
            .order_by(IssueComment.created_at.asc())
        )
        comments = list(comments_result.scalars().all())

        return ticket, comments

    @staticmethod
    async def get_support_stats(db: AsyncSession) -> dict:
        """
        Get support ticket statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        with tracer.start_as_current_span("support.get_stats"):
            # Get counts by status
            open_result = await db.execute(
                select(func.count(SupportIssue.id)).where(SupportIssue.status == IssueStatus.OPEN)
            )
            total_open = open_result.scalar_one()

            in_progress_result = await db.execute(
                select(func.count(SupportIssue.id)).where(
                    SupportIssue.status == IssueStatus.IN_PROGRESS
                )
            )
            total_in_progress = in_progress_result.scalar_one()

            resolved_result = await db.execute(
                select(func.count(SupportIssue.id)).where(SupportIssue.status == IssueStatus.RESOLVED)
            )
            total_resolved = resolved_result.scalar_one()

            escalated_result = await db.execute(
                select(func.count(SupportIssue.id)).where(
                    SupportIssue.status == IssueStatus.ESCALATED
                )
            )
            total_escalated = escalated_result.scalar_one()

            # Get total refunds
            refund_result = await db.execute(
                select(func.sum(SupportIssue.refund_amount)).where(
                    SupportIssue.refund_amount.isnot(None)
                )
            )
            total_refunds = refund_result.scalar_one() or 0.0

            # TODO: Calculate average resolution time

            return {
                "total_open": total_open,
                "total_in_progress": total_in_progress,
                "total_resolved": total_resolved,
                "total_escalated": total_escalated,
                "average_resolution_time_hours": None,  # TODO
                "total_refunds_issued": float(total_refunds),
            }
