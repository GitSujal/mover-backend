'use client';

import { useEffect, useState } from 'react';
import { analyticsAPI, OrganizationDashboard } from '@/lib/api/analytics-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  BarChart3,
  TrendingUp,
  Users,
  Truck,
  Star,
  MessageSquare,
  FileText,
  CheckCircle,
} from 'lucide-react';

// Mock org ID - in production, this would come from auth context
const MOCK_ORG_ID = '550e8400-e29b-41d4-a716-446655440000';

export default function AnalyticsPage() {
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
      // Get last 30 days by default
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();

      const data = await analyticsAPI.getDashboard(MOCK_ORG_ID, startDate, endDate);
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
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">Loading your business insights...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-red-600">{error || 'Failed to load dashboard'}</p>
        </div>
      </div>
    );
  }

  const {
    booking_metrics,
    driver_metrics,
    truck_metrics,
    rating_metrics,
    support_metrics,
    invoice_metrics,
    verification_metrics,
  } = dashboard;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <p className="text-muted-foreground">{dashboard.org_name} • Last 30 days</p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
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
            <CardTitle className="text-sm font-medium">Total Bookings</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{booking_metrics.total_bookings}</div>
            <p className="text-xs text-muted-foreground">
              {booking_metrics.completion_rate.toFixed(1)}% completion rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Rating</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rating_metrics.average_rating.toFixed(1)}/5.0</div>
            <p className="text-xs text-muted-foreground">
              From {rating_metrics.total_ratings} reviews
            </p>
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

      {/* Booking Metrics */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Booking Status</CardTitle>
            <CardDescription>Distribution of bookings by status</CardDescription>
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

        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>Key performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Completion Rate</span>
                  <span className="font-semibold">
                    {booking_metrics.completion_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${booking_metrics.completion_rate}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">Cancellation Rate</span>
                  <span className="font-semibold">
                    {booking_metrics.cancellation_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{ width: `${booking_metrics.cancellation_rate}%` }}
                  />
                </div>
              </div>
              <div className="pt-2 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Avg Booking Value</span>
                  <span className="font-semibold">
                    ${booking_metrics.average_booking_value.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fleet & Ratings */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Truck className="h-5 w-5" />
              Fleet Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Total Trucks</span>
                <span className="font-semibold">{truck_metrics.total_trucks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Active</span>
                <span className="font-semibold text-green-600">{truck_metrics.active_trucks}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Utilization</span>
                <span className="font-semibold">
                  {truck_metrics.average_utilization.toFixed(1)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5" />
              Rating Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[5, 4, 3, 2, 1].map((stars) => (
                <div key={stars} className="flex items-center gap-2">
                  <span className="text-sm w-12">{stars} stars</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{
                        width: `${((rating_metrics[`${['one', 'two', 'three', 'four', 'five'][stars - 1]}_star_count` as keyof typeof rating_metrics] as number) / Math.max(rating_metrics.total_ratings, 1)) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-8">
                    {
                      rating_metrics[
                        `${['one', 'two', 'three', 'four', 'five'][stars - 1]}_star_count` as keyof typeof rating_metrics
                      ]
                    }
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Performers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {driver_metrics.top_performers.slice(0, 3).map((driver, index) => (
                <div key={driver.driver_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-muted-foreground">
                      #{index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium">{driver.driver_name}</p>
                      <p className="text-xs text-muted-foreground">{driver.total_bookings} jobs</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                    <span className="text-sm font-semibold">
                      {driver.average_rating.toFixed(1)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Support & Invoices & Verification */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Support Tickets
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Total</span>
                <span className="font-semibold">{support_metrics.total_tickets}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-yellow-600">Open</span>
                <span className="font-semibold text-yellow-600">
                  {support_metrics.open_tickets}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-blue-600">In Progress</span>
                <span className="font-semibold text-blue-600">
                  {support_metrics.in_progress_tickets}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-green-600">Resolved</span>
                <span className="font-semibold text-green-600">
                  {support_metrics.resolved_tickets}
                </span>
              </div>
              <div className="flex justify-between pt-2 border-t">
                <span className="text-sm">Avg Resolution</span>
                <span className="font-semibold">
                  {support_metrics.average_resolution_hours.toFixed(1)}h
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Invoices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Total</span>
                <span className="font-semibold">{invoice_metrics.total_invoices}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-green-600">Paid</span>
                <span className="font-semibold text-green-600">
                  {invoice_metrics.paid_invoices}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-red-600">Overdue</span>
                <span className="font-semibold text-red-600">
                  {invoice_metrics.overdue_invoices}
                </span>
              </div>
              <div className="flex justify-between pt-2 border-t">
                <span className="text-sm">Payment Rate</span>
                <span className="font-semibold">{invoice_metrics.payment_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Outstanding</span>
                <span className="font-semibold">
                  ${invoice_metrics.total_outstanding.toLocaleString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-yellow-600">Pending</span>
                <span className="font-semibold text-yellow-600">
                  {verification_metrics.pending_verifications}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-blue-600">Under Review</span>
                <span className="font-semibold text-blue-600">
                  {verification_metrics.under_review_verifications}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-green-600">Approved</span>
                <span className="font-semibold text-green-600">
                  {verification_metrics.approved_verifications}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-red-600">Rejected</span>
                <span className="font-semibold text-red-600">
                  {verification_metrics.rejected_verifications}
                </span>
              </div>
              <div className="flex justify-between pt-2 border-t">
                <span className="text-sm">Expiring Soon</span>
                <span className="font-semibold text-orange-600">
                  {verification_metrics.expiring_soon_count}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
