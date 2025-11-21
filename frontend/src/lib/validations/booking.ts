import { z } from 'zod';

export const bookingFormSchema = z.object({
  customer_name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  customer_email: z.string().email('Invalid email address'),
  customer_phone: z.string().regex(/^\+?1?\d{10,}$/, 'Phone number must be at least 10 digits'),
  move_date: z.string().refine(
    (date) => {
      return new Date(date) >= new Date();
    },
    { message: 'Move date must be in the future' }
  ),
  pickup_address: z.string().min(5, 'Address must be at least 5 characters'),
  pickup_city: z.string().min(2, 'City is required'),
  pickup_state: z.string().length(2, 'State must be 2 characters'),
  pickup_zip: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code'),
  pickup_floors: z.number().int().min(0).max(100),
  has_elevator_pickup: z.boolean(),
  dropoff_address: z.string().min(5, 'Address must be at least 5 characters'),
  dropoff_city: z.string().min(2, 'City is required'),
  dropoff_state: z.string().length(2, 'State must be 2 characters'),
  dropoff_zip: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code'),
  dropoff_floors: z.number().int().min(0).max(100),
  has_elevator_dropoff: z.boolean(),
  estimated_distance_miles: z.number().positive('Distance must be positive'),
  estimated_duration_hours: z.number().positive('Duration must be positive'),
  special_items: z.array(z.string()).default([]),
  customer_notes: z.string().optional(),
});

export type BookingFormData = z.infer<typeof bookingFormSchema>;
