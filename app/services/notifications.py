"""
Notification service for email and SMS.

Integrates with SendGrid (email) and Twilio (SMS).
"""

import logging
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To
from twilio.rest import Client as TwilioClient

from app.core.config import settings
from app.core.observability import tracer

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending email and SMS notifications."""

    def __init__(self) -> None:
        """Initialize notification clients."""
        # SendGrid client
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        else:
            self.sendgrid_client = None
            logger.warning("SendGrid API key not configured")

        # Twilio client
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            )
            self.twilio_phone = settings.TWILIO_PHONE_NUMBER
        else:
            self.twilio_client = None
            logger.warning("Twilio credentials not configured")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: str | None = None,
    ) -> bool:
        """
        Send email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text fallback

        Returns:
            True if sent successfully
        """
        with tracer.start_as_current_span("notification.send_email") as span:
            span.set_attribute("notification.type", "email")
            span.set_attribute("notification.recipient", to_email)

            if not self.sendgrid_client:
                logger.error("Cannot send email: SendGrid not configured")
                return False

            try:
                from_email = Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
                to = To(to_email)
                content = Content("text/html", html_content)

                mail = Mail(from_email, to, subject, content)

                # Add plain text version if provided
                if plain_content:
                    mail.add_content(Content("text/plain", plain_content))

                response = self.sendgrid_client.send(mail)

                if response.status_code in [200, 201, 202]:
                    logger.info(
                        f"Email sent to {to_email}: {subject}",
                        extra={"recipient": to_email, "subject": subject},
                    )
                    return True
                else:
                    logger.error(
                        f"Failed to send email: {response.status_code}",
                        extra={"status_code": response.status_code, "body": response.body},
                    )
                    return False

            except Exception as e:
                logger.error(f"Email sending error: {e}", exc_info=True)
                return False

    async def send_sms(self, to_phone: str, message: str) -> bool:
        """
        Send SMS via Twilio.

        Args:
            to_phone: Recipient phone number (E.164 format)
            message: SMS message text

        Returns:
            True if sent successfully
        """
        with tracer.start_as_current_span("notification.send_sms") as span:
            span.set_attribute("notification.type", "sms")
            span.set_attribute("notification.recipient", to_phone)

            if not self.twilio_client:
                logger.error("Cannot send SMS: Twilio not configured")
                return False

            try:
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_phone,
                    to=to_phone,
                )

                if message_obj.sid:
                    logger.info(
                        f"SMS sent to {to_phone}",
                        extra={"recipient": to_phone, "sid": message_obj.sid},
                    )
                    return True
                else:
                    logger.error("Failed to send SMS: No SID returned")
                    return False

            except Exception as e:
                logger.error(f"SMS sending error: {e}", exc_info=True)
                return False

    async def send_booking_confirmation_email(
        self,
        customer_email: str,
        customer_name: str,
        booking_details: dict[str, Any],
    ) -> bool:
        """
        Send booking confirmation email to customer.

        Args:
            customer_email: Customer email
            customer_name: Customer name
            booking_details: Booking information

        Returns:
            True if sent successfully
        """
        subject = f"Booking Confirmation - {booking_details.get('move_date')}"

        html_content = f"""
        <html>
        <body>
            <h2>Booking Confirmed!</h2>
            <p>Dear {customer_name},</p>
            <p>Your move has been confirmed for {booking_details.get('move_date')}.</p>

            <h3>Details:</h3>
            <ul>
                <li><strong>Pickup:</strong> {booking_details.get('pickup_address')}</li>
                <li><strong>Dropoff:</strong> {booking_details.get('dropoff_address')}</li>
                <li><strong>Estimated Cost:</strong> ${booking_details.get('estimated_amount')}</li>
            </ul>

            <p>We'll send you reminders as your move date approaches.</p>

            <p>Thank you for choosing MoveHub!</p>
        </body>
        </html>
        """

        return await self.send_email(customer_email, subject, html_content)

    async def send_otp_email(self, email: str, otp_code: str) -> bool:
        """
        Send OTP verification code via email.

        Args:
            email: Recipient email
            otp_code: 6-digit OTP code

        Returns:
            True if sent successfully
        """
        subject = "Your MoveHub Verification Code"

        html_content = f"""
        <html>
        <body>
            <h2>Verification Code</h2>
            <p>Your verification code is:</p>
            <h1 style="font-size: 32px; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code expires in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </body>
        </html>
        """

        return await self.send_email(email, subject, html_content)

    async def send_otp_sms(self, phone: str, otp_code: str) -> bool:
        """
        Send OTP verification code via SMS.

        Args:
            phone: Recipient phone number
            otp_code: 6-digit OTP code

        Returns:
            True if sent successfully
        """
        message = f"Your MoveHub verification code is: {otp_code}. Valid for 10 minutes."
        return await self.send_sms(phone, message)
