'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useState } from 'react';
import { bookingAPI } from '@/lib/api/booking-api';
import { useToast } from '@/components/ui/use-toast';
import { Loader2 } from 'lucide-react';

interface Step4Props {
  onBack: () => void;
  onComplete: () => void;
  bookingData: any;
}

export function Step4Review({ onBack, onComplete, bookingData }: Step4Props) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userDetails, setUserDetails] = useState({
    name: '',
    email: '',
    phone: '',
  });
  const { toast } = useToast();

  const handleBook = async () => {
    if (!userDetails.name || !userDetails.email || !userDetails.phone) {
      toast({
        title: "Missing Information",
        description: "Please fill in all contact details.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsSubmitting(true);

      // Combine wizard data with user details
      const finalBookingData = {
        ...bookingData,
        customer_name: userDetails.name,
        customer_email: userDetails.email,
        customer_phone: userDetails.phone,
        // Ensure numeric fields are numbers
        pickup_floors: Number(bookingData.pickup_floors || 0),
        dropoff_floors: Number(bookingData.dropoff_floors || 0),
        estimated_distance_miles: Number(bookingData.estimated_distance_miles || 0),
        estimated_duration_hours: Number(bookingData.estimated_duration_hours || 0),
        special_items: bookingData.special_items || [],
      };

      await bookingAPI.createBooking(finalBookingData);

      toast({
        title: "Booking Confirmed!",
        description: "Your move has been successfully booked.",
      });

      onComplete();
    } catch (error) {
      console.error('Booking failed:', error);
      toast({
        title: "Booking Failed",
        description: error instanceof Error ? error.message : "Failed to create booking. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review & Book</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              placeholder="John Doe"
              value={userDetails.name}
              onChange={(e) => setUserDetails(prev => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="john@example.com"
              value={userDetails.email}
              onChange={(e) => setUserDetails(prev => ({ ...prev, email: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="+1 (555) 000-0000"
              value={userDetails.phone}
              onChange={(e) => setUserDetails(prev => ({ ...prev, phone: e.target.value }))}
            />
          </div>
        </div>

        <div className="flex justify-between pt-4">
          <Button type="button" variant="outline" onClick={onBack} disabled={isSubmitting}>
            Back
          </Button>
          <Button onClick={handleBook} className="bg-green-600 hover:bg-green-700" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              'Confirm Booking'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
