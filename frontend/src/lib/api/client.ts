/**
 * Centralized API client configuration
 * All API modules should import and use this client
 */

import axios, { AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Configured axios instance with authentication and error handling
 */
export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for CORS with credentials (JWT cookies)
});

/**
 * Request interceptor to add auth tokens
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add Authorization header with JWT token from localStorage
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common error scenarios
    if (error.response?.status === 401) {
      // Unauthorized - clear tokens and redirect to signin
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Client-side redirect
        window.location.href = '/signin';
      }
    }

    // Return formatted error
    const message = error.response?.data
      ? (error.response.data as any).detail || error.message
      : error.message;

    return Promise.reject(new Error(message));
  }
);

/**
 * API Error class for typed error handling
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}
