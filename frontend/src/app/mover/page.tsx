'use client';

import { useState, useEffect } from 'react';
import { analyticsAPI, OrganizationDashboard } from '@/lib/api/analytics-api';
import { bookingAPI } from '@/lib/api/booking-api';
import { BookingWithDetails } from '@/types/booking';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, DollarSign, Truck, Users, CalendarDays } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

// Get org_id from environment variable or use a default for development
const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID || '550e8400-e29b-41d4-a716-446655440000';

export default function MoverDashboard() {
  const [dashboard, setDashboard] = useState<OrganizationDashboard | null>(null);
  const [recentBookings, setRecentBookings] = useState<BookingWithDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();

      const [dashboardData, bookingsData] = await Promise.all([
        analyticsAPI.getDashboard(ORG_ID, startDate, endDate),
        bookingAPI.listBookings({ limit: 5 }),
      ]);

      setDashboard(dashboardData);
      setRecentBookings(bookingsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Loading your business overview...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-16 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your moving business.</p>
        </div>
        <Card className="border-destructive">
          <CardContent className="p-6">
            <p className="text-destructive mb-4">
              {error || 'Failed to load dashboard data'}
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              Make sure the database is seeded with data and the backend is running.
            </p>
            <button
              onClick={loadDashboardData}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
            >
              Try Again
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { booking_metrics, driver_metrics, truck_metrics } = dashboard;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your moving business - Last 30 days
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${booking_metrics.total_revenue.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              From {booking_metrics.completed_bookings} completed jobs
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {booking_metrics.confirmed_bookings + booking_metrics.in_progress_bookings}
            </div>
            <p className="text-xs text-muted-foreground">
              {booking_metrics.pending_bookings} pending approval
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fleet Status</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {truck_metrics.active_trucks}/{truck_metrics.total_trucks}
            </div>
            <p className="text-xs text-muted-foreground">Trucks available</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Drivers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{driver_metrics.active_drivers}</div>
            <p className="text-xs text-muted-foreground">
              {driver_metrics.average_bookings_per_driver.toFixed(1)} avg jobs/driver
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Bookings</CardTitle>
          </CardHeader>
          <CardContent>
            {recentBookings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No recent bookings</p>
                <p className="text-sm mt-2">Bookings will appear here once customers book your services</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentBookings.map((booking) => (
                  <div key={booking.id} className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">{booking.customer_name}</p>
                      <p className="text-sm text-muted-foreground">{booking.customer_email}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(booking.move_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${booking.total_price.toFixed(2)}</div>
                      <Badge variant="outline" className="mt-1">
                        {booking.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Booking Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Pending</span>
                <span className="font-semibold">{booking_metrics.pending_bookings}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Confirmed</span>
                <span className="font-semibold">{booking_metrics.confirmed_bookings}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">In Progress</span>
                <span className="font-semibold">{booking_metrics.in_progress_bookings}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600">Completed</span>
                <span className="font-semibold text-green-600">
                  {booking_metrics.completed_bookings}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-red-600">Cancelled</span>
                <span className="font-semibold text-red-600">
                  {booking_metrics.cancelled_bookings}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
