import { verificationAPI, VerificationStatus, DocumentType } from '@/lib/api/verification-api';
import { apiClient } from '@/lib/api/client';

// Mock the apiClient
jest.mock('@/lib/api/client');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Verification API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('submitOrganizationDocument', () => {
    it('submits organization document successfully', async () => {
      const mockResponse = {
        id: 'doc-1',
        org_id: 'org-1',
        driver_id: null,
        document_type: DocumentType.BUSINESS_LICENSE,
        document_url: 'https://example.com/license.pdf',
        document_number: 'BL-12345',
        expiry_date: '2026-01-15',
        status: VerificationStatus.PENDING,
        submitted_at: '2025-01-15T10:00:00Z',
        reviewed_at: null,
        reviewer_id: null,
        review_notes: null,
        rejection_reason: null,
        expiry_reminder_sent_at: null,
        additional_data: null,
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      };

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.submitOrganizationDocument('org-1', {
        document_type: DocumentType.BUSINESS_LICENSE,
        document_url: 'https://example.com/license.pdf',
        document_number: 'BL-12345',
        expiry_date: '2026-01-15',
      });

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/verification/organization/org-1/documents',
        {
          document_type: DocumentType.BUSINESS_LICENSE,
          document_url: 'https://example.com/license.pdf',
          document_number: 'BL-12345',
          expiry_date: '2026-01-15',
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('submitDriverDocument', () => {
    it('submits driver document successfully', async () => {
      const mockResponse = {
        id: 'doc-2',
        org_id: null,
        driver_id: 'driver-1',
        document_type: DocumentType.DRIVERS_LICENSE,
        document_url: 'https://example.com/dl.pdf',
        status: VerificationStatus.PENDING,
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.submitDriverDocument('driver-1', {
        document_type: DocumentType.DRIVERS_LICENSE,
        document_url: 'https://example.com/dl.pdf',
      });

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/verification/driver/driver-1/documents',
        {
          document_type: DocumentType.DRIVERS_LICENSE,
          document_url: 'https://example.com/dl.pdf',
        }
      );
      expect(result.driver_id).toBe('driver-1');
    });
  });

  describe('listPendingVerifications', () => {
    it('fetches pending verifications successfully', async () => {
      const mockResponse = {
        verifications: [
          {
            id: 'doc-1',
            org_id: 'org-1',
            driver_id: null,
            document_type: DocumentType.BUSINESS_LICENSE,
            status: VerificationStatus.PENDING,
            submitted_at: '2025-01-15T10:00:00Z',
          } as any,
        ],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.listPendingVerifications(1, 20);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/verification/documents/pending')
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('reviewDocument', () => {
    it('approves document successfully', async () => {
      const mockResponse = {
        id: 'doc-1',
        status: VerificationStatus.APPROVED,
        reviewed_at: '2025-01-16T10:00:00Z',
        review_notes: 'Document verified and approved',
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.reviewDocument('doc-1', {
        status: VerificationStatus.APPROVED,
        review_notes: 'Document verified and approved',
      });

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/verification/documents/doc-1/review',
        {
          status: VerificationStatus.APPROVED,
          review_notes: 'Document verified and approved',
        }
      );
      expect(result.status).toBe(VerificationStatus.APPROVED);
    });

    it('rejects document with reason', async () => {
      const mockResponse = {
        id: 'doc-1',
        status: VerificationStatus.REJECTED,
        reviewed_at: '2025-01-16T10:00:00Z',
        rejection_reason: 'Document is expired',
      } as any;

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.reviewDocument('doc-1', {
        status: VerificationStatus.REJECTED,
        rejection_reason: 'Document is expired',
      });

      expect(result.status).toBe(VerificationStatus.REJECTED);
      expect(result.rejection_reason).toBe('Document is expired');
    });
  });

  describe('getOrganizationStatus', () => {
    it('fetches organization verification status', async () => {
      const mockStatus = {
        org_id: 'org-1',
        business_name: 'ABC Moving Company',
        is_verified: false,
        required_documents: {
          business_license: true,
          liability_insurance: true,
          workers_comp_insurance: false,
        },
        missing_documents: ['workers_comp_insurance'],
        expiring_documents: [],
        total_documents: 2,
        approved_documents: 2,
        pending_documents: 0,
        rejected_documents: 0,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockStatus });

      const result = await verificationAPI.getOrganizationStatus('org-1');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/verification/organization/org-1/status'
      );
      expect(result).toEqual(mockStatus);
    });
  });

  describe('getDriverStatus', () => {
    it('fetches driver verification status', async () => {
      const mockStatus = {
        driver_id: 'driver-1',
        driver_name: 'John Doe',
        is_verified: true,
        required_documents: {
          drivers_license: true,
          background_check: true,
        },
        missing_documents: [],
        expiring_documents: ['drivers_license'],
        total_documents: 2,
        approved_documents: 2,
        pending_documents: 0,
        rejected_documents: 0,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockStatus });

      const result = await verificationAPI.getDriverStatus('driver-1');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/verification/driver/driver-1/status'
      );
      expect(result).toEqual(mockStatus);
    });
  });

  describe('getStats', () => {
    it('fetches verification statistics', async () => {
      const mockStats = {
        total_pending: 10,
        total_under_review: 5,
        total_approved: 50,
        total_rejected: 3,
        total_expired: 2,
        documents_expiring_soon: 4,
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockStats });

      const result = await verificationAPI.getStats();

      expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/verification/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('previewExpiringDocuments', () => {
    it('previews expiring documents successfully', async () => {
      const mockPreview = {
        total_expiring: 3,
        days_threshold: 30,
        documents: [
          {
            verification_id: 'doc-1',
            document_type: 'drivers_license',
            expiry_date: '2025-02-10',
            days_until_expiry: 25,
            org_id: null,
            driver_id: 'driver-1',
          },
        ],
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockPreview });

      const result = await verificationAPI.previewExpiringDocuments(30);

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/verification/expiry-reminders/preview')
      );
      expect(mockedApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('days_threshold=30')
      );
      expect(result).toEqual(mockPreview);
    });
  });

  describe('sendExpiryReminders', () => {
    it('sends expiry reminders successfully', async () => {
      const mockResponse = {
        total_expiring: 3,
        reminders_sent: 3,
        days_threshold: 30,
      };

      mockedApiClient.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await verificationAPI.sendExpiryReminders(30);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/verification/expiry-reminders/send')
      );
      expect(result.reminders_sent).toBe(3);
    });
  });

  describe('Error Handling', () => {
    it('handles API errors', async () => {
      const mockError = new Error('Network error');
      mockedApiClient.get.mockRejectedValueOnce(mockError);

      await expect(verificationAPI.listPendingVerifications()).rejects.toThrow('Network error');
    });
  });
});
