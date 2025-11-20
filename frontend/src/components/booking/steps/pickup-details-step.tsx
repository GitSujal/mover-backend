import { UseFormReturn } from 'react-hook-form';
import { BookingFormData } from '@/lib/validations/booking';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { US_STATES } from '@/lib/constants';

interface PickupDetailsStepProps {
  form: UseFormReturn<BookingFormData>;
}

export function PickupDetailsStep({ form }: PickupDetailsStepProps) {
  const {
    register,
    watch,
    formState: { errors },
  } = form;

  const hasElevator = watch('has_elevator_pickup');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Pickup Location
        </h2>
        <p className="text-gray-600">
          Where are we picking up your items?
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="pickup_address" required>
            Street Address
          </Label>
          <Input
            id="pickup_address"
            {...register('pickup_address')}
            placeholder="123 Main St, Apt 4B"
            error={errors.pickup_address?.message}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="pickup_city" required>
              City
            </Label>
            <Input
              id="pickup_city"
              {...register('pickup_city')}
              placeholder="San Francisco"
              error={errors.pickup_city?.message}
            />
          </div>

          <div>
            <Label htmlFor="pickup_state" required>
              State
            </Label>
            <Select
              id="pickup_state"
              {...register('pickup_state')}
              error={errors.pickup_state?.message}
            >
              {US_STATES.map((state) => (
                <option key={state.value} value={state.value}>
                  {state.label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="pickup_zip" required>
            ZIP Code
          </Label>
          <Input
            id="pickup_zip"
            {...register('pickup_zip')}
            placeholder="94102"
            maxLength={10}
            error={errors.pickup_zip?.message}
          />
        </div>

        <div className="border-t pt-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="pickup_floors" required>
                Floor Number
              </Label>
              <Input
                id="pickup_floors"
                type="number"
                min="0"
                max="50"
                {...register('pickup_floors', { valueAsNumber: true })}
                placeholder="0 for ground floor"
                error={errors.pickup_floors?.message}
              />
              <p className="mt-1 text-xs text-gray-500">
                0 for ground floor, 1 for 1st floor, etc.
              </p>
            </div>

            <div>
              <Label htmlFor="has_elevator_pickup">
                Elevator Available?
              </Label>
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    {...register('has_elevator_pickup')}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {hasElevator ? 'Yes' : 'No'}
                  </span>
                </label>
              </div>
              {!hasElevator && (
                <p className="mt-1 text-xs text-amber-600">
                  Stairs surcharge may apply
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
