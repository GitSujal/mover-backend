import { supportAPI, IssueStatus, IssueType, IssuePriority } from '@/lib/api/support-api';
import { apiClient } from '@/lib/api/client';

// Mock the apiClient
jest.mock('@/lib/api/client');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Support API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('listOrganizationTickets', () => {
    it('fetches organization tickets successfully', async () => {
      const mockResponse = {
        tickets: [
          {
            id: 'ticket-1',
            booking_id: 'booking-1',
            customer_email: 'customer@example.com',
            customer_name: 'John Doe',
            issue_type: IssueType.DAMAGE,
            subject: 'Item damaged during move',
            description: 'My TV was damaged',
            status: IssueStatus.OPEN,
            priority: IssuePriority.HIGH,
            is_escalated: false,
            assigned_to_id: null,
            assigned_to_name: null,
            resolved_at: null,
            resolution_notes: null,
            refund_amount: null,
            refund_issued_at: null,
            created_at: '2025-01-15T10:00:00Z',
            updated_at: '2025-01-15T10:00:00Z',
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.listOrganizationTickets('org-1', 1, 20);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/support/organization/org-1/tickets')
      );
      expect(result).toEqual(mockResponse);
    });

    it('includes status filter in request', async () => {
      const mockResponse = {
        tickets: [],
        total: 0,
        page: 1,
        page_size: 20,
        pages: 1,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

      await supportAPI.listOrganizationTickets('org-1', 1, 20, IssueStatus.OPEN);

      expect(mockedApiClient.get).toHaveBeenCalledWith(expect.stringContaining('status=open'));
    });
  });

  describe('getTicket', () => {
    it('fetches ticket details with comments', async () => {
      const mockResponse = {
        id: 'ticket-1',
        booking_id: 'booking-1',
        customer_email: 'customer@example.com',
        customer_name: 'John Doe',
        issue_type: IssueType.DAMAGE,
        subject: 'Item damaged during move',
        description: 'My TV was damaged',
        status: IssueStatus.OPEN,
        priority: IssuePriority.HIGH,
        is_escalated: false,
        assigned_to_id: null,
        assigned_to_name: null,
        resolved_at: null,
        resolution_notes: null,
        refund_amount: null,
        refund_issued_at: null,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
        comments: [
          {
            id: 'comment-1',
            issue_id: 'ticket-1',
            author_id: 'user-1',
            author_name: 'Support Agent',
            author_type: 'mover',
            comment: 'We are reviewing your case',
            is_internal: false,
            created_at: '2025-01-15T11:00:00Z',
          },
        ],
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.getTicket('ticket-1');

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/support/tickets/ticket-1');
      expect(result).toEqual(mockResponse);
      expect(result.comments).toHaveLength(1);
    });
  });

  describe('updateTicket', () => {
    it('updates ticket status successfully', async () => {
      const mockResponse = {
        id: 'ticket-1',
        status: IssueStatus.IN_PROGRESS,
      } as any;

      mockedApiClient.patch.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.updateTicket('ticket-1', {
        status: IssueStatus.IN_PROGRESS,
      });

      expect(mockedApiClient.patch).toHaveBeenCalledWith('/api/v1/support/tickets/ticket-1', {
        status: IssueStatus.IN_PROGRESS,
      });
      expect(result.status).toBe(IssueStatus.IN_PROGRESS);
    });
  });

  describe('resolveTicket', () => {
    it('resolves ticket with refund', async () => {
      const mockResponse = {
        id: 'ticket-1',
        status: IssueStatus.RESOLVED,
        resolution_notes: 'Issued refund for damaged item',
        refund_amount: 150.0,
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.resolveTicket('ticket-1', {
        resolution_notes: 'Issued refund for damaged item',
        refund_amount: 150.0,
      });

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/support/tickets/ticket-1/resolve',
        {
          resolution_notes: 'Issued refund for damaged item',
          refund_amount: 150.0,
        }
      );
      expect(result.status).toBe(IssueStatus.RESOLVED);
    });
  });

  describe('escalateTicket', () => {
    it('escalates ticket successfully', async () => {
      const mockResponse = {
        id: 'ticket-1',
        is_escalated: true,
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.escalateTicket('ticket-1');

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/support/tickets/ticket-1/escalate'
      );
      expect(result.is_escalated).toBe(true);
    });
  });

  describe('addMoverComment', () => {
    it('adds internal comment successfully', async () => {
      const mockResponse = {
        id: 'comment-1',
        issue_id: 'ticket-1',
        comment: 'Internal note: Customer seems reasonable',
        is_internal: true,
        created_at: '2025-01-15T12:00:00Z',
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.addMoverComment('ticket-1', {
        comment: 'Internal note: Customer seems reasonable',
        is_internal: true,
      });

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/support/tickets/ticket-1/comments/mover',
        {
          comment: 'Internal note: Customer seems reasonable',
          is_internal: true,
        }
      );
      expect(result.is_internal).toBe(true);
    });

    it('adds external comment successfully', async () => {
      const mockResponse = {
        id: 'comment-2',
        issue_id: 'ticket-1',
        comment: 'We will process your refund within 3-5 business days',
        is_internal: false,
        created_at: '2025-01-15T13:00:00Z',
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await supportAPI.addMoverComment('ticket-1', {
        comment: 'We will process your refund within 3-5 business days',
        is_internal: false,
      });

      expect(result.is_internal).toBe(false);
    });
  });

  describe('getStats', () => {
    it('fetches support statistics successfully', async () => {
      const mockStats = {
        total_tickets: 50,
        open_tickets: 10,
        in_progress_tickets: 15,
        resolved_tickets: 20,
        escalated_tickets: 5,
        average_resolution_time_hours: 24,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockStats });

      const result = await supportAPI.getStats();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/support/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('Error Handling', () => {
    it('handles API errors', async () => {
      const mockError = new Error('Network error');
      mockedApiClient.get.mockRejectedValueOnce(mockError);

      await expect(supportAPI.listOrganizationTickets('org-1')).rejects.toThrow('Network error');
    });
  });
});
