"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { moverAPI, OrganizationCreate } from "@/lib/api/mover-api";
import { useToast } from "@/components/ui/use-toast";
import { Loader2 } from "lucide-react";

export default function MoverOnboardingPage() {
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData(e.currentTarget);
        const data: OrganizationCreate = {
            name: formData.get('companyName') as string,
            email: formData.get('email') as string,
            phone: formData.get('phone') as string,
            business_license_number: formData.get('license') as string,
            tax_id: 'PENDING', // Simplified for now
            address_line1: formData.get('address') as string,
            city: 'San Francisco', // Simplified
            state: 'CA', // Simplified
            zip_code: '94105', // Simplified
        };

        try {
            await moverAPI.createOrganization(data);
            setSubmitted(true);
            toast({
                title: "Application Submitted",
                description: "We have received your application and will be in touch soon.",
            });
        } catch (error) {
            console.error('Error submitting application:', error);
            toast({
                title: "Submission Failed",
                description: "There was an error submitting your application. Please try again.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="min-h-screen bg-gray-50 py-12 flex items-center justify-center">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle className="text-green-600">Application Received!</CardTitle>
                        <CardDescription>
                            Thanks for your interest in joining MoveHub. Our team will review your application and contact you shortly.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button className="w-full" onClick={() => window.location.href = '/'}>
                            Return Home
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12">
            <div className="mx-auto max-w-2xl px-4">
                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold text-gray-900">Join MoveHub Network</h1>
                    <p className="mt-2 text-gray-600">Grow your moving business with high-quality leads.</p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Company Registration</CardTitle>
                        <CardDescription>Enter your business details to get started.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label htmlFor="companyName">Company Name</Label>
                                    <Input id="companyName" name="companyName" required placeholder="Acme Movers" />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="license">Business License #</Label>
                                    <Input id="license" name="license" required placeholder="BL-123456" />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Business Email</Label>
                                <Input id="email" name="email" type="email" required placeholder="contact@acmemovers.com" />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="phone">Phone Number</Label>
                                <Input id="phone" name="phone" type="tel" required placeholder="+1 (555) 000-0000" />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="address">Headquarters Address</Label>
                                <Input id="address" name="address" required placeholder="123 Main St, City, State" />
                            </div>

                            <div className="pt-4">
                                <Button type="submit" className="w-full" size="lg" disabled={loading}>
                                    {loading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Submitting...
                                        </>
                                    ) : (
                                        "Submit Application"
                                    )}
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
