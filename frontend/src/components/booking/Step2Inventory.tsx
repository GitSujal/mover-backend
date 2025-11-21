'use client';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';

interface Step2Props {
  onNext: (data: any) => void;
  onBack: () => void;
  defaultValues?: any;
}

export function Step2Inventory({ onNext, onBack, defaultValues: _defaultValues }: Step2Props) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      specialItems: ['piano'],
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Inventory & Special Items</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <Label>Do you have any of these items?</Label>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center space-x-2">
                <Checkbox id="piano" />
                <Label htmlFor="piano">Piano</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="pool_table" />
                <Label htmlFor="pool_table">Pool Table</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="safe" />
                <Label htmlFor="safe">Heavy Safe</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="artwork" />
                <Label htmlFor="artwork">Valuable Artwork</Label>
              </div>
            </div>
          </div>

          <div className="flex justify-between">
            <Button type="button" variant="outline" onClick={onBack}>
              Back
            </Button>
            <Button type="submit">Next: Get Quote</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
