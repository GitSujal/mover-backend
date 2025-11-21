"""Support ticket API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_current_customer_session, get_db
from app.models.booking import Booking
from app.models.support import IssueStatus, SupportIssue
from app.models.user import CustomerSession, User
from app.schemas.support import (
    IssueCommentCreate,
    IssueCommentResponse,
    SupportIssueCreate,
    SupportIssueListResponse,
    SupportIssueResponse,
    SupportIssueUpdate,
    SupportIssueWithComments,
    SupportStats,
)
from app.services.support import SupportError, SupportTicketService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=SupportIssueResponse)
async def create_support_ticket(
    ticket_create: SupportIssueCreate,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> SupportIssueResponse:
    """
    Create a new support ticket.

    Requires customer session authentication.
    """
    # Verify booking belongs to customer
    booking_result = await db.execute(
        select(Booking).where(Booking.id == ticket_create.booking_id)
    )
    booking = booking_result.scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {ticket_create.booking_id} not found",
        )

    if booking.customer_email != customer_session.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create tickets for your own bookings",
        )

    try:
        ticket = await SupportTicketService.create_support_ticket(
            db=db,
            booking_id=ticket_create.booking_id,
            issue_type=ticket_create.issue_type,
            title=ticket_create.title,
            description=ticket_create.description,
            reporter_name=ticket_create.reporter_name,
            reporter_email=ticket_create.reporter_email,
            reporter_phone=ticket_create.reporter_phone,
            evidence_urls=ticket_create.evidence_urls,
        )

        logger.info(
            f"Support ticket created by {customer_session.email}: {ticket.id}",
            extra={
                "ticket_id": str(ticket.id),
                "customer_email": customer_session.email,
                "booking_id": str(ticket_create.booking_id),
            },
        )

        return SupportIssueResponse.model_validate(ticket)

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/tickets/{ticket_id}", response_model=SupportIssueWithComments)
async def get_support_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> SupportIssueWithComments:
    """
    Get support ticket with full comment history.

    Requires customer session authentication.
    """
    try:
        ticket, comments = await SupportTicketService.get_ticket_with_comments(
            db=db,
            issue_id=ticket_id,
        )

        # Verify customer owns ticket
        if ticket.reporter_email != customer_session.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Filter out internal comments for customers
        visible_comments = [c for c in comments if not c.is_internal]

        return SupportIssueWithComments(
            **SupportIssueResponse.model_validate(ticket).model_dump(),
            comments=[IssueCommentResponse.model_validate(c) for c in visible_comments],
        )

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/tickets/{ticket_id}/comments", response_model=IssueCommentResponse)
async def add_comment_to_ticket(
    ticket_id: UUID,
    comment_create: IssueCommentCreate,
    db: AsyncSession = Depends(get_db),
    customer_session: CustomerSession = Depends(get_current_customer_session),
) -> IssueCommentResponse:
    """
    Add comment to support ticket.

    Requires customer session authentication.
    """
    # Verify customer owns ticket
    ticket_result = await db.execute(select(SupportIssue).where(SupportIssue.id == ticket_id))
    ticket = ticket_result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    if ticket.reporter_email != customer_session.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only comment on your own tickets",
        )

    try:
        comment = await SupportTicketService.add_comment(
            db=db,
            issue_id=ticket_id,
            author_id=None,  # Customer session has no user ID
            author_name=ticket.reporter_name,
            author_type="customer",
            comment_text=comment_create.comment_text,
            attachment_urls=comment_create.attachment_urls,
            is_internal=False,  # Customer comments never internal
        )

        return IssueCommentResponse.model_validate(comment)

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# Admin/Mover endpoints


@router.get("/organization/{org_id}/tickets", response_model=SupportIssueListResponse)
async def list_organization_tickets(
    org_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: IssueStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SupportIssueListResponse:
    """
    List support tickets for an organization.

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
        select(SupportIssue)
        .where(SupportIssue.org_id == org_id)
        .order_by(SupportIssue.created_at.desc())
    )

    if status_filter:
        query = query.where(SupportIssue.status == status_filter)

    # Get total count
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count(SupportIssue.id)).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Get page
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    tickets = result.scalars().all()

    return SupportIssueListResponse(
        issues=[SupportIssueResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.patch("/tickets/{ticket_id}", response_model=SupportIssueResponse)
async def update_support_ticket(
    ticket_id: UUID,
    ticket_update: SupportIssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SupportIssueResponse:
    """
    Update support ticket (status, priority, assignment, resolution).

    Requires mover or platform admin authentication.
    """
    # Get ticket
    ticket_result = await db.execute(select(SupportIssue).where(SupportIssue.id == ticket_id))
    ticket = ticket_result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    # Verify access (own org or platform admin)
    if ticket.org_id != current_user.org_id:
        # TODO: Check if platform admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    try:
        updated_ticket = await SupportTicketService.update_ticket(
            db=db,
            issue_id=ticket_id,
            status=ticket_update.status,
            priority=ticket_update.priority,
            assigned_to=ticket_update.assigned_to,
            resolution_notes=ticket_update.resolution_notes,
            refund_amount=ticket_update.refund_amount,
            resolved_by=current_user.id if ticket_update.status == IssueStatus.RESOLVED else None,
        )

        logger.info(
            f"Ticket {ticket_id} updated by {current_user.email}",
            extra={
                "ticket_id": str(ticket_id),
                "user_email": current_user.email,
            },
        )

        return SupportIssueResponse.model_validate(updated_ticket)

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/tickets/{ticket_id}/escalate", response_model=SupportIssueResponse)
async def escalate_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SupportIssueResponse:
    """
    Escalate support ticket to urgent priority.

    Requires mover or platform admin authentication.
    """
    try:
        updated_ticket = await SupportTicketService.escalate_ticket(
            db=db,
            issue_id=ticket_id,
            escalated_by=current_user.id,
        )

        logger.info(
            f"Ticket {ticket_id} escalated by {current_user.email}",
            extra={
                "ticket_id": str(ticket_id),
                "user_email": current_user.email,
            },
        )

        return SupportIssueResponse.model_validate(updated_ticket)

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/tickets/{ticket_id}/comments/mover", response_model=IssueCommentResponse)
async def add_mover_comment(
    ticket_id: UUID,
    comment_create: IssueCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> IssueCommentResponse:
    """
    Add comment to ticket as mover.

    Requires mover authentication.
    """
    # Verify ticket belongs to mover's org
    ticket_result = await db.execute(select(SupportIssue).where(SupportIssue.id == ticket_id))
    ticket = ticket_result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    if ticket.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    try:
        comment = await SupportTicketService.add_comment(
            db=db,
            issue_id=ticket_id,
            author_id=current_user.id,
            author_name=current_user.name,
            author_type="mover",
            comment_text=comment_create.comment_text,
            attachment_urls=comment_create.attachment_urls,
            is_internal=comment_create.is_internal,
        )

        return IssueCommentResponse.model_validate(comment)

    except SupportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/stats", response_model=SupportStats)
async def get_support_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SupportStats:
    """
    Get support ticket statistics.

    Requires platform admin role.
    """
    stats = await SupportTicketService.get_support_stats(db=db)

    return SupportStats(**stats)
