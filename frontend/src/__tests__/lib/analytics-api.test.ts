import { analyticsAPI } from '@/lib/api/analytics-api';
import { apiClient } from '@/lib/api/client';

// Mock the apiClient
jest.mock('@/lib/api/client');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Analytics API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getDashboard', () => {
    it('fetches organization dashboard successfully', async () => {
      const mockDashboard = {
        org_id: 'test-org-id',
        org_name: 'Test Organization',
        period_start: '2025-01-01T00:00:00Z',
        period_end: '2025-01-31T23:59:59Z',
        booking_metrics: {
          total_bookings: 50,
          completed_bookings: 40,
          cancelled_bookings: 5,
          active_bookings: 5,
          total_revenue: 25000,
          average_booking_value: 625,
        },
        driver_metrics: {
          total_drivers: 10,
          active_drivers: 8,
          total_hours_worked: 320,
          average_rating: 4.5,
        },
        truck_metrics: {
          total_trucks: 5,
          active_trucks: 4,
          total_hours_used: 200,
          utilization_rate: 0.8,
        },
        rating_metrics: {
          total_ratings: 45,
          average_rating: 4.6,
          five_star_count: 30,
          four_star_count: 10,
          three_star_count: 3,
          two_star_count: 1,
          one_star_count: 1,
        },
        support_metrics: {
          total_tickets: 12,
          open_tickets: 3,
          resolved_tickets: 8,
          average_resolution_time_hours: 24,
        },
        invoice_metrics: {
          total_invoices: 48,
          paid_invoices: 40,
          pending_invoices: 6,
          overdue_invoices: 2,
          total_revenue: 25000,
          outstanding_amount: 3000,
        },
        verification_metrics: {
          total_documents: 25,
          approved_documents: 20,
          pending_documents: 3,
          rejected_documents: 2,
          expiring_soon: 1,
        },
        trends: {
          dates: ['2025-01-01', '2025-01-02', '2025-01-03'],
          booking_counts: [5, 7, 6],
          revenue: [2500, 3500, 3000],
          ratings: [4.5, 4.6, 4.7],
        },
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockDashboard });

      const result = await analyticsAPI.getDashboard('test-org-id', '2025-01-01', '2025-01-31');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/analytics/organization/test-org-id/dashboard')
      );
      expect(result).toEqual(mockDashboard);
    });

    it('fetches dashboard without date parameters', async () => {
      const mockDashboard = {
        org_id: 'test-org-id',
        org_name: 'Test Organization',
        period_start: '2025-01-01T00:00:00Z',
        period_end: '2025-01-31T23:59:59Z',
        booking_metrics: {} as any,
        driver_metrics: {} as any,
        truck_metrics: {} as any,
        rating_metrics: {} as any,
        support_metrics: {} as any,
        invoice_metrics: {} as any,
        verification_metrics: {} as any,
        trends: {} as any,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockDashboard });

      await analyticsAPI.getDashboard('test-org-id');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/analytics/organization/test-org-id/dashboard'
      );
    });
  });

  describe('getBookingMetrics', () => {
    it('fetches booking metrics successfully', async () => {
      const mockMetrics = {
        total_bookings: 50,
        completed_bookings: 40,
        cancelled_bookings: 5,
        active_bookings: 5,
        total_revenue: 25000,
        average_booking_value: 625,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await analyticsAPI.getBookingMetrics('test-org-id');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/analytics/organization/test-org-id/bookings'
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('getDriverMetrics', () => {
    it('fetches driver metrics successfully', async () => {
      const mockMetrics = {
        total_drivers: 10,
        active_drivers: 8,
        total_hours_worked: 320,
        average_rating: 4.5,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await analyticsAPI.getDriverMetrics('test-org-id');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/analytics/organization/test-org-id/drivers'
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('getTruckMetrics', () => {
    it('fetches truck metrics successfully', async () => {
      const mockMetrics = {
        total_trucks: 5,
        active_trucks: 4,
        total_hours_used: 200,
        utilization_rate: 0.8,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await analyticsAPI.getTruckMetrics('test-org-id');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/analytics/organization/test-org-id/trucks'
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('getRatingMetrics', () => {
    it('fetches rating metrics successfully', async () => {
      const mockMetrics = {
        total_ratings: 45,
        average_rating: 4.6,
        five_star_count: 30,
        four_star_count: 10,
        three_star_count: 3,
        two_star_count: 1,
        one_star_count: 1,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockMetrics });

      const result = await analyticsAPI.getRatingMetrics('test-org-id');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/analytics/organization/test-org-id/ratings'
      );
      expect(result).toEqual(mockMetrics);
    });
  });

  describe('getTrendData', () => {
    it('fetches trend data successfully', async () => {
      const mockTrends = {
        dates: ['2025-01-01', '2025-01-02', '2025-01-03'],
        booking_counts: [5, 7, 6],
        revenue: [2500, 3500, 3000],
        ratings: [4.5, 4.6, 4.7],
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockTrends });

      const result = await analyticsAPI.getTrendData('test-org-id', '2025-01-01', '2025-01-31');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/analytics/organization/test-org-id/trends')
      );
      expect(result).toEqual(mockTrends);
    });
  });

  describe('Error Handling', () => {
    it('handles API errors', async () => {
      const mockError = new Error('Network error');
      mockedApiClient.get.mockRejectedValueOnce(mockError);

      await expect(analyticsAPI.getDashboard('test-org-id')).rejects.toThrow('Network error');
    });
  });
});
