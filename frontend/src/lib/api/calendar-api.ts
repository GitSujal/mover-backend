/**
 * Calendar and Fleet Management API client
 * Type-safe API calls for calendar and scheduling endpoints
 */

import { apiClient } from './client';

export interface BookingCalendarItem {
  id: string;
  booking_number: string;
  customer_name: string;
  customer_phone: string;
  move_date: string;
  pickup_address: string;
  dropoff_address: string;
  estimated_duration_hours: number;
  status: string;
  assigned_driver_id: string | null;
  assigned_driver_name: string | null;
  assigned_truck_id: string | null;
  assigned_truck_identifier: string | null;
  notes: string | null;
}

export interface DriverScheduleItem {
  driver_id: string;
  driver_name: string;
  driver_phone: string;
  booking_id: string | null;
  booking_number: string | null;
  start_time: string;
  end_time: string;
  status: string;
  customer_name: string | null;
  pickup_address: string | null;
  dropoff_address: string | null;
}

export interface TruckScheduleItem {
  truck_id: string;
  truck_identifier: string;
  booking_id: string | null;
  booking_number: string | null;
  start_time: string;
  end_time: string;
  status: string;
  customer_name: string | null;
  pickup_address: string | null;
  dropoff_address: string | null;
}

export interface CalendarViewResponse {
  start_date: string;
  end_date: string;
  bookings: BookingCalendarItem[];
  total_bookings: number;
}

export interface DriverScheduleResponse {
  driver_id: string;
  driver_name: string;
  start_date: string;
  end_date: string;
  schedule: DriverScheduleItem[];
  total_hours_booked: number;
  total_bookings: number;
}

export interface TruckScheduleResponse {
  truck_id: string;
  truck_identifier: string;
  start_date: string;
  end_date: string;
  schedule: TruckScheduleItem[];
  total_hours_booked: number;
  total_bookings: number;
}

export interface FleetCalendarResponse {
  org_id: string;
  start_date: string;
  end_date: string;
  bookings: BookingCalendarItem[];
  driver_schedules: DriverScheduleResponse[];
  truck_schedules: TruckScheduleResponse[];
  total_bookings: number;
  total_drivers: number;
  total_trucks: number;
}

export interface AvailabilitySlot {
  start_time: string;
  end_time: string;
  available_drivers: string[];
  available_trucks: string[];
}

export interface AvailabilityCheckRequest {
  org_id: string;
  date: string;
  estimated_duration_hours: number;
  require_driver?: boolean;
  require_truck?: boolean;
}

export interface AvailabilityCheckResponse {
  is_available: boolean;
  available_slots: AvailabilitySlot[];
  total_available_drivers: number;
  total_available_trucks: number;
  message: string | null;
}

export const calendarAPI = {
  /**
   * Get calendar bookings for date range
   */
  getCalendarBookings: async (
    startDate: string,
    endDate: string,
    statusFilter?: string[]
  ): Promise<CalendarViewResponse> => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    if (statusFilter && statusFilter.length > 0) {
      statusFilter.forEach((status) => params.append('status_filter', status));
    }

    const response = await apiClient.get(`/api/v1/calendar/bookings?${params.toString()}`);
    return response.data;
  },

  /**
   * Get driver schedule
   */
  getDriverSchedule: async (
    driverId: string,
    startDate: string,
    endDate: string
  ): Promise<DriverScheduleResponse> => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);

    const response = await apiClient.get(
      `/api/v1/calendar/driver/${driverId}/schedule?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get truck schedule
   */
  getTruckSchedule: async (
    truckId: string,
    startDate: string,
    endDate: string
  ): Promise<TruckScheduleResponse> => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);

    const response = await apiClient.get(
      `/api/v1/calendar/truck/${truckId}/schedule?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get fleet-wide calendar
   */
  getFleetCalendar: async (startDate: string, endDate: string): Promise<FleetCalendarResponse> => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);

    const response = await apiClient.get(`/api/v1/calendar/fleet?${params.toString()}`);
    return response.data;
  },

  /**
   * Check availability for a time slot
   */
  checkAvailability: async (
    request: AvailabilityCheckRequest
  ): Promise<AvailabilityCheckResponse> => {
    const response = await apiClient.post('/api/v1/calendar/availability', request);
    return response.data;
  },
};
