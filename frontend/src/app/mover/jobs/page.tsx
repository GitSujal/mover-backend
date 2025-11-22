'use client';

import { useState, useEffect } from 'react';
import { bookingAPI } from '@/lib/api/booking-api';
import { BookingWithDetails } from '@/types/booking';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CalendarDays, MapPin, Package } from 'lucide-react';

const getStatusBadge = (status: string) => {
  const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
    pending: 'outline',
    confirmed: 'default',
    in_progress: 'secondary',
    completed: 'default',
    cancelled: 'destructive',
  };

  return variants[status] || 'outline';
};

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
      const data = await bookingAPI.listBookings({ limit: 50 });
      setBookings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bookings');
      console.error('Bookings loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs & Schedule</h1>
          <p className="text-muted-foreground">Loading your upcoming moves...</p>
        </div>
        <div className="grid gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-24 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs & Schedule</h1>
          <p className="text-muted-foreground">View and manage your upcoming moves.</p>
        </div>
        <Card className="border-destructive">
          <CardContent className="p-6">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={loadBookings} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
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

      {bookings.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Package className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-lg font-medium mb-2">No bookings found</p>
            <p className="text-sm text-muted-foreground">
              Your upcoming moves will appear here once customers book your services.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {bookings.map((booking) => (
            <Card key={booking.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-lg font-medium">
                    Move #{booking.id.slice(0, 8)} - {booking.customer_name}
                  </CardTitle>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <CalendarDays className="mr-2 h-4 w-4" />
                    {new Date(booking.move_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </div>
                </div>
                <Badge variant={getStatusBadge(booking.status)}>
                  {booking.status.replace(/_/g, ' ').toUpperCase()}
                </Badge>
              </CardHeader>
              <CardContent>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Pickup</div>
                    <div className="flex items-start text-sm text-muted-foreground">
                      <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                      {booking.pickup_address}
                      {booking.pickup_address_line2 && `, ${booking.pickup_address_line2}`}
                      {', '}
                      {booking.pickup_city}, {booking.pickup_state} {booking.pickup_zip_code}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Floor: {booking.pickup_floor_number}
                      {booking.pickup_has_elevator ? ' (Elevator available)' : ' (No elevator)'}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Dropoff</div>
                    <div className="flex items-start text-sm text-muted-foreground">
                      <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                      {booking.dropoff_address}
                      {booking.dropoff_address_line2 && `, ${booking.dropoff_address_line2}`}
                      {', '}
                      {booking.dropoff_city}, {booking.dropoff_state} {booking.dropoff_zip_code}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Floor: {booking.dropoff_floor_number}
                      {booking.dropoff_has_elevator ? ' (Elevator available)' : ' (No elevator)'}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t grid gap-2 sm:grid-cols-3">
                  <div>
                    <div className="text-xs text-muted-foreground">Distance</div>
                    <div className="text-sm font-medium">{booking.distance_miles} miles</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Duration</div>
                    <div className="text-sm font-medium">{booking.estimated_duration_hours} hours</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Total Price</div>
                    <div className="text-sm font-bold text-primary">
                      ${booking.total_price.toFixed(2)}
                    </div>
                  </div>
                </div>

                {booking.special_items && booking.special_items.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-xs text-muted-foreground mb-2">Special Items</div>
                    <div className="flex flex-wrap gap-2">
                      {booking.special_items.map((item, idx) => (
                        <Badge key={idx} variant="outline">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {booking.notes && (
                  <div className="mt-4 pt-4 border-t">
                    <div className="text-xs text-muted-foreground mb-1">Notes</div>
                    <div className="text-sm">{booking.notes}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
