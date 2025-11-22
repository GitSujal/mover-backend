import axios from 'axios';
import { BookingFormData } from '@/lib/validations/booking';
import { BookingWithDetails } from '@/types/booking';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for CORS with credentials
});

export const bookingAPI = {
  createBooking: async (data: BookingFormData): Promise<BookingWithDetails> => {
    const response = await apiClient.post<BookingWithDetails>('/api/v1/bookings', data);
    return response.data;
  },

  getBooking: async (id: string): Promise<BookingWithDetails> => {
    const response = await apiClient.get<BookingWithDetails>(`/api/v1/bookings/${id}`);
    return response.data;
  },

  listBookings: async (params?: {
    truck_id?: string;
    driver_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<BookingWithDetails[]> => {
    const response = await apiClient.get<BookingWithDetails[]>('/api/v1/bookings', { params });
    return response.data;
  },
};
