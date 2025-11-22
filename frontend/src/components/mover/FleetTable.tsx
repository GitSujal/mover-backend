'use client';

import { useState, useEffect } from 'react';
import { fleetAPI, TruckResponse, DriverResponse } from '@/lib/api/fleet-api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit, Trash2, Truck as TruckIcon, User } from 'lucide-react';

type FleetItem = {
  id: string;
  type: 'truck' | 'driver';
  name: string;
  details: string;
  status: string;
  lastActive?: string;
};

export function FleetTable() {
  const [fleet, setFleet] = useState<FleetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFleetData();
  }, []);

  const loadFleetData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [trucks, drivers] = await Promise.all([
        fleetAPI.listTrucks(),
        fleetAPI.listDrivers(),
      ]);

      const fleetItems: FleetItem[] = [
        ...trucks.map((truck: TruckResponse) => ({
          id: truck.id,
          type: 'truck' as const,
          name: truck.license_plate,
          details: `${truck.make} ${truck.model} (${truck.year}) - ${truck.capacity_cubic_feet} cu ft`,
          status: truck.is_available ? 'Available' : 'In Use',
          lastActive: new Date(truck.updated_at).toLocaleString(),
        })),
        ...drivers.map((driver: DriverResponse) => ({
          id: driver.id,
          type: 'driver' as const,
          name: `${driver.first_name} ${driver.last_name}`,
          details: `DL: ${driver.drivers_license_number}${driver.has_cdl ? ` (CDL Class ${driver.cdl_class})` : ''}`,
          status: driver.is_available ? 'Available' : 'On Duty',
          lastActive: new Date(driver.updated_at).toLocaleString(),
        })),
      ];

      setFleet(fleetItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load fleet data');
      console.error('Fleet loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-muted-foreground">Loading fleet data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive p-8 text-center">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={loadFleetData} variant="outline">
          Try Again
        </Button>
      </div>
    );
  }

  if (fleet.length === 0) {
    return (
      <div className="rounded-md border p-12 text-center">
        <div className="flex justify-center mb-4 gap-4">
          <TruckIcon className="h-12 w-12 text-muted-foreground opacity-50" />
          <User className="h-12 w-12 text-muted-foreground opacity-50" />
        </div>
        <p className="text-muted-foreground mb-2">No trucks or drivers found</p>
        <p className="text-sm text-muted-foreground">Add your first truck or driver to get started</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Type</TableHead>
            <TableHead>Name / ID</TableHead>
            <TableHead>Details</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Updated</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {fleet.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  {item.type === 'truck' ? (
                    <TruckIcon className="h-4 w-4" />
                  ) : (
                    <User className="h-4 w-4" />
                  )}
                  <span className="capitalize">{item.type}</span>
                </div>
              </TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell>{item.details}</TableCell>
              <TableCell>
                <Badge
                  variant={
                    item.status === 'Available'
                      ? 'default'
                      : item.status === 'In Use' || item.status === 'On Duty'
                        ? 'secondary'
                        : 'outline'
                  }
                >
                  {item.status}
                </Badge>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">{item.lastActive}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="icon" title="Edit">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive" title="Delete">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
