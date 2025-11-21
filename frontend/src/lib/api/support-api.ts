/**
 * Support Ticket API client
 * Type-safe API calls for support ticket management
 */

import { apiClient } from './client';

export enum IssueType {
  DAMAGE = 'damage',
  LATE_ARRIVAL = 'late_arrival',
  UNPROFESSIONAL_BEHAVIOR = 'unprofessional_behavior',
  MISSING_ITEMS = 'missing_items',
  BILLING_DISPUTE = 'billing_dispute',
  CANCELLATION_REQUEST = 'cancellation_request',
  OTHER = 'other',
}

export enum IssuePriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export enum IssueStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  RESOLVED = 'resolved',
  CLOSED = 'closed',
}

export interface SupportTicketCreate {
  booking_id: string;
  issue_type: IssueType;
  subject: string;
  description: string;
  priority?: IssuePriority;
}

export interface SupportTicketUpdate {
  status?: IssueStatus;
  priority?: IssuePriority;
  assigned_to_id?: string;
}

export interface IssueCommentCreate {
  comment: string;
  is_internal?: boolean;
}

export interface IssueCommentResponse {
  id: string;
  issue_id: string;
  author_id: string | null;
  author_name: string;
  author_type: string;
  comment: string;
  is_internal: boolean;
  created_at: string;
}

export interface SupportTicketResponse {
  id: string;
  booking_id: string;
  customer_email: string;
  customer_name: string;
  issue_type: IssueType;
  subject: string;
  description: string;
  status: IssueStatus;
  priority: IssuePriority;
  is_escalated: boolean;
  assigned_to_id: string | null;
  assigned_to_name: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  refund_amount: number | null;
  refund_issued_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportTicketWithComments extends SupportTicketResponse {
  comments: IssueCommentResponse[];
}

export interface SupportTicketListResponse {
  tickets: SupportTicketResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SupportStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  escalated_tickets: number;
  average_resolution_time_hours: number;
}

export interface ResolveSupportTicketRequest {
  resolution_notes: string;
  refund_amount?: number;
}

export const supportAPI = {
  /**
   * Create support ticket (customer)
   */
  createTicket: async (ticket: SupportTicketCreate): Promise<SupportTicketResponse> => {
    const response = await apiClient.post('/api/v1/support/tickets', ticket);
    return response.data;
  },

  /**
   * Get ticket details with comments
   */
  getTicket: async (ticketId: string): Promise<SupportTicketWithComments> => {
    const response = await apiClient.get(`/api/v1/support/tickets/${ticketId}`);
    return response.data;
  },

  /**
   * Add customer comment
   */
  addComment: async (
    ticketId: string,
    comment: IssueCommentCreate
  ): Promise<IssueCommentResponse> => {
    const response = await apiClient.post(`/api/v1/support/tickets/${ticketId}/comments`, comment);
    return response.data;
  },

  /**
   * List organization tickets (mover)
   */
  listOrganizationTickets: async (
    orgId: string,
    page: number = 1,
    pageSize: number = 20,
    status?: IssueStatus
  ): Promise<SupportTicketListResponse> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (status) {
      params.append('status', status);
    }

    const response = await apiClient.get(
      `/api/v1/support/organization/${orgId}/tickets?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Update ticket (mover/admin)
   */
  updateTicket: async (
    ticketId: string,
    update: SupportTicketUpdate
  ): Promise<SupportTicketResponse> => {
    const response = await apiClient.patch(`/api/v1/support/tickets/${ticketId}`, update);
    return response.data;
  },

  /**
   * Resolve ticket
   */
  resolveTicket: async (
    ticketId: string,
    resolution: ResolveSupportTicketRequest
  ): Promise<SupportTicketResponse> => {
    const response = await apiClient.post(
      `/api/v1/support/tickets/${ticketId}/resolve`,
      resolution
    );
    return response.data;
  },

  /**
   * Escalate ticket
   */
  escalateTicket: async (ticketId: string): Promise<SupportTicketResponse> => {
    const response = await apiClient.post(`/api/v1/support/tickets/${ticketId}/escalate`);
    return response.data;
  },

  /**
   * Add mover comment (internal or external)
   */
  addMoverComment: async (
    ticketId: string,
    comment: IssueCommentCreate
  ): Promise<IssueCommentResponse> => {
    const response = await apiClient.post(
      `/api/v1/support/tickets/${ticketId}/comments/mover`,
      comment
    );
    return response.data;
  },

  /**
   * Get support statistics
   */
  getStats: async (): Promise<SupportStats> => {
    const response = await apiClient.get('/api/v1/support/stats');
    return response.data;
  },
};
