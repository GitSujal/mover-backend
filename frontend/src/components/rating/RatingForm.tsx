/**
 * Rating Form Component
 *
 * Form for customers to submit ratings after completing a move
 */

'use client';

import { useState } from 'react';
import { StarRating } from './StarRating';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { ratingAPI } from '@/lib/api/rating-api';
import type { RatingCreate, RatingCategory } from '@/types/rating';
import { RATING_CATEGORIES } from '@/types/rating';

interface RatingFormProps {
  bookingId: string;
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

export function RatingForm({ bookingId, onSuccess, onError }: RatingFormProps) {
  const [overallRating, setOverallRating] = useState(0);
  const [categoryRatings, setCategoryRatings] = useState<Record<RatingCategory, number>>({
    professionalism: 0,
    punctuality: 0,
    care_of_items: 0,
    communication: 0,
    value_for_money: 0,
  });
  const [reviewTitle, setReviewTitle] = useState('');
  const [reviewText, setReviewText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCategoryRatingChange = (category: RatingCategory, rating: number) => {
    setCategoryRatings((prev) => ({
      ...prev,
      [category]: rating,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (overallRating === 0) {
      setError('Please provide an overall rating');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const ratingData: RatingCreate = {
        booking_id: bookingId,
        overall_rating: overallRating,
        professionalism_rating: categoryRatings.professionalism || undefined,
        punctuality_rating: categoryRatings.punctuality || undefined,
        care_of_items_rating: categoryRatings.care_of_items || undefined,
        communication_rating: categoryRatings.communication || undefined,
        value_for_money_rating: categoryRatings.value_for_money || undefined,
        review_title: reviewTitle || undefined,
        review_text: reviewText || undefined,
      };

      await ratingAPI.createRating(ratingData);

      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit rating';
      setError(errorMessage);
      if (onError) {
        onError(err instanceof Error ? err : new Error(errorMessage));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Rate Your Move</CardTitle>
        <CardDescription>
          Share your experience to help others make informed decisions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Overall Rating */}
          <div>
            <StarRating
              value={overallRating}
              onChange={setOverallRating}
              size="lg"
              label="Overall Rating*"
            />
          </div>

          {/* Category Ratings */}
          <div className="space-y-4">
            <Label className="text-base">Rate Specific Aspects (Optional)</Label>
            <div className="grid gap-4 sm:grid-cols-2">
              {RATING_CATEGORIES.map(({ key, label }) => (
                <StarRating
                  key={key}
                  value={categoryRatings[key]}
                  onChange={(rating) => handleCategoryRatingChange(key, rating)}
                  size="sm"
                  label={label}
                />
              ))}
            </div>
          </div>

          {/* Review Title */}
          <div className="space-y-2">
            <Label htmlFor="review-title">Review Title (Optional)</Label>
            <Input
              id="review-title"
              placeholder="Summarize your experience"
              value={reviewTitle}
              onChange={(e) => setReviewTitle(e.target.value)}
              maxLength={200}
            />
          </div>

          {/* Review Text */}
          <div className="space-y-2">
            <Label htmlFor="review-text">Your Review (Optional)</Label>
            <Textarea
              id="review-text"
              placeholder="Tell us about your experience..."
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              rows={5}
              maxLength={2000}
              className="resize-none"
            />
            <p className="text-xs text-gray-500">{reviewText.length} / 2000 characters</p>
          </div>

          {/* Error Message */}
          {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">{error}</div>}

          {/* Submit Button */}
          <div className="flex justify-end gap-2">
            <Button
              type="submit"
              disabled={isSubmitting || overallRating === 0}
              className="min-w-[120px]"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Rating'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
