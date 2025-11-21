/**
 * Star Rating Component
 *
 * Interactive star rating input (1-5 stars)
 */

'use client';

import { Star } from 'lucide-react';
import { useState } from 'react';

interface StarRatingProps {
  value: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  label?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

export function StarRating({
  value,
  onChange,
  readonly = false,
  size = 'md',
  showValue = false,
  label,
}: StarRatingProps) {
  const [hoverRating, setHoverRating] = useState(0);

  const displayRating = readonly ? value : hoverRating || value;

  const handleClick = (rating: number) => {
    if (!readonly && onChange) {
      onChange(rating);
    }
  };

  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => handleClick(star)}
            onMouseEnter={() => !readonly && setHoverRating(star)}
            onMouseLeave={() => !readonly && setHoverRating(0)}
            disabled={readonly}
            className={`${
              readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'
            } transition-transform ${sizeClasses[size]}`}
            aria-label={`Rate ${star} stars`}
          >
            <Star
              className={`${sizeClasses[size]} ${
                star <= displayRating
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'fill-none text-gray-300'
              }`}
            />
          </button>
        ))}
        {showValue && <span className="ml-2 text-sm text-gray-600">{value.toFixed(1)} / 5.0</span>}
      </div>
    </div>
  );
}
