'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CalendarDays, MapPin, Loader2, AlertCircle } from 'lucide-react';
import { bookingAPI } from '@/lib/api/booking-api';
import { BookingWithDetails } from '@/types/booking';
import { Button } from '@/components/ui/button';

export default function JobsPage() {
  const [bookings, setBookings] = useState<BookingWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await bookingAPI.listBookings();
      setBookings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bookings');
      console.error('Error loading bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center gap-4">
        <div className="flex items-center gap-2 text-red-600">
          <AlertCircle className="h-5 w-5" />
          <p>{error}</p>
        </div>
        <Button onClick={loadBookings}>Try Again</Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs & Schedule</h1>
          <p className="text-muted-foreground">View and manage your upcoming moves.</p>
        </div>
        <Button onClick={loadBookings} variant="outline">
          Refresh
        </Button>
      </div>

      <div className="grid gap-6">
        {bookings.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <CalendarDays className="h-12 w-12 mb-4 opacity-50" />
              <p>No bookings found.</p>
            </CardContent>
          </Card>
        ) : (
          bookings.map((booking) => (
            <Card key={booking.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-lg font-medium">
                    Move #{booking.id.slice(0, 8).toUpperCase()} - {booking.customer_name}
                  </CardTitle>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <CalendarDays className="mr-2 h-4 w-4" />
                    {new Date(booking.move_date).toLocaleDateString()}
                    {booking.estimated_duration_hours &&
                      ` • ~${booking.estimated_duration_hours} hours`}
                  </div>
                </div>
                <Badge variant={booking.status === 'COMPLETED' ? 'secondary' : 'default'}>
                  {booking.status}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Pickup</div>
                    <div className="flex items-start text-sm text-muted-foreground">
                      <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                      {booking.pickup_address}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Dropoff</div>
                    <div className="flex items-start text-sm text-muted-foreground">
                      <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                      {booking.dropoff_address}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
