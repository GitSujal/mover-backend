import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CalendarDays, MapPin } from 'lucide-react';

export default function JobsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Jobs & Schedule</h1>
        <p className="text-muted-foreground">View and manage your upcoming moves.</p>
      </div>

      <div className="grid gap-6">
        {/* Mock Job Card */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="space-y-1">
              <CardTitle className="text-lg font-medium">Move #1234 - Olivia Martin</CardTitle>
              <div className="flex items-center text-sm text-muted-foreground">
                <CalendarDays className="mr-2 h-4 w-4" />
                Today, 2:00 PM - 6:00 PM
              </div>
            </div>
            <Badge>In Progress</Badge>
          </CardHeader>
          <CardContent>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="text-sm font-medium">Pickup</div>
                <div className="flex items-start text-sm text-muted-foreground">
                  <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                  123 Start St, San Francisco, CA 94102
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Dropoff</div>
                <div className="flex items-start text-sm text-muted-foreground">
                  <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                  456 End Ave, Oakland, CA 94601
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="space-y-1">
              <CardTitle className="text-lg font-medium">Move #1235 - Jackson Lee</CardTitle>
              <div className="flex items-center text-sm text-muted-foreground">
                <CalendarDays className="mr-2 h-4 w-4" />
                Tomorrow, 9:00 AM - 1:00 PM
              </div>
            </div>
            <Badge variant="outline">Confirmed</Badge>
          </CardHeader>
          <CardContent>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="text-sm font-medium">Pickup</div>
                <div className="flex items-start text-sm text-muted-foreground">
                  <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                  789 Main St, San Francisco, CA 94103
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Dropoff</div>
                <div className="flex items-start text-sm text-muted-foreground">
                  <MapPin className="mr-2 h-4 w-4 shrink-0 text-primary" />
                  321 Oak Ave, Berkeley, CA 94704
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
