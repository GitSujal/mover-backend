"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Step4Props {
    onBack: () => void;
    bookingData: any;
}

export function Step4Review({ onBack, bookingData: _bookingData }: Step4Props) {
    const handleBook = () => {
        alert("Booking Confirmed! (Mock)");
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
                        <Input id="name" placeholder="John Doe" />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" placeholder="john@example.com" />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input id="phone" type="tel" placeholder="+1 (555) 000-0000" />
                    </div>
                </div>

                <div className="flex justify-between pt-4">
                    <Button type="button" variant="outline" onClick={onBack}>
                        Back
                    </Button>
                    <Button onClick={handleBook} className="bg-green-600 hover:bg-green-700">
                        Confirm Booking
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
