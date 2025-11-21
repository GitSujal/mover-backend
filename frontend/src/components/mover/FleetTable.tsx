'use client';

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
import { Edit, Trash2 } from 'lucide-react';

interface FleetItem {
  id: string;
  type: 'truck' | 'driver';
  name: string; // License plate or Driver Name
  details: string; // Model or License Number
  status: string;
  lastActive?: string;
}

const mockFleet: FleetItem[] = [
  {
    id: '1',
    type: 'truck',
    name: 'TEST123',
    details: 'Ford F-650 (Large)',
    status: 'Available',
    lastActive: 'Today, 2:00 PM',
  },
  {
    id: '2',
    type: 'truck',
    name: 'MOVE999',
    details: 'Isuzu NPR (Medium)',
    status: 'In Use',
    lastActive: 'Currently Active',
  },
  {
    id: '3',
    type: 'driver',
    name: 'John Driver',
    details: 'DL: D1234567',
    status: 'Active',
    lastActive: 'Today, 9:00 AM',
  },
  {
    id: '4',
    type: 'driver',
    name: 'Jane Mover',
    details: 'DL: M9876543',
    status: 'Off Duty',
    lastActive: 'Yesterday',
  },
];

export function FleetTable() {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Type</TableHead>
            <TableHead>Name / ID</TableHead>
            <TableHead>Details</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Last Active</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mockFleet.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium capitalize">{item.type}</TableCell>
              <TableCell>{item.name}</TableCell>
              <TableCell>{item.details}</TableCell>
              <TableCell>
                <Badge
                  variant={
                    item.status === 'Available' || item.status === 'Active'
                      ? 'default'
                      : item.status === 'In Use'
                        ? 'secondary'
                        : 'outline'
                  }
                >
                  {item.status}
                </Badge>
              </TableCell>
              <TableCell>{item.lastActive}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="icon">
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive">
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
