"""Calendar and fleet management schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.booking import BookingStatus


class BookingCalendarItem(BaseModel):
    """Booking item for calendar view."""

    id: UUID
    booking_number: str
    customer_name: str
    customer_phone: str
    move_date: datetime
    pickup_address: str
    dropoff_address: str
    estimated_duration_hours: float
    status: BookingStatus
    assigned_driver_id: UUID | None = None
    assigned_driver_name: str | None = None
    assigned_truck_id: UUID | None = None
    assigned_truck_identifier: str | None = None
    notes: str | None = None


class DriverScheduleItem(BaseModel):
    """Driver schedule item."""

    driver_id: UUID
    driver_name: str
    driver_phone: str
    booking_id: UUID | None = None
    booking_number: str | None = None
    start_time: datetime
    end_time: datetime
    status: str  # 'available', 'booked', 'off_duty'
    customer_name: str | None = None
    pickup_address: str | None = None
    dropoff_address: str | None = None


class TruckScheduleItem(BaseModel):
    """Truck schedule item."""

    truck_id: UUID
    truck_identifier: str
    booking_id: UUID | None = None
    booking_number: str | None = None
    start_time: datetime
    end_time: datetime
    status: str  # 'available', 'booked', 'maintenance'
    customer_name: str | None = None
    pickup_address: str | None = None
    dropoff_address: str | None = None


class CalendarViewResponse(BaseModel):
    """Calendar view with bookings and availability."""

    start_date: datetime
    end_date: datetime
    bookings: list[BookingCalendarItem]
    total_bookings: int


class DriverScheduleResponse(BaseModel):
    """Driver schedule response."""

    driver_id: UUID
    driver_name: str
    start_date: datetime
    end_date: datetime
    schedule: list[DriverScheduleItem]
    total_hours_booked: float
    total_bookings: int


class TruckScheduleResponse(BaseModel):
    """Truck schedule response."""

    truck_id: UUID
    truck_identifier: str
    start_date: datetime
    end_date: datetime
    schedule: list[TruckScheduleItem]
    total_hours_booked: float
    total_bookings: int


class FleetCalendarResponse(BaseModel):
    """Fleet-wide calendar response."""

    org_id: UUID
    start_date: datetime
    end_date: datetime
    bookings: list[BookingCalendarItem]
    driver_schedules: list[DriverScheduleResponse]
    truck_schedules: list[TruckScheduleResponse]
    total_bookings: int
    total_drivers: int
    total_trucks: int


class AvailabilitySlot(BaseModel):
    """Available time slot."""

    start_time: datetime
    end_time: datetime
    available_drivers: list[UUID]
    available_trucks: list[UUID]


class AvailabilityCheckRequest(BaseModel):
    """Request to check availability."""

    org_id: UUID
    date: datetime
    estimated_duration_hours: float = Field(gt=0, le=24)
    require_driver: bool = True
    require_truck: bool = True


class AvailabilityCheckResponse(BaseModel):
    """Availability check response."""

    is_available: bool
    available_slots: list[AvailabilitySlot]
    total_available_drivers: int
    total_available_trucks: int
    message: str | None = None
