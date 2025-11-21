'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { bookingFormSchema, type BookingFormData } from '@/lib/validations/booking';
import { bookingAPI } from '@/lib/api/booking-api';
import { Button } from '@/components/ui/button';
import { CustomerInfoStep } from './steps/customer-info-step';
import { PickupDetailsStep } from './steps/pickup-details-step';
import { DropoffDetailsStep } from './steps/dropoff-details-step';
import { MoveDetailsStep } from './steps/move-details-step';
import { ReviewStep } from './steps/review-step';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const STEPS = [
  { number: 1, title: 'Your Info', component: CustomerInfoStep },
  { number: 2, title: 'Pickup', component: PickupDetailsStep },
  { number: 3, title: 'Dropoff', component: DropoffDetailsStep },
  { number: 4, title: 'Move Details', component: MoveDetailsStep },
  { number: 5, title: 'Review', component: ReviewStep },
];

export function BookingForm() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);

  const form = useForm<BookingFormData>({
    resolver: zodResolver(bookingFormSchema),
    mode: 'onChange',
    defaultValues: {
      customer_name: '',
      customer_email: '',
      customer_phone: '',
      move_date: '',
      pickup_address: '',
      pickup_city: '',
      pickup_state: 'CA',
      pickup_zip: '',
      pickup_floors: 0,
      has_elevator_pickup: false,
      dropoff_address: '',
      dropoff_city: '',
      dropoff_state: 'CA',
      dropoff_zip: '',
      dropoff_floors: 0,
      has_elevator_dropoff: false,
      estimated_distance_miles: 10,
      estimated_duration_hours: 4,
      special_items: [],
      customer_notes: '',
    },
  });

  const createBookingMutation = useMutation({
    mutationFn: bookingAPI.createBooking,
    onSuccess: (data) => {
      // Redirect to booking confirmation page
      router.push(`/booking/${data.id}`);
    },
    onError: (error: Error) => {
      alert(`Error creating booking: ${error.message}`);
    },
  });

  const handleNext = async () => {
    // Validate current step fields
    const fieldsToValidate = getFieldsForStep(currentStep);
    const isValid = await form.trigger(fieldsToValidate);

    if (isValid) {
      if (currentStep < STEPS.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = form.handleSubmit((data) => {
    createBookingMutation.mutate(data);
  });

  const CurrentStepComponent = STEPS[currentStep].component;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.number} className="flex-1">
                <div className="flex items-center">
                  {/* Step Circle */}
                  <div className="flex flex-col items-center flex-shrink-0">
                    <div
                      className={cn(
                        'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors',
                        index < currentStep
                          ? 'bg-primary-600 border-primary-600'
                          : index === currentStep
                            ? 'border-primary-600 bg-white text-primary-600'
                            : 'border-gray-300 bg-white text-gray-400'
                      )}
                    >
                      {index < currentStep ? (
                        <Check className="h-5 w-5 text-white" />
                      ) : (
                        <span className="font-semibold">{step.number}</span>
                      )}
                    </div>
                    <span
                      className={cn(
                        'mt-2 text-xs font-medium',
                        index <= currentStep ? 'text-gray-900' : 'text-gray-400'
                      )}
                    >
                      {step.title}
                    </span>
                  </div>

                  {/* Connector Line */}
                  {index < STEPS.length - 1 && (
                    <div
                      className={cn(
                        'h-0.5 flex-1 mx-2',
                        index < currentStep ? 'bg-primary-600' : 'bg-gray-300'
                      )}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit}>
            <CurrentStepComponent form={form} />

            {/* Navigation Buttons */}
            <div className="mt-8 flex justify-between border-t pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={handleBack}
                disabled={currentStep === 0}
              >
                Back
              </Button>

              {currentStep < STEPS.length - 1 ? (
                <Button type="button" onClick={handleNext}>
                  Continue
                </Button>
              ) : (
                <Button
                  type="submit"
                  isLoading={createBookingMutation.isPending}
                  disabled={createBookingMutation.isPending}
                >
                  Confirm Booking
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Helper function to determine which fields to validate for each step
function getFieldsForStep(step: number): (keyof BookingFormData)[] {
  switch (step) {
    case 0: // Customer Info
      return ['customer_name', 'customer_email', 'customer_phone'];
    case 1: // Pickup
      return ['pickup_address', 'pickup_city', 'pickup_state', 'pickup_zip', 'pickup_floors'];
    case 2: // Dropoff
      return ['dropoff_address', 'dropoff_city', 'dropoff_state', 'dropoff_zip', 'dropoff_floors'];
    case 3: // Move Details
      return ['move_date', 'estimated_distance_miles', 'estimated_duration_hours'];
    default:
      return [];
  }
}
