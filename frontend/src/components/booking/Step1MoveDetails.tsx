'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Step1Props {
  onNext: (data: any) => void;
  defaultValues?: any;
}

export function Step1MoveDetails({ onNext, defaultValues }: Step1Props) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, use react-hook-form
    onNext({
      pickup: '123 Start St',
      dropoff: '456 End Ave',
      date: '2024-01-01',
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Move Details</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="pickup">Pickup Address</Label>
              <Input
                id="pickup"
                placeholder="Enter pickup address"
                defaultValue={defaultValues?.pickup}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dropoff">Dropoff Address</Label>
              <Input
                id="dropoff"
                placeholder="Enter dropoff address"
                defaultValue={defaultValues?.dropoff}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="date">Move Date</Label>
            <Input id="date" type="date" defaultValue={defaultValues?.date} required />
          </div>

          <div className="flex justify-end">
            <Button type="submit">Next: Inventory</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
