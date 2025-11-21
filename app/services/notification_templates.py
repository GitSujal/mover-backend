"""
Comprehensive notification templates for all workflow events.

Provides HTML email templates and SMS messages for customer and mover notifications.
"""

from typing import Any


class EmailTemplates:
    """HTML email templates for all workflow events."""

    @staticmethod
    def booking_confirmed_customer(data: dict[str, Any]) -> tuple[str, str]:
        """Email to customer when booking is confirmed."""
        subject = f"Move Confirmed - {data['move_date']}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9fafb; padding: 20px; }}
                .details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .detail-row {{ display: flex; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
                .detail-label {{ font-weight: bold; width: 150px; }}
                .button {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Move Confirmed!</h1>
                </div>
                <div class="content">
                    <p>Hi {data['customer_name']},</p>
                    <p>Great news! Your move has been confirmed.</p>

                    <div class="details">
                        <h3>Move Details</h3>
                        <div class="detail-row">
                            <div class="detail-label">Date & Time:</div>
                            <div>{data['move_date']}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">From:</div>
                            <div>{data['pickup_address']}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">To:</div>
                            <div>{data['dropoff_address']}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Estimated Cost:</div>
                            <div>${data['estimated_amount']:.2f}</div>
                        </div>
                    </div>

                    <div class="details">
                        <h3>Your Moving Company</h3>
                        <div class="detail-row">
                            <div class="detail-label">Company:</div>
                            <div>{data['mover_name']}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Driver:</div>
                            <div>{data.get('driver_name', 'Will be assigned')}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Contact:</div>
                            <div>{data.get('mover_phone', 'Available in app')}</div>
                        </div>
                    </div>

                    <p style="text-align: center; margin: 20px 0;">
                        <a href="{data['booking_url']}" class="button">View Booking Details</a>
                    </p>

                    <p>We'll send you reminders as your move date approaches.</p>
                    <p><strong>Need to make changes?</strong> Contact us at least 24 hours before your move.</p>
                </div>
                <div class="footer">
                    <p>© 2025 MoveHub. All rights reserved.</p>
                    <p>Have questions? Reply to this email or visit our help center.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def booking_confirmed_mover(data: dict[str, Any]) -> tuple[str, str]:
        """Email to mover when new booking is received."""
        subject = f"New Move Booking - {data['move_date']}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">🚚 New Move Booking</h2>
                <p>You have a new booking request!</p>

                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>Customer Information</h3>
                    <p><strong>Name:</strong> {data['customer_name']}</p>
                    <p><strong>Phone:</strong> {data['customer_phone']}</p>
                    <p><strong>Email:</strong> {data['customer_email']}</p>
                </div>

                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>Move Details</h3>
                    <p><strong>Date:</strong> {data['move_date']}</p>
                    <p><strong>Pickup:</strong> {data['pickup_address']}</p>
                    <p><strong>Dropoff:</strong> {data['dropoff_address']}</p>
                    <p><strong>Distance:</strong> {data['estimated_distance']} miles</p>
                    <p><strong>Estimated Duration:</strong> {data['estimated_duration']} hours</p>
                    <p><strong>Special Items:</strong> {data.get('special_items', 'None')}</p>
                </div>

                <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Customer Notes:</strong></p>
                    <p>{data.get('customer_notes', 'No special instructions')}</p>
                </div>

                <p style="text-align: center;">
                    <a href="{data['dashboard_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View in Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def driver_arrived(data: dict[str, Any]) -> tuple[str, str]:
        """Email to customer when driver arrives at pickup location."""
        subject = "Your Mover Has Arrived!"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #16a34a;">✅ Your Mover Has Arrived</h2>
                <p>Hi {data['customer_name']},</p>
                <p style="font-size: 18px;"><strong>{data['driver_name']}</strong> has arrived at your pickup location.</p>

                <div style="background: #f0fdf4; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #16a34a;">
                    <p><strong>Driver:</strong> {data['driver_name']}</p>
                    <p><strong>Truck:</strong> {data['truck_info']}</p>
                    <p><strong>Contact:</strong> {data['driver_phone']}</p>
                </div>

                <p>Your belongings will be loaded shortly. Please ensure everything is ready to go!</p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def job_completed(data: dict[str, Any]) -> tuple[str, str]:
        """Email to customer when move is completed."""
        subject = "Move Completed - Please Rate Your Experience"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">🎉 Move Completed Successfully!</h2>
                <p>Hi {data['customer_name']},</p>
                <p>Your move has been completed. We hope everything went smoothly!</p>

                <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>Move Summary</h3>
                    <p><strong>Completed:</strong> {data['completed_at']}</p>
                    <p><strong>Duration:</strong> {data['actual_duration']} hours</p>
                </div>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{data['rating_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Rate Your Experience
                    </a>
                </p>

                <p style="font-size: 14px; color: #6b7280;">
                    Your feedback helps other customers make informed decisions and helps us maintain quality service.
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def invoice_sent(data: dict[str, Any]) -> tuple[str, str]:
        """Email to customer with invoice."""
        subject = f"Invoice #{data['invoice_number']} - Your Move"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Invoice Ready</h2>
                <p>Hi {data['customer_name']},</p>
                <p>Your invoice is ready for review.</p>

                <div style="background: #f3f4f6; padding: 20px; border-radius: 5px; margin: 15px 0;">
                    <h3>Invoice Summary</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 8px 0;"><strong>Invoice #:</strong></td>
                            <td style="text-align: right;">{data['invoice_number']}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 8px 0;"><strong>Date:</strong></td>
                            <td style="text-align: right;">{data['invoice_date']}</td>
                        </tr>
                        <tr style="border-bottom: 2px solid #2563eb;">
                            <td style="padding: 8px 0;"><strong>Total Amount:</strong></td>
                            <td style="text-align: right; font-size: 18px; font-weight: bold;">${data['total_amount']:.2f}</td>
                        </tr>
                    </table>
                </div>

                <p style="text-align: center;">
                    <a href="{data['invoice_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View & Pay Invoice
                    </a>
                </p>

                <p style="font-size: 14px; color: #6b7280;">
                    Payment methods: Credit Card, Bank Transfer, or Cash
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def insurance_expiring(data: dict[str, Any]) -> tuple[str, str]:
        """Email to mover when insurance is expiring soon."""
        subject = f"⚠️ Insurance Expiring in {data['days_remaining']} Days"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">⚠️ Action Required: Insurance Renewal</h2>
                <p>Hi {data['organization_name']},</p>
                <p>Your <strong>{data['insurance_type']}</strong> is expiring soon.</p>

                <div style="background: #fef2f2; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc2626;">
                    <p><strong>Policy Type:</strong> {data['insurance_type']}</p>
                    <p><strong>Expires:</strong> {data['expiry_date']}</p>
                    <p><strong>Days Remaining:</strong> {data['days_remaining']}</p>
                </div>

                <p><strong>Important:</strong> Your account will be suspended if insurance expires.</p>

                <p style="text-align: center;">
                    <a href="{data['upload_url']}"
                       style="background: #dc2626; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Upload Renewal Document
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def cancellation_confirmed(data: dict[str, Any]) -> tuple[str, str]:
        """Email confirming booking cancellation and refund details."""
        subject = "Booking Cancelled - Refund Information"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Booking Cancellation Confirmed</h2>
                <p>Hi {data['customer_name']},</p>
                <p>Your booking for {data['move_date']} has been cancelled.</p>

                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>Refund Information</h3>
                    <p><strong>Original Amount:</strong> ${data['original_amount']:.2f}</p>
                    <p><strong>Refund Amount:</strong> ${data['refund_amount']:.2f}</p>
                    <p><strong>Reason:</strong> {data['cancellation_reason']}</p>
                </div>

                {f'''
                <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Processing Time:</strong> {data.get('refund_processing_time', '5-7 business days')}</p>
                    <p>The refund will be credited to your original payment method.</p>
                </div>
                ''' if data['refund_amount'] > 0 else ''}

                {f'''
                <p style="text-align: center; margin: 20px 0;">
                    <a href="{data['rebook_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Book a New Move
                    </a>
                </p>
                ''' if data.get('offer_rebook') else ''}
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def rating_received_mover(data: dict[str, Any]) -> tuple[str, str]:
        """Email to mover when they receive a new rating."""
        subject = f"New {data['overall_rating']}★ Rating Received"

        stars = "⭐" * data["overall_rating"]
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>📝 New Customer Rating</h2>
                <p>You've received a new rating!</p>

                <div style="background: #f0f9ff; padding: 20px; border-radius: 5px; margin: 15px 0; text-align: center;">
                    <div style="font-size: 48px;">{stars}</div>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">{data['overall_rating']}.0 / 5.0</p>
                </div>

                {f'''
                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p style="font-style: italic;">"{data['review_text']}"</p>
                    <p style="text-align: right; color: #6b7280;">- {data['customer_name']}</p>
                </div>
                ''' if data.get('review_text') else ''}

                <p style="text-align: center;">
                    <a href="{data['rating_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Respond to Review
                    </a>
                </p>

                <p style="font-size: 14px; color: #6b7280;">
                    Responding to reviews shows professionalism and helps build trust with future customers.
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html

    @staticmethod
    def support_ticket_created(data: dict[str, Any]) -> tuple[str, str]:
        """Email confirming support ticket creation."""
        subject = f"Support Ticket #{data['ticket_number']} Created"

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Support Ticket Created</h2>
                <p>Hi {data['reporter_name']},</p>
                <p>We've received your support request and are looking into it.</p>

                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Ticket #:</strong> {data['ticket_number']}</p>
                    <p><strong>Type:</strong> {data['issue_type']}</p>
                    <p><strong>Priority:</strong> {data['priority']}</p>
                    <p><strong>Status:</strong> {data['status']}</p>
                </div>

                <div style="background: #fffbeb; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Your Report:</strong></p>
                    <p>{data['description']}</p>
                </div>

                <p><strong>What happens next?</strong></p>
                <ul>
                    <li>Our team will review your case within 24 hours</li>
                    <li>We'll reach out if we need more information</li>
                    <li>You'll receive updates via email</li>
                </ul>

                <p style="text-align: center;">
                    <a href="{data['ticket_url']}"
                       style="background: #2563eb; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Ticket Status
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        return subject, html


class SMSTemplates:
    """SMS templates for critical notifications."""

    @staticmethod
    def booking_confirmed(data: dict[str, Any]) -> str:
        """SMS confirmation of booking."""
        return (
            f"MoveHub: Your move is confirmed for {data['move_date']}. "
            f"Mover: {data['mover_name']}. View details: {data['short_url']}"
        )

    @staticmethod
    def driver_arrived(data: dict[str, Any]) -> str:
        """SMS when driver arrives."""
        return (
            f"MoveHub: Your mover {data['driver_name']} has arrived at your pickup location. "
            f"Contact: {data['driver_phone']}"
        )

    @staticmethod
    def move_completed(data: dict[str, Any]) -> str:
        """SMS when move is completed."""
        return f"MoveHub: Your move is complete! Please rate your experience: {data['rating_url']}"

    @staticmethod
    def cancellation_confirmed(data: dict[str, Any]) -> str:
        """SMS confirming cancellation."""
        return (
            f"MoveHub: Your booking for {data['move_date']} has been cancelled. "
            f"Refund: ${data['refund_amount']:.2f}. Details: {data['short_url']}"
        )

    @staticmethod
    def otp_code(data: dict[str, Any]) -> str:
        """OTP verification code."""
        return f"Your MoveHub verification code is: {data['otp_code']}. Valid for 10 minutes."

    @staticmethod
    def reminder_24h(data: dict[str, Any]) -> str:
        """24-hour reminder before move."""
        return (
            f"MoveHub: Reminder - Your move is tomorrow at {data['move_time']}. "
            f"Pickup: {data['pickup_address']}. Contact: {data['mover_phone']}"
        )
