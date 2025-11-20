"""
Pricing calculation service.

Implements extensible pricing logic with surcharge rules.
All calculations are traced with OpenTelemetry for observability.
"""

import logging
from datetime import datetime, time
from typing import Any

from app.core.config import settings
from app.core.observability import pricing_calculation_histogram, tracer
from app.schemas.pricing import PriceBreakdown, PriceEstimate, PricingConfigResponse, SurchargeRule

logger = logging.getLogger(__name__)


class PricingService:
    """Service for calculating booking prices based on configurable rules."""

    @staticmethod
    def _apply_surcharge_rule(
        rule: SurchargeRule,
        base_amount: float,
        booking_details: dict[str, Any],
    ) -> tuple[float, dict[str, Any]]:
        """
        Apply a single surcharge rule.

        Args:
            rule: Surcharge rule configuration
            base_amount: Base amount before surcharge
            booking_details: Booking information for context

        Returns:
            Tuple of (surcharge_amount, surcharge_details)
        """
        surcharge = 0.0
        details: dict[str, Any] = {
            "type": rule.type,
            "applied": False,
            "amount": 0.0,
        }

        # Stairs surcharge
        if rule.type == "stairs":
            total_flights = booking_details.get("pickup_floors", 0) + booking_details.get(
                "dropoff_floors", 0
            )
            # Only apply if no elevators available
            has_elevator = booking_details.get("has_elevator_pickup") or booking_details.get(
                "has_elevator_dropoff"
            )

            if total_flights > 0 and not has_elevator:
                if rule.per_flight and rule.amount:
                    surcharge = rule.amount * total_flights
                    details["applied"] = True
                    details["amount"] = surcharge
                    details["flights"] = total_flights
                elif rule.amount:
                    surcharge = rule.amount
                    details["applied"] = True
                    details["amount"] = surcharge

        # Special items (piano, fragile, etc.)
        elif rule.type in ["piano", "fragile", "antiques"]:
            special_items = booking_details.get("special_items", [])
            if rule.type in [item.lower() for item in special_items]:
                if rule.amount:
                    surcharge = rule.amount
                    details["applied"] = True
                    details["amount"] = surcharge

        # Time-based surcharges (weekend, after_hours, holiday)
        elif rule.type in ["weekend", "after_hours", "holiday"]:
            move_date: datetime = booking_details.get("move_date")
            if not move_date:
                return 0.0, details

            # Weekend surcharge
            if rule.type == "weekend" and rule.days:
                if move_date.weekday() in [6, 0] or move_date.isoweekday() in rule.days:
                    if rule.multiplier:
                        surcharge = base_amount * (rule.multiplier - 1.0)
                        details["applied"] = True
                        details["amount"] = surcharge
                        details["multiplier"] = rule.multiplier

            # After hours surcharge
            elif rule.type == "after_hours" and rule.min_time and rule.max_time:
                move_time = move_date.time()
                start_time = time.fromisoformat(rule.min_time)
                end_time = time.fromisoformat(rule.max_time)

                # Handle overnight ranges (e.g., 18:00 to 08:00)
                if start_time > end_time:
                    is_after_hours = move_time >= start_time or move_time <= end_time
                else:
                    is_after_hours = start_time <= move_time <= end_time

                if is_after_hours:
                    if rule.multiplier:
                        surcharge = base_amount * (rule.multiplier - 1.0)
                        details["applied"] = True
                        details["amount"] = surcharge
                        details["multiplier"] = rule.multiplier

        # Distance-based surcharge
        elif rule.type == "distance":
            distance = booking_details.get("estimated_distance_miles", 0)
            if rule.amount and distance > 50:  # Long distance threshold
                surcharge = rule.amount
                details["applied"] = True
                details["amount"] = surcharge

        # Custom surcharge
        elif rule.type == "custom" and rule.amount:
            surcharge = rule.amount
            details["applied"] = True
            details["amount"] = surcharge
            if rule.description:
                details["description"] = rule.description

        return surcharge, details

    @staticmethod
    def calculate_price(
        pricing_config: PricingConfigResponse,
        booking_details: dict[str, Any],
    ) -> PriceEstimate:
        """
        Calculate total price for a booking.

        Args:
            pricing_config: Organization's pricing configuration
            booking_details: Booking information including distance, duration, special items, etc.

        Returns:
            PriceEstimate with total and breakdown
        """
        with tracer.start_as_current_span("pricing.calculate") as span:
            start_time = datetime.now()

            # Extract booking details
            duration_hours = booking_details.get("estimated_duration_hours", 0)
            distance_miles = booking_details.get("estimated_distance_miles", 0)

            # Calculate base costs
            base_hourly_cost = float(pricing_config.base_hourly_rate) * duration_hours
            base_mileage_cost = float(pricing_config.base_mileage_rate) * distance_miles
            base_subtotal = base_hourly_cost + base_mileage_cost

            # Add span attributes
            span.set_attribute("pricing.base_hourly_cost", base_hourly_cost)
            span.set_attribute("pricing.base_mileage_cost", base_mileage_cost)
            span.set_attribute("pricing.duration_hours", duration_hours)
            span.set_attribute("pricing.distance_miles", distance_miles)

            # Apply surcharge rules
            total_surcharges = 0.0
            applied_surcharges: list[dict[str, Any]] = []

            for rule in pricing_config.surcharge_rules:
                surcharge_amount, surcharge_details = PricingService._apply_surcharge_rule(
                    rule, base_subtotal, booking_details
                )

                if surcharge_details["applied"]:
                    total_surcharges += surcharge_amount
                    applied_surcharges.append(surcharge_details)
                    logger.debug(
                        f"Applied surcharge: {rule.type} = ${surcharge_amount:.2f}",
                        extra={"surcharge": surcharge_details},
                    )

            # Calculate subtotal
            subtotal = base_subtotal + total_surcharges

            # Apply minimum charge if needed
            minimum_charge = float(pricing_config.minimum_charge)
            minimum_applied = subtotal < minimum_charge
            total = max(subtotal, minimum_charge)

            # Calculate platform fee
            platform_fee = total * (settings.PLATFORM_FEE_PERCENTAGE / 100.0)

            # Create breakdown
            breakdown = PriceBreakdown(
                base_hourly_cost=round(base_hourly_cost, 2),
                base_mileage_cost=round(base_mileage_cost, 2),
                surcharges=applied_surcharges,
                subtotal=round(subtotal, 2),
                minimum_applied=minimum_applied,
                total=round(total, 2),
            )

            # Record metrics
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            pricing_calculation_histogram.record(duration_ms)

            span.set_attribute("pricing.total_surcharges", total_surcharges)
            span.set_attribute("pricing.minimum_applied", minimum_applied)
            span.set_attribute("pricing.final_total", total)
            span.set_attribute("pricing.platform_fee", platform_fee)

            logger.info(
                f"Price calculated: ${total:.2f} (base: ${base_subtotal:.2f}, "
                f"surcharges: ${total_surcharges:.2f}, min: ${minimum_applied})",
                extra={
                    "total": total,
                    "platform_fee": platform_fee,
                    "surcharges_count": len(applied_surcharges),
                },
            )

            return PriceEstimate(
                estimated_amount=round(total, 2),
                platform_fee=round(platform_fee, 2),
                breakdown=breakdown,
            )
