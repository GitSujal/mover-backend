"""
Payment service using Stripe Connect.

Handles payment processing with platform fees for marketplace model.
"""

import logging

import stripe

from app.core.config import settings
from app.core.observability import tracer

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    """Service for Stripe payment processing."""

    @staticmethod
    async def create_payment_intent(
        amount: float,
        customer_email: str,
        org_stripe_account_id: str,
        platform_fee: float,
        metadata: dict[str, str] | None = None,
    ) -> stripe.PaymentIntent:
        """
        Create Stripe PaymentIntent with platform fee.

        Args:
            amount: Total amount in USD
            customer_email: Customer email for receipt
            org_stripe_account_id: Connected account ID for mover organization
            platform_fee: Platform fee amount
            metadata: Additional metadata

        Returns:
            PaymentIntent object
        """
        with tracer.start_as_current_span("payment.create_intent") as span:
            span.set_attribute("payment.amount", amount)
            span.set_attribute("payment.platform_fee", platform_fee)

            try:
                # Convert to cents
                amount_cents = int(amount * 100)
                fee_cents = int(platform_fee * 100)

                # Create payment intent with destination charge
                # Platform receives fee, organization receives rest
                payment_intent = stripe.PaymentIntent.create(
                    amount=amount_cents,
                    currency="usd",
                    receipt_email=customer_email,
                    application_fee_amount=fee_cents,
                    transfer_data={"destination": org_stripe_account_id},
                    metadata=metadata or {},
                )

                logger.info(
                    f"Payment intent created: {payment_intent.id} for ${amount:.2f}",
                    extra={
                        "payment_intent_id": payment_intent.id,
                        "amount": amount,
                        "platform_fee": platform_fee,
                    },
                )

                span.set_attribute("payment.intent_id", payment_intent.id)

                return payment_intent

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating payment intent: {e}", exc_info=True)
                raise

    @staticmethod
    async def confirm_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
        """
        Confirm payment intent.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Updated PaymentIntent
        """
        with tracer.start_as_current_span("payment.confirm_intent") as span:
            span.set_attribute("payment.intent_id", payment_intent_id)

            try:
                payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)

                logger.info(
                    f"Payment intent confirmed: {payment_intent_id}",
                    extra={"payment_intent_id": payment_intent_id},
                )

                return payment_intent

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error confirming payment: {e}", exc_info=True)
                raise

    @staticmethod
    async def create_connected_account(
        email: str,
        business_name: str,
        business_tax_id: str,
    ) -> stripe.Account:
        """
        Create Stripe Connected Account for mover organization.

        Args:
            email: Organization email
            business_name: Business name
            business_tax_id: Tax ID (EIN)

        Returns:
            Account object
        """
        with tracer.start_as_current_span("payment.create_account") as span:
            span.set_attribute("payment.business_name", business_name)

            try:
                account = stripe.Account.create(
                    type="express",
                    country="US",
                    email=email,
                    business_type="company",
                    company={"name": business_name, "tax_id": business_tax_id},
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True},
                    },
                )

                logger.info(
                    f"Connected account created: {account.id}",
                    extra={"account_id": account.id, "business": business_name},
                )

                span.set_attribute("payment.account_id", account.id)

                return account

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating account: {e}", exc_info=True)
                raise

    @staticmethod
    async def create_account_link(
        account_id: str,
        refresh_url: str,
        return_url: str,
    ) -> stripe.AccountLink:
        """
        Create account onboarding link for organization.

        Args:
            account_id: Stripe account ID
            refresh_url: URL to redirect if link expires
            return_url: URL to redirect after onboarding

        Returns:
            AccountLink with onboarding URL
        """
        with tracer.start_as_current_span("payment.create_account_link") as span:
            span.set_attribute("payment.account_id", account_id)

            try:
                account_link = stripe.AccountLink.create(
                    account=account_id,
                    refresh_url=refresh_url,
                    return_url=return_url,
                    type="account_onboarding",
                )

                logger.info(
                    f"Account link created for {account_id}",
                    extra={"account_id": account_id},
                )

                return account_link

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating account link: {e}", exc_info=True)
                raise

    @staticmethod
    async def refund_payment(
        payment_intent_id: str,
        amount: float | None = None,
        reason: str | None = None,
    ) -> stripe.Refund:
        """
        Refund a payment.

        Args:
            payment_intent_id: Payment intent to refund
            amount: Amount to refund (None for full refund)
            reason: Refund reason

        Returns:
            Refund object
        """
        with tracer.start_as_current_span("payment.refund") as span:
            span.set_attribute("payment.intent_id", payment_intent_id)

            try:
                refund_params: dict[str, any] = {
                    "payment_intent": payment_intent_id,
                }

                if amount:
                    refund_params["amount"] = int(amount * 100)
                    span.set_attribute("payment.refund_amount", amount)

                if reason:
                    refund_params["reason"] = reason

                refund = stripe.Refund.create(**refund_params)

                logger.info(
                    f"Refund created: {refund.id} for {payment_intent_id}",
                    extra={
                        "refund_id": refund.id,
                        "payment_intent_id": payment_intent_id,
                        "amount": amount,
                    },
                )

                return refund

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating refund: {e}", exc_info=True)
                raise
