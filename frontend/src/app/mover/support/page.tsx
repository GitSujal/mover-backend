'use client';

import { useState, useEffect } from 'react';
import {
  supportAPI,
  SupportTicketWithComments,
  SupportTicketListResponse,
  IssueStatus,
  IssueType,
  IssuePriority,
  IssueCommentCreate,
} from '@/lib/api/support-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowUpCircle,
  Send,
  ChevronLeft,
  ChevronRight,
  XCircle,
} from 'lucide-react';

// Get org_id from environment variable or use a default for development
const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID || '550e8400-e29b-41d4-a716-446655440000';

export default function SupportPage() {
  const [tickets, setTickets] = useState<SupportTicketListResponse | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicketWithComments | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<IssueStatus | undefined>(undefined);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadTickets();
  }, [currentPage, statusFilter]);

  const loadTickets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await supportAPI.listOrganizationTickets(
        ORG_ID,
        currentPage,
        20,
        statusFilter
      );
      setTickets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load support tickets');
    } finally {
      setLoading(false);
    }
  };

  const loadTicketDetails = async (ticketId: string) => {
    try {
      const data = await supportAPI.getTicket(ticketId);
      setSelectedTicket(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load ticket details');
    }
  };

  const handleAddComment = async () => {
    if (!selectedTicket || !newComment.trim()) return;

    try {
      setActionLoading(true);
      const comment: IssueCommentCreate = {
        comment: newComment,
        is_internal: isInternal,
      };

      await supportAPI.addMoverComment(selectedTicket.id, comment);
      setNewComment('');
      await loadTicketDetails(selectedTicket.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add comment');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (status: IssueStatus) => {
    if (!selectedTicket) return;

    try {
      setActionLoading(true);
      await supportAPI.updateTicket(selectedTicket.id, { status });
      await loadTicketDetails(selectedTicket.id);
      await loadTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveTicket = async () => {
    if (!selectedTicket) return;

    const notes = prompt('Enter resolution notes:');
    if (!notes) return;

    const refundStr = prompt('Enter refund amount (or leave blank for no refund):');
    const refund_amount = refundStr ? parseFloat(refundStr) : undefined;

    try {
      setActionLoading(true);
      await supportAPI.resolveTicket(selectedTicket.id, {
        resolution_notes: notes,
        refund_amount,
      });
      await loadTicketDetails(selectedTicket.id);
      await loadTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalateTicket = async () => {
    if (!selectedTicket) return;

    try {
      setActionLoading(true);
      await supportAPI.escalateTicket(selectedTicket.id);
      await loadTicketDetails(selectedTicket.id);
      await loadTickets();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to escalate ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: IssueStatus) => {
    const variants: Record<
      IssueStatus,
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: any }
    > = {
      [IssueStatus.OPEN]: { variant: 'destructive', icon: AlertCircle },
      [IssueStatus.IN_PROGRESS]: {
        variant: 'outline',
        icon: Clock,
      },
      [IssueStatus.RESOLVED]: {
        variant: 'default',
        icon: CheckCircle2,
      },
      [IssueStatus.CLOSED]: { variant: 'secondary', icon: XCircle },
    };

    const config = variants[status];
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status.replace(/_/g, ' ').toUpperCase()}
      </Badge>
    );
  };

  const getPriorityBadge = (priority: IssuePriority) => {
    const colors: Record<IssuePriority, string> = {
      [IssuePriority.LOW]: 'bg-blue-100 text-blue-800',
      [IssuePriority.MEDIUM]: 'bg-yellow-100 text-yellow-800',
      [IssuePriority.HIGH]: 'bg-orange-100 text-orange-800',
      [IssuePriority.URGENT]: 'bg-red-100 text-red-800',
    };

    return <Badge className={colors[priority]}>{priority.toUpperCase()}</Badge>;
  };

  const getIssueTypeLabel = (type: IssueType): string => {
    const labels: Record<IssueType, string> = {
      [IssueType.DAMAGE]: 'Damage',
      [IssueType.LATE_ARRIVAL]: 'Late Arrival',
      [IssueType.UNPROFESSIONAL_BEHAVIOR]: 'Unprofessional Behavior',
      [IssueType.MISSING_ITEMS]: 'Missing Items',
      [IssueType.BILLING_DISPUTE]: 'Billing Dispute',
      [IssueType.CANCELLATION_REQUEST]: 'Cancellation Request',
      [IssueType.OTHER]: 'Other',
    };
    return labels[type];
  };

  if (loading && !tickets) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Support Tickets</h1>
          <p className="text-muted-foreground">Manage customer support requests</p>
        </div>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-20 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error && !tickets) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={loadTickets} variant="outline" className="mt-4">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Support Tickets</h1>
        <p className="text-muted-foreground">Manage customer support requests and issues</p>
      </div>

      {error && (
        <Card className="mb-4 border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Ticket List */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Tickets ({tickets?.total || 0})</span>
                <div className="flex items-center gap-2">
                  <select
                    value={statusFilter || ''}
                    onChange={(e) =>
                      setStatusFilter(e.target.value ? (e.target.value as IssueStatus) : undefined)
                    }
                    className="text-sm border rounded px-2 py-1"
                  >
                    <option value="">All Status</option>
                    <option value={IssueStatus.OPEN}>Open</option>
                    <option value={IssueStatus.IN_PROGRESS}>In Progress</option>
                    <option value={IssueStatus.RESOLVED}>Resolved</option>
                    <option value={IssueStatus.CLOSED}>Closed</option>
                  </select>
                  <Button onClick={loadTickets} variant="outline" size="sm">
                    Refresh
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {tickets?.tickets.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No support tickets found</p>
                </div>
              ) : (
                <>
                  {tickets?.tickets.map((ticket) => (
                    <Card
                      key={ticket.id}
                      className={`cursor-pointer hover:border-primary transition-colors ${selectedTicket?.id === ticket.id ? 'border-primary' : ''
                        }`}
                      onClick={() => loadTicketDetails(ticket.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="font-medium">{ticket.subject}</p>
                            <p className="text-sm text-muted-foreground">
                              {ticket.customer_name} • {getIssueTypeLabel(ticket.issue_type)}
                            </p>
                          </div>
                          {ticket.is_escalated && (
                            <ArrowUpCircle className="h-5 w-5 text-destructive" />
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(ticket.status)}
                          {getPriorityBadge(ticket.priority)}
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          Created: {new Date(ticket.created_at).toLocaleDateString()}
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {/* Pagination */}
                  {tickets && tickets.pages > 1 && (
                    <div className="flex items-center justify-between pt-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4 mr-1" />
                        Previous
                      </Button>
                      <span className="text-sm text-muted-foreground">
                        Page {currentPage} of {tickets.pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === tickets.pages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Ticket Details */}
        <div>
          {selectedTicket ? (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Ticket Details</span>
                    {selectedTicket.is_escalated && (
                      <Badge variant="destructive">
                        <ArrowUpCircle className="h-3 w-3 mr-1" />
                        Escalated
                      </Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Subject</p>
                    <p className="font-medium text-lg">{selectedTicket.subject}</p>
                  </div>

                  <div>
                    <p className="text-sm text-muted-foreground">Description</p>
                    <p className="text-sm">{selectedTicket.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Customer</p>
                      <p className="text-sm font-medium">{selectedTicket.customer_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {selectedTicket.customer_email}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">Issue Type</p>
                      <p className="text-sm font-medium">
                        {getIssueTypeLabel(selectedTicket.issue_type)}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">Status</p>
                      <div className="mt-1">{getStatusBadge(selectedTicket.status)}</div>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">Priority</p>
                      <div className="mt-1">{getPriorityBadge(selectedTicket.priority)}</div>
                    </div>
                  </div>

                  {selectedTicket.assigned_to_name && (
                    <div>
                      <p className="text-sm text-muted-foreground">Assigned To</p>
                      <p className="text-sm font-medium">{selectedTicket.assigned_to_name}</p>
                    </div>
                  )}

                  {selectedTicket.resolution_notes && (
                    <div>
                      <p className="text-sm text-muted-foreground">Resolution Notes</p>
                      <p className="text-sm">{selectedTicket.resolution_notes}</p>
                    </div>
                  )}

                  {selectedTicket.refund_amount && (
                    <div>
                      <p className="text-sm text-muted-foreground">Refund Issued</p>
                      <p className="text-lg font-bold text-green-600">
                        ${selectedTicket.refund_amount.toFixed(2)}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  {selectedTicket.status !== IssueStatus.RESOLVED &&
                    selectedTicket.status !== IssueStatus.CLOSED && (
                      <div className="space-y-2 pt-4 border-t">
                        <p className="font-medium">Actions</p>
                        <div className="grid grid-cols-2 gap-2">
                          {selectedTicket.status === IssueStatus.OPEN && (
                            <Button
                              onClick={() => handleUpdateStatus(IssueStatus.IN_PROGRESS)}
                              disabled={actionLoading}
                              variant="outline"
                            >
                              <Clock className="h-4 w-4 mr-2" />
                              In Progress
                            </Button>
                          )}
                          <Button
                            onClick={handleResolveTicket}
                            disabled={actionLoading}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Resolve
                          </Button>
                          {!selectedTicket.is_escalated && (
                            <Button
                              onClick={handleEscalateTicket}
                              disabled={actionLoading}
                              variant="destructive"
                            >
                              <ArrowUpCircle className="h-4 w-4 mr-2" />
                              Escalate
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                </CardContent>
              </Card>

              {/* Comments */}
              <Card>
                <CardHeader>
                  <CardTitle>Comments ({selectedTicket.comments.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {selectedTicket.comments.map((comment) => (
                      <div
                        key={comment.id}
                        className={`p-3 rounded-lg ${comment.is_internal
                          ? 'bg-yellow-50 border border-yellow-200'
                          : 'bg-gray-50'
                          }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-medium">
                            {comment.author_name}
                            <span className="text-xs text-muted-foreground ml-2">
                              ({comment.author_type})
                            </span>
                          </p>
                          {comment.is_internal && (
                            <Badge variant="outline" className="text-xs">
                              Internal
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm">{comment.comment}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(comment.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Add Comment */}
                  {selectedTicket.status !== IssueStatus.CLOSED && (
                    <div className="space-y-2 pt-4 border-t">
                      <Label>Add Comment</Label>
                      <Textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Enter your comment..."
                        rows={3}
                      />
                      <div className="flex items-center justify-between">
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={isInternal}
                            onChange={(e) => setIsInternal(e.target.checked)}
                          />
                          Internal comment (not visible to customer)
                        </label>
                        <Button
                          onClick={handleAddComment}
                          disabled={!newComment.trim() || actionLoading}
                          size="sm"
                        >
                          <Send className="h-4 w-4 mr-2" />
                          Send
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-12 text-center text-muted-foreground">
                <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>Select a ticket to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
