/**
 * Rating Summary Component
 *
 * Displays aggregate rating statistics with star distribution
 */

"use client";

import { StarRating } from "./StarRating";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { RatingSummary as RatingSummaryType } from "@/types/rating";

interface RatingSummaryProps {
  summary: RatingSummaryType;
  showDetails?: boolean;
}

export function RatingSummary({ summary, showDetails = true }: RatingSummaryProps) {
  const { total_ratings, average_overall_rating } = summary;

  // Calculate percentages for star distribution
  const getStarPercentage = (count: number) => {
    if (total_ratings === 0) return 0;
    return (count / total_ratings) * 100;
  };

  const starDistribution = [
    { stars: 5, count: summary.five_star_count },
    { stars: 4, count: summary.four_star_count },
    { stars: 3, count: summary.three_star_count },
    { stars: 2, count: summary.two_star_count },
    { stars: 1, count: summary.one_star_count },
  ];

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Customer Ratings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Rating Display */}
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="text-5xl font-bold text-gray-900">
              {average_overall_rating.toFixed(1)}
            </div>
            <div className="mt-1">
              <StarRating
                value={average_overall_rating}
                readonly
                size="md"
              />
            </div>
            <p className="mt-2 text-sm text-gray-600">
              {total_ratings} {total_ratings === 1 ? "rating" : "ratings"}
            </p>
          </div>

          {/* Star Distribution */}
          {showDetails && total_ratings > 0 && (
            <div className="flex-1 space-y-2">
              {starDistribution.map(({ stars, count }) => {
                const percentage = getStarPercentage(count);
                return (
                  <div key={stars} className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 w-12">
                      {stars} star{stars !== 1 ? "s" : ""}
                    </span>
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-yellow-400 transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-12 text-right">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Category Averages */}
        {showDetails && (
          <div className="space-y-3 pt-4 border-t">
            <h4 className="text-sm font-medium text-gray-900">
              Average Ratings by Category
            </h4>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { label: "Professionalism", value: summary.average_professionalism },
                { label: "Punctuality", value: summary.average_punctuality },
                { label: "Care of Items", value: summary.average_care_of_items },
                { label: "Communication", value: summary.average_communication },
                { label: "Value for Money", value: summary.average_value_for_money },
              ].map(({ label, value }) => {
                if (value === null) return null;
                return (
                  <div
                    key={label}
                    className="flex items-center justify-between p-2 rounded-lg bg-gray-50"
                  >
                    <span className="text-sm text-gray-700">{label}</span>
                    <div className="flex items-center gap-1">
                      <StarRating value={value} readonly size="sm" />
                      <span className="text-sm font-medium text-gray-900 ml-1">
                        {value.toFixed(1)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* No Ratings State */}
        {total_ratings === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No ratings yet</p>
            <p className="text-sm text-gray-400 mt-1">
              Be the first to leave a review!
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
