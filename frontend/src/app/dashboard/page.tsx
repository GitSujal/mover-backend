"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MapPin, CalendarDays, Package, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { bookingAPI } from "@/lib/api/booking-api";
import { BookingWithDetails } from "@/types/booking";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function CustomerDashboard() {
    const [bookings, setBookings] = useState<BookingWithDetails[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadBookings();
    }, []);

    const loadBookings = async () => {
        try {
            setLoading(true);
            const data = await bookingAPI.listBookings();
            setBookings(data);
        } catch (err) {
            console.error("Failed to load bookings:", err);
            setError("Failed to load your bookings. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 py-12 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 py-12">
                <div className="mx-auto max-w-4xl px-4 text-center">
                    <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <Button onClick={loadBookings}>Try Again</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12">
            <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-gray-900">My Moves</h1>
                        <p className="mt-2 text-gray-600">Track your current move and view history.</p>
                    </div>
                    <Link href="/book">
                        <Button>Book New Move</Button>
                    </Link>
                </div>

                {bookings.length === 0 ? (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <Package className="h-12 w-12 text-gray-400 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No bookings found</h3>
                            <p className="text-gray-500 mb-6">You haven't made any bookings yet.</p>
                            <Link href="/book">
                                <Button>Book Your First Move</Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="space-y-6">
                        {bookings.map((booking) => (
                            <Card key={booking.id}>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <div className="space-y-1">
                                        <CardTitle className="text-lg font-medium">Move #{booking.id.slice(0, 8)}</CardTitle>
                                        <div className="flex items-center text-sm text-muted-foreground">
                                            <CalendarDays className="mr-2 h-4 w-4" />
                                            {new Date(booking.move_date).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <Badge variant={booking.status === "PENDING" ? "secondary" : "default"}>
                                        {booking.status}
                                    </Badge>
                                </CardHeader>
                                <CardContent>
                                    <div className="mt-4 grid gap-6 md:grid-cols-2">
                                        <div className="space-y-4">
                                            <div className="space-y-2">
                                                <div className="text-sm font-medium text-gray-500">Pickup</div>
                                                <div className="flex items-start">
                                                    <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary-600" />
                                                    <span>{booking.pickup_address}, {booking.pickup_city}, {booking.pickup_state}</span>
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                <div className="text-sm font-medium text-gray-500">Dropoff</div>
                                                <div className="flex items-start">
                                                    <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary-600" />
                                                    <span>{booking.dropoff_address}, {booking.dropoff_city}, {booking.dropoff_state}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            <div className="space-y-2">
                                                <div className="text-sm font-medium text-gray-500">Details</div>
                                                <div className="flex items-start">
                                                    <Package className="mr-2 h-4 w-4 shrink-0 text-primary-600" />
                                                    <span>{booking.special_items?.length ? booking.special_items.join(", ") : "Standard Move"}</span>
                                                </div>
                                            </div>
                                            <div className="space-y-2">
                                                <div className="text-sm font-medium text-gray-500">Estimated Price</div>
                                                <div className="text-lg font-bold">
                                                    {booking.price_estimate?.breakdown?.total
                                                        ? `$${booking.price_estimate.breakdown.total.toFixed(2)}`
                                                        : "Pending Quote"}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
