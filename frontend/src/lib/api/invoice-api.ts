/**
 * Invoice API client
 * Type-safe API calls for invoice management
 */

import { apiClient } from './client';

export enum InvoiceStatus {
  DRAFT = 'draft',
  ISSUED = 'issued',
  PAID = 'paid',
  OVERDUE = 'overdue',
  CANCELLED = 'cancelled',
}

export interface InvoiceCreate {
  booking_id: string;
  notes?: string;
}

export interface InvoiceUpdate {
  status?: InvoiceStatus;
  payment_method?: string;
  notes?: string;
}

export interface InvoiceResponse {
  id: string;
  booking_id: string;
  invoice_number: string;
  subtotal: number;
  platform_fee: number;
  tax_amount: number;
  total_amount: number;
  status: InvoiceStatus;
  issued_at: string;
  paid_at: string | null;
  due_date: string | null;
  payment_method: string | null;
  stripe_invoice_id: string | null;
  stripe_payment_intent_id: string | null;
  pdf_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceListResponse {
  invoices: InvoiceResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface InvoiceStats {
  total_invoices: number;
  draft_invoices: number;
  issued_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  total_revenue: number;
  total_outstanding: number;
  average_invoice_amount: number;
  payment_rate: number;
}

export const invoiceAPI = {
  /**
   * Create invoice for booking
   */
  createInvoice: async (invoice: InvoiceCreate): Promise<InvoiceResponse> => {
    const response = await apiClient.post('/api/v1/invoices', invoice);
    return response.data;
  },

  /**
   * Get invoice by ID
   */
  getInvoice: async (invoiceId: string): Promise<InvoiceResponse> => {
    const response = await apiClient.get(`/api/v1/invoices/${invoiceId}`);
    return response.data;
  },

  /**
   * Get invoice by booking ID (customer)
   */
  getInvoiceByBooking: async (bookingId: string): Promise<InvoiceResponse | null> => {
    const response = await apiClient.get(`/api/v1/invoices/booking/${bookingId}`);
    return response.data;
  },

  /**
   * Update invoice
   */
  updateInvoice: async (invoiceId: string, update: InvoiceUpdate): Promise<InvoiceResponse> => {
    const response = await apiClient.patch(`/api/v1/invoices/${invoiceId}`, update);
    return response.data;
  },

  /**
   * Mark invoice as paid
   */
  markAsPaid: async (
    invoiceId: string,
    paymentMethod: string = 'stripe'
  ): Promise<InvoiceResponse> => {
    const params = new URLSearchParams();
    params.append('payment_method', paymentMethod);

    const response = await apiClient.post(
      `/api/v1/invoices/${invoiceId}/mark-paid?${params.toString()}`
    );
    return response.data;
  },

  /**
   * List organization invoices
   */
  listOrganizationInvoices: async (
    orgId: string,
    page: number = 1,
    pageSize: number = 20,
    statusFilter?: InvoiceStatus
  ): Promise<InvoiceListResponse> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }

    const response = await apiClient.get(
      `/api/v1/invoices/organization/${orgId}/list?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get organization invoice statistics
   */
  getOrganizationStats: async (orgId: string): Promise<InvoiceStats> => {
    const response = await apiClient.get(`/api/v1/invoices/organization/${orgId}/stats`);
    return response.data;
  },

  /**
   * Download invoice PDF
   */
  getInvoicePdfUrl: (invoiceId: string): string => {
    // Returns the URL for PDF download
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${baseUrl}/api/v1/invoices/${invoiceId}/pdf`;
  },
};
