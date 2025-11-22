'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, DollarSign, Truck, Users, CalendarDays } from 'lucide-react';
import { analyticsAPI, OrganizationDashboard } from '@/lib/api/analytics-api';
import { authAPI } from '@/lib/api/auth-api';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function MoverDashboard() {
  const [dashboard, setDashboard] = useState<OrganizationDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get current user to get org_id
      const user = await authAPI.getCurrentUser();
      if (!user.org_id) {
        throw new Error('User is not associated with an organization');
      }

      // Get last 30 days by default
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();

      const data = await analyticsAPI.getDashboard(user.org_id, startDate, endDate);
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      console.error('Dashboard error:', err);
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
        <p className="text-red-600">{error}</p>
        <Button onClick={loadDashboard}>Try Again</Button>
      </div>
    );
  }

  if (!dashboard) return null;

  const { booking_metrics, truck_metrics, driver_metrics } = dashboard;

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
            <div className="text-2xl font-bold">{booking_metrics.in_progress_bookings}</div>
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
            <p className="text-xs text-muted-foreground">Trucks active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Drivers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{driver_metrics.active_drivers}</div>
            <p className="text-xs text-muted-foreground">Currently active</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Bookings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {/* We don't have recent bookings in the dashboard summary yet, 
                  so we'll show a placeholder message or we could fetch them separately.
                  For now, let's show a message to check the bookings tab. */}
              <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                <p>View detailed booking history in the Bookings tab.</p>
                <Link href="/mover/jobs" className="mt-2 text-primary-600 hover:underline">
                  Go to Bookings
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Booking Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <CalendarDays className="h-8 w-8 mb-2 opacity-50" />
              <p>Check the Jobs tab for your full schedule.</p>
              <Link href="/mover/jobs" className="mt-2 text-primary-600 hover:underline">
                View Schedule
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
