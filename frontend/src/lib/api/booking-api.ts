import { apiClient } from './client';
import { BookingFormData } from '@/lib/validations/booking';
import { BookingWithDetails } from '@/types/booking';

export const bookingAPI = {
  createBooking: async (data: BookingFormData): Promise<BookingWithDetails> => {
    const response = await apiClient.post<BookingWithDetails>('/api/v1/bookings', data);
    return response.data;
  },

  getBooking: async (id: string): Promise<BookingWithDetails> => {
    const response = await apiClient.get<BookingWithDetails>(`/api/v1/bookings/${id}`);
    return response.data;
  },

  listBookings: async (): Promise<BookingWithDetails[]> => {
    const response = await apiClient.get<BookingWithDetails[]>('/api/v1/bookings');
    return response.data;
  },
};
