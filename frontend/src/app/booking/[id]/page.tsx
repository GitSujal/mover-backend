'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { bookingAPI } from '@/lib/api/booking-api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatDateTime, formatPhoneNumber } from '@/lib/utils';
import {
  CheckCircle,
  Clock,
  MapPin,
  Package,
  Truck,
  User,
  Phone,
  Mail,
  Calendar,
  AlertCircle,
} from 'lucide-react';

interface BookingPageProps {
  params: Promise<{ id: string }>;
}

export default function BookingPage({ params }: BookingPageProps) {
  const { id } = use(params);

  const { data: booking, isLoading, error } = useQuery({
    queryKey: ['booking', id],
    queryFn: () => bookingAPI.getBooking(id),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading booking details...</p>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                Booking Not Found
              </h2>
              <p className="text-gray-600 mb-6">
                We couldn't find the booking you're looking for.
              </p>
              <Link href="/">
                <Button>Back to Home</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      CONFIRMED: 'bg-green-100 text-green-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-gray-100 text-gray-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };

    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          styles[status as keyof typeof styles] || styles.PENDING
        }`}
      >
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Booking Confirmed!
              </h1>
              <p className="text-gray-600">
                Booking ID: <span className="font-mono text-sm">{booking.id}</span>
              </p>
            </div>
            {getStatusBadge(booking.status)}
          </div>

          <div className="flex items-center gap-2 text-green-700 bg-green-50 p-4 rounded-lg">
            <CheckCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">
              Your booking has been confirmed! We've sent a confirmation email to{' '}
              <strong>{booking.customer_email}</strong>
            </p>
          </div>
        </div>

        <div className="grid gap-6">
          {/* Move Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Move Schedule
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">Move Date</div>
                <div className="text-lg font-semibold">
                  {formatDateTime(booking.move_date)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Distance</div>
                  <div className="font-semibold">
                    {booking.estimated_distance_miles} miles
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Duration</div>
                  <div className="font-semibold">
                    {booking.estimated_duration_hours} hours
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Locations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Locations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm font-medium text-green-700 mb-1">
                  Pickup Location
                </div>
                <div className="text-gray-700">
                  {booking.pickup_address}<br />
                  {booking.pickup_city}, {booking.pickup_state} {booking.pickup_zip}<br />
                  Floor {booking.pickup_floors}
                  {booking.has_elevator_pickup ? ' (Elevator Available)' : ' (Stairs)'}
                </div>
              </div>
              <div className="border-t pt-4">
                <div className="text-sm font-medium text-blue-700 mb-1">
                  Dropoff Location
                </div>
                <div className="text-gray-700">
                  {booking.dropoff_address}<br />
                  {booking.dropoff_city}, {booking.dropoff_state} {booking.dropoff_zip}<br />
                  Floor {booking.dropoff_floors}
                  {booking.has_elevator_dropoff ? ' (Elevator Available)' : ' (Stairs)'}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Driver & Truck Info */}
          {(booking.driver || booking.truck) && (
            <Card className="border-primary-200 bg-primary-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="h-5 w-5" />
                  Your Moving Team
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {booking.driver && (
                  <div>
                    <div className="text-sm font-medium text-primary-700 mb-2">
                      Driver
                    </div>
                    <div className="flex items-center gap-4">
                      {booking.driver.photo_url ? (
                        <img
                          src={booking.driver.photo_url}
                          alt={`${booking.driver.first_name} ${booking.driver.last_name}`}
                          className="w-16 h-16 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                          <User className="h-8 w-8 text-gray-400" />
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-lg">
                          {booking.driver.first_name} {booking.driver.last_name}
                        </div>
                        <div className="text-sm text-gray-700 flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          {formatPhoneNumber(booking.driver.phone)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {booking.truck && (
                  <div className="border-t pt-4">
                    <div className="text-sm font-medium text-primary-700 mb-2">
                      Vehicle
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-600">Make & Model</div>
                        <div className="font-semibold">
                          {booking.truck.year} {booking.truck.make} {booking.truck.model}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">License Plate</div>
                        <div className="font-semibold font-mono">
                          {booking.truck.license_plate}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-600">Capacity</div>
                        <div className="font-semibold">
                          {booking.truck.capacity_cubic_feet} cu ft
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Contact Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Your Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 text-sm">
                <User className="h-4 w-4 text-gray-400" />
                <span className="font-medium">{booking.customer_name}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-gray-400" />
                <span>{booking.customer_email}</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-gray-400" />
                <span>{formatPhoneNumber(booking.customer_phone)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Special Items & Notes */}
          {(booking.special_items.length > 0 || booking.customer_notes) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Additional Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {booking.special_items.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      Special Items
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {booking.special_items.map((item) => (
                        <span
                          key={item}
                          className="px-3 py-1 bg-gray-100 rounded-full text-sm"
                        >
                          {item.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {booking.customer_notes && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </div>
                    <div className="text-sm text-gray-600 italic">
                      "{booking.customer_notes}"
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            <Link href="/" className="flex-1">
              <Button variant="outline" className="w-full">
                Back to Home
              </Button>
            </Link>
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => window.print()}
            >
              Print Confirmation
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
