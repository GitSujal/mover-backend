'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Package, Clock, Shield, DollarSign } from 'lucide-react';

import { useEffect, useState } from 'react';

export default function HomePage() {
  const [hasActiveBooking, setHasActiveBooking] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setHasActiveBooking(localStorage.getItem('hasActiveBooking') === 'true');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Package className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">MoveHub</span>
          </div>
          <nav className="flex items-center space-x-6">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-gray-600 hover:text-primary-600 transition-colors"
            >
              Track Booking
            </Link>
            <Link
              href="/mover/onboarding"
              className="text-sm font-medium text-gray-600 hover:text-primary-600 transition-colors"
            >
              For Movers
            </Link>
            <Link href="/signin">
              <Button variant="outline" size="sm">
                Sign In
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Professional Moving Services
            <span className="block text-primary-600 mt-2">Made Simple</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Book verified moving companies with transparent pricing, real-time tracking, and
            hassle-free service. No account needed—get started in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {hasActiveBooking ? (
              <Link href="/dashboard">
                <Button size="lg" className="w-full sm:w-auto">
                  Track My Booking
                </Button>
              </Link>
            ) : (
              <Link href="/book">
                <Button size="lg" className="w-full sm:w-auto">
                  Book a Move
                </Button>
              </Link>
            )}
            {!hasActiveBooking && (
              <Link href="/dashboard">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Track My Booking
                </Button>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                  <Shield className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Verified Companies</h3>
                <p className="text-sm text-gray-600">
                  All moving companies are licensed, insured, and background-checked
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                  <DollarSign className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Transparent Pricing</h3>
                <p className="text-sm text-gray-600">
                  No hidden fees. Get instant price estimates based on your move details
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                  <Clock className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Real-Time Tracking</h3>
                <p className="text-sm text-gray-600">
                  Track your booking status and driver location in real-time
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="h-12 w-12 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                  <Package className="h-6 w-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-lg mb-2">Easy Booking</h3>
                <p className="text-sm text-gray-600">
                  No account required. Book your move in just a few simple steps
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-16 mb-20">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="step-number mx-auto mb-4">1</div>
            <h3 className="font-semibold text-lg mb-2">Enter Move Details</h3>
            <p className="text-sm text-gray-600">
              Tell us about your move - pickup, dropoff, dates, and special items
            </p>
          </div>
          <div className="text-center">
            <div className="step-number mx-auto mb-4">2</div>
            <h3 className="font-semibold text-lg mb-2">Get Instant Quote</h3>
            <p className="text-sm text-gray-600">
              Receive transparent pricing with detailed breakdown of all costs
            </p>
          </div>
          <div className="text-center">
            <div className="step-number mx-auto mb-4">3</div>
            <h3 className="font-semibold text-lg mb-2">Confirm & Track</h3>
            <p className="text-sm text-gray-600">
              Confirm your booking and track your driver in real-time
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Package className="h-6 w-6" />
              <span className="text-xl font-bold">MoveHub</span>
            </div>
            <p className="text-gray-400 text-sm">© 2025 MoveHub. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
