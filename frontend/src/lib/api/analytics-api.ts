/**
 * Analytics API client
 * Type-safe API calls for analytics dashboard endpoints
 */

import { apiClient } from './client';

export interface BookingMetrics {
  total_bookings: number;
  pending_bookings: number;
  confirmed_bookings: number;
  in_progress_bookings: number;
  completed_bookings: number;
  cancelled_bookings: number;
  total_revenue: number;
  average_booking_value: number;
  completion_rate: number;
  cancellation_rate: number;
}

export interface DriverMetrics {
  total_drivers: number;
  active_drivers: number;
  inactive_drivers: number;
  average_bookings_per_driver: number;
  top_performers: Array<{
    driver_id: string;
    driver_name: string;
    total_bookings: number;
    average_rating: number;
  }>;
}

export interface TruckMetrics {
  total_trucks: number;
  active_trucks: number;
  inactive_trucks: number;
  average_utilization: number;
}

export interface RatingMetrics {
  total_ratings: number;
  average_rating: number;
  five_star_count: number;
  four_star_count: number;
  three_star_count: number;
  two_star_count: number;
  one_star_count: number;
  rating_distribution: Record<number, number>;
  recent_reviews: Array<{
    rating: number;
    comment: string;
    created_at: string;
    booking_id: string;
  }>;
}

export interface SupportMetrics {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  escalated_tickets: number;
  average_resolution_hours: number;
  ticket_by_type: Record<string, number>;
  ticket_by_priority: Record<string, number>;
}

export interface InvoiceMetrics {
  total_invoices: number;
  draft_invoices: number;
  issued_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  total_revenue: number;
  total_outstanding: number;
  average_invoice_amount: number;
  payment_rate: number;
}

export interface VerificationMetrics {
  pending_verifications: number;
  under_review_verifications: number;
  approved_verifications: number;
  rejected_verifications: number;
  expired_verifications: number;
  expiring_soon_count: number;
}

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label: string | null;
}

export interface TrendData {
  bookings_trend: TimeSeriesDataPoint[];
  revenue_trend: TimeSeriesDataPoint[];
  rating_trend: TimeSeriesDataPoint[];
}

export interface OrganizationDashboard {
  org_id: string;
  org_name: string;
  period_start: string;
  period_end: string;
  booking_metrics: BookingMetrics;
  driver_metrics: DriverMetrics;
  truck_metrics: TruckMetrics;
  rating_metrics: RatingMetrics;
  support_metrics: SupportMetrics;
  invoice_metrics: InvoiceMetrics;
  verification_metrics: VerificationMetrics;
  trends: TrendData;
}

export const analyticsAPI = {
  /**
   * Get complete organization dashboard with all metrics
   */
  getDashboard: async (
    orgId: string,
    startDate?: string,
    endDate?: string
  ): Promise<OrganizationDashboard> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = `/api/v1/analytics/organization/${orgId}/dashboard${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * Get booking metrics only
   */
  getBookingMetrics: async (
    orgId: string,
    startDate?: string,
    endDate?: string
  ): Promise<BookingMetrics> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = `/api/v1/analytics/organization/${orgId}/bookings${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * Get driver metrics
   */
  getDriverMetrics: async (orgId: string): Promise<DriverMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/drivers`);
    return response.data;
  },

  /**
   * Get truck metrics
   */
  getTruckMetrics: async (orgId: string): Promise<TruckMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/trucks`);
    return response.data;
  },

  /**
   * Get rating metrics
   */
  getRatingMetrics: async (orgId: string): Promise<RatingMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/ratings`);
    return response.data;
  },

  /**
   * Get support metrics
   */
  getSupportMetrics: async (orgId: string): Promise<SupportMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/support`);
    return response.data;
  },

  /**
   * Get invoice metrics
   */
  getInvoiceMetrics: async (orgId: string): Promise<InvoiceMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/invoices`);
    return response.data;
  },

  /**
   * Get verification metrics
   */
  getVerificationMetrics: async (orgId: string): Promise<VerificationMetrics> => {
    const response = await apiClient.get(`/api/v1/analytics/organization/${orgId}/verification`);
    return response.data;
  },

  /**
   * Get trend data over time
   */
  getTrendData: async (orgId: string, startDate?: string, endDate?: string): Promise<TrendData> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = `/api/v1/analytics/organization/${orgId}/trends${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get(url);
    return response.data;
  },
};
