/**
 * Rating Card Component
 *
 * Displays a single rating/review with all details
 */

'use client';

import { StarRating } from './StarRating';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Badge } from '../ui/badge';
import type { Rating } from '@/types/rating';
import { RATING_CATEGORIES } from '@/types/rating';

interface RatingCardProps {
  rating: Rating;
  showMoverResponse?: boolean;
}

export function RatingCard({ rating, showMoverResponse = true }: RatingCardProps) {
  const createdDate = new Date(rating.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <Card className="w-full">
      <CardHeader className="space-y-3">
        {/* Header with rating and date */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <StarRating value={rating.overall_rating} readonly size="sm" />
              {rating.is_verified_booking && (
                <Badge variant="outline" className="text-xs">
                  Verified Move
                </Badge>
              )}
            </div>
            <p className="text-sm text-gray-600">
              {rating.customer_name} • {createdDate}
            </p>
          </div>
        </div>

        {/* Review Title */}
        {rating.review_title && <h3 className="text-lg font-semibold">{rating.review_title}</h3>}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Review Text */}
        {rating.review_text && (
          <p className="text-gray-700 whitespace-pre-wrap">{rating.review_text}</p>
        )}

        {/* Category Ratings */}
        {(rating.professionalism_rating ||
          rating.punctuality_rating ||
          rating.care_of_items_rating ||
          rating.communication_rating ||
          rating.value_for_money_rating) && (
          <div className="space-y-2 pt-2 border-t">
            <p className="text-sm font-medium text-gray-700">Detailed Ratings</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {RATING_CATEGORIES.map(({ key, label }) => {
                const ratingValue = rating[`${key}_rating` as keyof Rating] as number | null;
                if (!ratingValue) return null;
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{label}:</span>
                    <StarRating value={ratingValue} readonly size="sm" />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Mover Response */}
        {showMoverResponse && rating.mover_response && (
          <div className="mt-4 space-y-2 rounded-lg bg-gray-50 p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-900">Response from Mover</p>
              {rating.mover_responded_at && (
                <p className="text-xs text-gray-500">
                  {new Date(rating.mover_responded_at).toLocaleDateString()}
                </p>
              )}
            </div>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{rating.mover_response}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
