import { UseFormReturn } from 'react-hook-form';
import { BookingFormData } from '@/lib/validations/booking';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatDateTime, formatPhoneNumber } from '@/lib/utils';
import { MapPin, Calendar, Package, User, Phone, Mail } from 'lucide-react';

interface ReviewStepProps {
  form: UseFormReturn<BookingFormData>;
}

export function ReviewStep({ form }: ReviewStepProps) {
  const formData = form.watch();

  // Calculate estimated price (simplified - backend will do actual calculation)
  const baseHourlyRate = 150;
  const baseMileageRate = 2.5;
  const hourlyC = baseHourlyRate * formData.estimated_duration_hours;
  const mileageCost = baseMileageRate * formData.estimated_distance_miles;

  // Stairs surcharge
  let stairsSurcharge = 0;
  const stairsRate = 50;
  if (formData.pickup_floors > 0 && !formData.has_elevator_pickup) {
    stairsSurcharge += stairsRate * formData.pickup_floors;
  }
  if (formData.dropoff_floors > 0 && !formData.has_elevator_dropoff) {
    stairsSurcharge += stairsRate * formData.dropoff_floors;
  }

  // Special items surcharge
  const specialItemsSurcharge = (formData.special_items?.length || 0) * 100;

  const subtotal = hourlyCost + mileageCost + stairsSurcharge + specialItemsSurcharge;
  const platformFee = subtotal * 0.05;
  const total = subtotal + platformFee;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Review Your Booking
        </h2>
        <p className="text-gray-600">
          Please review all details before confirming your booking
        </p>
      </div>

      <div className="grid gap-4">
        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <User className="h-5 w-5" />
              Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-gray-400" />
              <span className="font-medium">{formData.customer_name}</span>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-gray-400" />
              <span>{formData.customer_email}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-gray-400" />
              <span>{formatPhoneNumber(formData.customer_phone)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Move Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Move Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <span className="font-medium">Date & Time:</span>
              <div className="text-gray-700">
                {formatDateTime(formData.move_date)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-medium">Distance:</span>
                <div className="text-gray-700">
                  {formData.estimated_distance_miles} miles
                </div>
              </div>
              <div>
                <span className="font-medium">Duration:</span>
                <div className="text-gray-700">
                  {formData.estimated_duration_hours} hours
                </div>
              </div>
            </div>
            {formData.special_items && formData.special_items.length > 0 && (
              <div>
                <span className="font-medium">Special Items:</span>
                <div className="text-gray-700">
                  {formData.special_items.map(item =>
                    item.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                  ).join(', ')}
                </div>
              </div>
            )}
            {formData.customer_notes && (
              <div>
                <span className="font-medium">Notes:</span>
                <div className="text-gray-700 italic">
                  "{formData.customer_notes}"
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Locations */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <MapPin className="h-5 w-5" />
              Locations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <div className="font-medium text-green-700 mb-1">Pickup</div>
              <div className="text-gray-700">
                {formData.pickup_address}<br />
                {formData.pickup_city}, {formData.pickup_state} {formData.pickup_zip}<br />
                Floor {formData.pickup_floors}
                {formData.has_elevator_pickup ? ' (Elevator)' : ' (Stairs)'}
              </div>
            </div>
            <div>
              <div className="font-medium text-blue-700 mb-1">Dropoff</div>
              <div className="text-gray-700">
                {formData.dropoff_address}<br />
                {formData.dropoff_city}, {formData.dropoff_state} {formData.dropoff_zip}<br />
                Floor {formData.dropoff_floors}
                {formData.has_elevator_dropoff ? ' (Elevator)' : ' (Stairs)'}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Price Estimate */}
        <Card className="border-primary-200 bg-primary-50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Package className="h-5 w-5" />
              Price Estimate
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span>Hourly Rate ({formData.estimated_duration_hours} hrs @ {formatCurrency(baseHourlyRate)}/hr):</span>
              <span>{formatCurrency(hourlyCost)}</span>
            </div>
            <div className="flex justify-between">
              <span>Mileage ({formData.estimated_distance_miles} mi @ {formatCurrency(baseMileageRate)}/mi):</span>
              <span>{formatCurrency(mileageCost)}</span>
            </div>
            {stairsSurcharge > 0 && (
              <div className="flex justify-between text-amber-700">
                <span>Stairs Surcharge:</span>
                <span>{formatCurrency(stairsSurcharge)}</span>
              </div>
            )}
            {specialItemsSurcharge > 0 && (
              <div className="flex justify-between">
                <span>Special Items:</span>
                <span>{formatCurrency(specialItemsSurcharge)}</span>
              </div>
            )}
            <div className="border-t pt-2 flex justify-between">
              <span>Subtotal:</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-600">
              <span>Platform Fee (5%):</span>
              <span>{formatCurrency(platformFee)}</span>
            </div>
            <div className="border-t-2 border-primary-600 pt-2 flex justify-between font-bold text-lg text-primary-700">
              <span>Total:</span>
              <span>{formatCurrency(total)}</span>
            </div>
            <p className="text-xs text-gray-600 italic mt-2">
              * Final price will be calculated by the moving company and may vary based on actual conditions
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> By confirming this booking, you agree to our terms of service.
          You'll receive a confirmation email with your booking details and the assigned mover information.
        </p>
      </div>
    </div>
  );
}
