"""Unit tests for pricing service."""

from datetime import datetime

import pytest

from app.schemas.pricing import PricingConfigResponse, SurchargeRule
from app.services.pricing import PricingService


@pytest.mark.unit
class TestPricingService:
    """Test pricing calculations."""

    def test_basic_pricing_calculation(self):
        """Test basic pricing without surcharges."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        booking_details = {
            "estimated_duration_hours": 4.0,
            "estimated_distance_miles": 20.0,
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        expected_hourly = 150.0 * 4.0  # 600.0
        expected_mileage = 2.50 * 20.0  # 50.0
        expected_total = expected_hourly + expected_mileage  # 650.0

        assert result.estimated_amount == expected_total
        assert result.breakdown.base_hourly_cost == expected_hourly
        assert result.breakdown.base_mileage_cost == expected_mileage
        assert not result.breakdown.minimum_applied

    def test_minimum_charge_applied(self):
        """Test that minimum charge is applied when subtotal is below minimum."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=50.0,
            base_mileage_rate=1.0,
            minimum_charge=200.0,
            surcharge_rules=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        booking_details = {
            "estimated_duration_hours": 1.0,
            "estimated_distance_miles": 5.0,
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        assert result.estimated_amount == 200.0  # Minimum applied
        assert result.breakdown.minimum_applied

    def test_stairs_surcharge(self):
        """Test stairs surcharge calculation."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[SurchargeRule(type="stairs", amount=50.0, per_flight=True)],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        booking_details = {
            "estimated_duration_hours": 4.0,
            "estimated_distance_miles": 20.0,
            "pickup_floors": 2,
            "dropoff_floors": 1,
            "has_elevator_pickup": False,
            "has_elevator_dropoff": False,
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        base_cost = (150.0 * 4.0) + (2.50 * 20.0)  # 650.0
        stairs_surcharge = 50.0 * 3  # 3 flights total = 150.0
        expected_total = base_cost + stairs_surcharge  # 800.0

        assert result.estimated_amount == expected_total
        assert len(result.breakdown.surcharges) == 1
        assert result.breakdown.surcharges[0]["amount"] == stairs_surcharge

    def test_weekend_multiplier_surcharge(self):
        """Test weekend multiplier surcharge."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[SurchargeRule(type="weekend", multiplier=1.25, days=[0, 6])],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Saturday
        move_date = datetime(2024, 1, 6, 10, 0)  # Saturday

        booking_details = {
            "estimated_duration_hours": 4.0,
            "estimated_distance_miles": 20.0,
            "move_date": move_date,
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        base_cost = (150.0 * 4.0) + (2.50 * 20.0)  # 650.0
        weekend_surcharge = base_cost * 0.25  # 162.5 (25% increase)
        expected_total = base_cost + weekend_surcharge  # 812.5

        assert result.estimated_amount == expected_total

    def test_multiple_surcharges(self):
        """Test that multiple surcharges are applied correctly."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[
                SurchargeRule(type="stairs", amount=50.0, per_flight=True),
                SurchargeRule(type="piano", amount=100.0),
            ],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        booking_details = {
            "estimated_duration_hours": 4.0,
            "estimated_distance_miles": 20.0,
            "pickup_floors": 2,
            "dropoff_floors": 0,
            "has_elevator_pickup": False,
            "has_elevator_dropoff": True,
            "special_items": ["piano", "antiques"],
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        base_cost = (150.0 * 4.0) + (2.50 * 20.0)  # 650.0
        stairs_surcharge = 50.0 * 2  # 100.0
        piano_surcharge = 100.0
        expected_total = base_cost + stairs_surcharge + piano_surcharge  # 850.0

        assert result.estimated_amount == expected_total
        assert len(result.breakdown.surcharges) == 2

    def test_platform_fee_calculation(self):
        """Test platform fee calculation (5%)."""
        # Arrange
        pricing_config = PricingConfigResponse(
            id="00000000-0000-0000-0000-000000000000",  # type: ignore
            org_id="00000000-0000-0000-0000-000000000000",  # type: ignore
            base_hourly_rate=150.0,
            base_mileage_rate=2.50,
            minimum_charge=200.0,
            surcharge_rules=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        booking_details = {
            "estimated_duration_hours": 4.0,
            "estimated_distance_miles": 20.0,
        }

        # Act
        result = PricingService.calculate_price(pricing_config, booking_details)

        # Assert
        expected_total = 650.0
        expected_platform_fee = expected_total * 0.05  # 32.5

        assert result.platform_fee == expected_platform_fee
