/**
 * Rating API Client
 *
 * API client for rating and review operations
 */

import axios from "axios";
import type {
  Rating,
  RatingCreate,
  RatingListResponse,
  RatingStats,
  RatingSummary,
  MoverResponse,
} from "@/types/rating";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Create API client with session cookie support
 */
const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true, // Include session cookies
  headers: {
    "Content-Type": "application/json",
  },
});

export const ratingAPI = {
  /**
   * Submit a rating for a completed booking
   */
  createRating: async (data: RatingCreate): Promise<Rating> => {
    const response = await apiClient.post<Rating>("/ratings", data);
    return response.data;
  },

  /**
   * Get a specific rating by ID
   */
  getRating: async (ratingId: string): Promise<Rating> => {
    const response = await apiClient.get<Rating>(`/ratings/${ratingId}`);
    return response.data;
  },

  /**
   * Get rating for a specific booking
   */
  getRatingByBooking: async (bookingId: string): Promise<Rating> => {
    const response = await apiClient.get<Rating>(`/ratings/booking/${bookingId}`);
    return response.data;
  },

  /**
   * List all ratings for an organization (paginated)
   */
  listOrganizationRatings: async (
    orgId: string,
    page: number = 1,
    limit: number = 20
  ): Promise<RatingListResponse> => {
    const response = await apiClient.get<RatingListResponse>(
      `/ratings/organization/${orgId}`,
      {
        params: { page, limit },
      }
    );
    return response.data;
  },

  /**
   * Get aggregate rating summary for an organization
   */
  getOrganizationSummary: async (orgId: string): Promise<RatingSummary> => {
    const response = await apiClient.get<RatingSummary>(
      `/ratings/organization/${orgId}/summary`
    );
    return response.data;
  },

  /**
   * Get detailed rating statistics for an organization
   */
  getOrganizationStats: async (orgId: string): Promise<RatingStats> => {
    const response = await apiClient.get<RatingStats>(`/ratings/organization/${orgId}/stats`);
    return response.data;
  },

  /**
   * Add mover's response to a rating (requires mover authentication)
   */
  addMoverResponse: async (ratingId: string, response: MoverResponse): Promise<Rating> => {
    const apiResponse = await apiClient.patch<Rating>(`/ratings/${ratingId}/response`, response);
    return apiResponse.data;
  },
};
