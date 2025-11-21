import { UseFormReturn } from 'react-hook-form';
import { BookingFormData } from '@/lib/validations/booking';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { US_STATES } from '@/lib/constants';

interface DropoffDetailsStepProps {
  form: UseFormReturn<BookingFormData>;
}

export function DropoffDetailsStep({ form }: DropoffDetailsStepProps) {
  const {
    register,
    watch,
    formState: { errors },
  } = form;

  const hasElevator = watch('has_elevator_dropoff');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Dropoff Location</h2>
        <p className="text-gray-600">Where are we delivering your items?</p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="dropoff_address" required>
            Street Address
          </Label>
          <Input
            id="dropoff_address"
            {...register('dropoff_address')}
            placeholder="456 Oak Ave, Unit 2C"
            error={errors.dropoff_address?.message}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="dropoff_city" required>
              City
            </Label>
            <Input
              id="dropoff_city"
              {...register('dropoff_city')}
              placeholder="Oakland"
              error={errors.dropoff_city?.message}
            />
          </div>

          <div>
            <Label htmlFor="dropoff_state" required>
              State
            </Label>
            <Select
              id="dropoff_state"
              {...register('dropoff_state')}
              error={errors.dropoff_state?.message}
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
          <Label htmlFor="dropoff_zip" required>
            ZIP Code
          </Label>
          <Input
            id="dropoff_zip"
            {...register('dropoff_zip')}
            placeholder="94601"
            maxLength={10}
            error={errors.dropoff_zip?.message}
          />
        </div>

        <div className="border-t pt-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="dropoff_floors" required>
                Floor Number
              </Label>
              <Input
                id="dropoff_floors"
                type="number"
                min="0"
                max="50"
                {...register('dropoff_floors', { valueAsNumber: true })}
                placeholder="0 for ground floor"
                error={errors.dropoff_floors?.message}
              />
              <p className="mt-1 text-xs text-gray-500">
                0 for ground floor, 1 for 1st floor, etc.
              </p>
            </div>

            <div>
              <Label htmlFor="has_elevator_dropoff">Elevator Available?</Label>
              <div className="mt-2">
                <label className="inline-flex items-center">
                  <input
                    type="checkbox"
                    {...register('has_elevator_dropoff')}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{hasElevator ? 'Yes' : 'No'}</span>
                </label>
              </div>
              {!hasElevator && (
                <p className="mt-1 text-xs text-amber-600">Stairs surcharge may apply</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
