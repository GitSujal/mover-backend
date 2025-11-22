import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

export interface TruckResponse {
  id: string;
  org_id: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  capacity_cubic_feet: number;
  current_latitude: number;
  current_longitude: number;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface DriverResponse {
  id: string;
  org_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  drivers_license_number: string;
  drivers_license_state: string;
  drivers_license_expiry: string;
  has_cdl: boolean;
  cdl_class?: string;
  is_verified: boolean;
  is_available: boolean;
  background_check_completed: boolean;
  created_at: string;
  updated_at: string;
}

export const fleetAPI = {
  // Trucks
  listTrucks: async (limit = 100): Promise<TruckResponse[]> => {
    const response = await apiClient.get<TruckResponse[]>('/api/v1/movers/trucks', {
      params: { limit },
    });
    return response.data;
  },

  getTruck: async (truckId: string): Promise<TruckResponse> => {
    const response = await apiClient.get<TruckResponse>(`/api/v1/movers/trucks/${truckId}`);
    return response.data;
  },

  // Drivers
  listDrivers: async (limit = 100): Promise<DriverResponse[]> => {
    const response = await apiClient.get<DriverResponse[]>('/api/v1/movers/drivers', {
      params: { limit },
    });
    return response.data;
  },

  getDriver: async (driverId: string): Promise<DriverResponse> => {
    const response = await apiClient.get<DriverResponse>(`/api/v1/movers/drivers/${driverId}`);
    return response.data;
  },
};
