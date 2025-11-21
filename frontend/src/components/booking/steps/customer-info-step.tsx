import { UseFormReturn } from 'react-hook-form';
import { BookingFormData } from '@/lib/validations/booking';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface CustomerInfoStepProps {
  form: UseFormReturn<BookingFormData>;
}

export function CustomerInfoStep({ form }: CustomerInfoStepProps) {
  const {
    register,
    formState: { errors },
  } = form;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Let&apos;s Get Started</h2>
        <p className="text-gray-600">
          We&apos;ll need your contact information to confirm your booking and send updates.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="customer_name" required>
            Full Name
          </Label>
          <Input
            id="customer_name"
            {...register('customer_name')}
            placeholder="John Doe"
            error={errors.customer_name?.message}
          />
        </div>

        <div>
          <Label htmlFor="customer_email" required>
            Email Address
          </Label>
          <Input
            id="customer_email"
            type="email"
            {...register('customer_email')}
            placeholder="john@example.com"
            error={errors.customer_email?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            We&apos;ll send your booking confirmation here
          </p>
        </div>

        <div>
          <Label htmlFor="customer_phone" required>
            Phone Number
          </Label>
          <Input
            id="customer_phone"
            type="tel"
            {...register('customer_phone')}
            placeholder="1234567890"
            error={errors.customer_phone?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            Format: 1234567890 (10 digits, no spaces or dashes)
          </p>
        </div>
      </div>
    </div>
  );
}
