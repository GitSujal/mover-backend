"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

interface Step3Props {
    onNext: (data: any) => void;
    onBack: () => void;
    bookingData: any;
}

export function Step3Quote({ onNext, onBack, bookingData: _bookingData }: Step3Props) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Your Quote</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="rounded-lg bg-slate-50 p-6">
                    <div className="flex items-baseline justify-between">
                        <span className="text-sm font-medium text-slate-500">Estimated Total</span>
                        <span className="text-3xl font-bold text-slate-900">$1,250.00</span>
                    </div>
                    <Separator className="my-4" />
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-slate-600">Base Rate (4 hours)</span>
                            <span>$600.00</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-600">Mileage (15 miles)</span>
                            <span>$37.50</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-600">Piano Surcharge</span>
                            <span>$150.00</span>
                        </div>
                        <div className="flex justify-between font-medium">
                            <span>Platform Fee</span>
                            <span>$62.50</span>
                        </div>
                    </div>
                </div>

                <div className="flex justify-between">
                    <Button type="button" variant="outline" onClick={onBack}>
                        Back
                    </Button>
                    <Button onClick={() => onNext({})}>Proceed to Booking</Button>
                </div>
            </CardContent>
        </Card>
    );
}
