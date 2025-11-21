/**
 * Rating and Review Types
 *
 * Type definitions for customer ratings and reviews
 */

export interface RatingCreate {
  booking_id: string;
  overall_rating: number; // 1-5 stars
  professionalism_rating?: number;
  punctuality_rating?: number;
  care_of_items_rating?: number;
  communication_rating?: number;
  value_for_money_rating?: number;
  review_text?: string;
  review_title?: string;
}

export interface Rating {
  id: string;
  booking_id: string;
  org_id: string;
  overall_rating: number;
  professionalism_rating: number | null;
  punctuality_rating: number | null;
  care_of_items_rating: number | null;
  communication_rating: number | null;
  value_for_money_rating: number | null;
  review_text: string | null;
  review_title: string | null;
  customer_name: string;
  mover_response: string | null;
  mover_responded_at: string | null;
  is_published: boolean;
  is_verified_booking: boolean;
  created_at: string;
  updated_at: string;
}

export interface RatingSummary {
  org_id: string;
  total_ratings: number;
  average_overall_rating: number;
  average_professionalism: number | null;
  average_punctuality: number | null;
  average_care_of_items: number | null;
  average_communication: number | null;
  average_value_for_money: number | null;
  five_star_count: number;
  four_star_count: number;
  three_star_count: number;
  two_star_count: number;
  one_star_count: number;
  created_at: string;
  updated_at: string;
}

export interface RatingListResponse {
  ratings: Rating[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface RatingStats {
  org_id: string;
  summary: RatingSummary;
  recent_ratings: Rating[];
  rating_trend: 'improving' | 'stable' | 'declining';
  response_rate: number;
  average_response_time_hours: number | null;
}

export interface MoverResponse {
  mover_response: string;
}

export const RATING_CATEGORIES = [
  { key: 'professionalism', label: 'Professionalism' },
  { key: 'punctuality', label: 'Punctuality' },
  { key: 'care_of_items', label: 'Care of Items' },
  { key: 'communication', label: 'Communication' },
  { key: 'value_for_money', label: 'Value for Money' },
] as const;

export type RatingCategory = (typeof RATING_CATEGORIES)[number]['key'];
