/**
 * Type definitions matching backend Pydantic schemas
 * These are strongly typed to ensure type safety across the application
 */

export type BookingStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';

export interface BookingBase {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  move_date: string; // ISO 8601 datetime
  pickup_address: string;
  pickup_city: string;
  pickup_state: string;
  pickup_zip: string;
  dropoff_address: string;
  dropoff_city: string;
  dropoff_state: string;
  dropoff_zip: string;
  estimated_distance_miles: number;
  estimated_duration_hours: number;
  special_items: string[];
  pickup_floors: number;
  dropoff_floors: number;
  has_elevator_pickup: boolean;
  has_elevator_dropoff: boolean;
  customer_notes?: string;
}

export interface BookingCreate extends BookingBase {}

export interface BookingResponse extends BookingBase {
  id: string; // UUID
  org_id: string; // UUID
  truck_id: string | null; // UUID
  status: BookingStatus;
  effective_start: string; // ISO 8601 datetime
  effective_end: string; // ISO 8601 datetime
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime;
}

export interface AvailabilityCheck {
  org_id: string; // UUID
  truck_id: string | null; // UUID
  move_date: string; // ISO 8601 datetime
  estimated_duration_hours: number;
}

export interface AvailabilityResponse {
  available: boolean;
  conflicting_bookings: BookingResponse[];
}

export interface PriceEstimate {
  estimated_amount: number;
  platform_fee: number;
  breakdown: PriceBreakdown;
}

export interface PriceBreakdown {
  base_hourly_cost: number;
  base_mileage_cost: number;
  surcharges: Surcharge[];
  subtotal: number;
  minimum_applied: boolean;
  total: number;
}

export interface Surcharge {
  type: string;
  applied: boolean;
  amount: number;
  description?: string;
  flights?: number;
  multiplier?: number;
}

export interface TruckDetails {
  id: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  capacity_cubic_feet: number;
}

export interface DriverDetails {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  photo_url: string | null;
}

export interface BookingWithDetails extends BookingResponse {
  truck?: TruckDetails;
  driver?: DriverDetails;
  price_estimate?: PriceEstimate;
}
