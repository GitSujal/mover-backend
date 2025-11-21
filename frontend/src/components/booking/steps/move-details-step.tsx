import { UseFormReturn } from 'react-hook-form';
import { BookingFormData } from '@/lib/validations/booking';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SPECIAL_ITEMS } from '@/lib/constants';

interface MoveDetailsStepProps {
  form: UseFormReturn<BookingFormData>;
}

export function MoveDetailsStep({ form }: MoveDetailsStepProps) {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = form;

  const specialItems = watch('special_items') || [];

  const toggleSpecialItem = (item: string) => {
    const currentItems = specialItems;
    if (currentItems.includes(item)) {
      setValue(
        'special_items',
        currentItems.filter((i) => i !== item)
      );
    } else {
      setValue('special_items', [...currentItems, item]);
    }
  };

  // Get tomorrow's date as minimum
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split('T')[0];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Move Details</h2>
        <p className="text-gray-600">Tell us when and what you&apos;re moving</p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="move_date" required>
            Move Date & Time
          </Label>
          <Input
            id="move_date"
            type="datetime-local"
            {...register('move_date')}
            min={minDate}
            error={errors.move_date?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            Select your preferred date and time for the move
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="estimated_distance_miles" required>
              Estimated Distance (miles)
            </Label>
            <Input
              id="estimated_distance_miles"
              type="number"
              min="1"
              max="1000"
              step="0.1"
              {...register('estimated_distance_miles', { valueAsNumber: true })}
              placeholder="10"
              error={errors.estimated_distance_miles?.message}
            />
            <p className="mt-1 text-xs text-gray-500">Approximate distance between locations</p>
          </div>

          <div>
            <Label htmlFor="estimated_duration_hours" required>
              Estimated Duration (hours)
            </Label>
            <Input
              id="estimated_duration_hours"
              type="number"
              min="1"
              max="24"
              step="0.5"
              {...register('estimated_duration_hours', { valueAsNumber: true })}
              placeholder="4"
              error={errors.estimated_duration_hours?.message}
            />
            <p className="mt-1 text-xs text-gray-500">How long do you think it will take?</p>
          </div>
        </div>

        <div>
          <Label>Special Items</Label>
          <p className="text-sm text-gray-500 mb-3">
            Select any items that require special handling (may affect pricing)
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {SPECIAL_ITEMS.map((item) => {
              const isSelected = specialItems.includes(item.value);
              return (
                <button
                  key={item.value}
                  type="button"
                  onClick={() => toggleSpecialItem(item.value)}
                  className={`px-4 py-2 rounded-md border-2 text-sm font-medium transition-colors ${
                    isSelected
                      ? 'border-primary-600 bg-primary-50 text-primary-700'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
          {specialItems.length > 0 && (
            <p className="mt-2 text-sm text-primary-600">
              Selected: {specialItems.join(', ').replace(/_/g, ' ')}
            </p>
          )}
        </div>

        <div>
          <Label htmlFor="customer_notes">Additional Notes (Optional)</Label>
          <Textarea
            id="customer_notes"
            {...register('customer_notes')}
            placeholder="Any special instructions or concerns? (e.g., parking restrictions, narrow stairs, valuable items)"
            rows={4}
            error={errors.customer_notes?.message}
          />
          <p className="mt-1 text-xs text-gray-500">Maximum 1000 characters</p>
        </div>
      </div>
    </div>
  );
}
