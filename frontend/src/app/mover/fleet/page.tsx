import { FleetTable } from '@/components/mover/FleetTable';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';

export default function FleetPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Fleet Management</h1>
          <p className="text-muted-foreground">Manage your trucks and drivers.</p>
        </div>
        <div className="flex gap-4">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Truck
          </Button>
          <Button variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Add Driver
          </Button>
        </div>
      </div>

      <FleetTable />
    </div>
  );
}
