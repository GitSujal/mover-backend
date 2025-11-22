'use client';

import { useState, useEffect } from 'react';
import {
  invoiceAPI,
  InvoiceResponse,
  InvoiceListResponse,
  InvoiceStatus,
} from '@/lib/api/invoice-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  Download,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';

// Get org_id from environment variable or use a default for development
const ORG_ID = process.env.NEXT_PUBLIC_ORG_ID || '550e8400-e29b-41d4-a716-446655440000';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<InvoiceListResponse | null>(null);
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | undefined>(undefined);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadInvoices();
  }, [currentPage, statusFilter]);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await invoiceAPI.listOrganizationInvoices(
        ORG_ID,
        currentPage,
        20,
        statusFilter
      );
      setInvoices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const loadInvoiceDetails = async (invoiceId: string) => {
    try {
      const data = await invoiceAPI.getInvoice(invoiceId);
      setSelectedInvoice(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invoice details');
    }
  };

  const handleMarkAsPaid = async () => {
    if (!selectedInvoice) return;

    const paymentMethod = prompt('Enter payment method (e.g., cash, check, stripe):') || 'manual';

    try {
      setActionLoading(true);
      await invoiceAPI.markAsPaid(selectedInvoice.id, paymentMethod);
      await loadInvoiceDetails(selectedInvoice.id);
      await loadInvoices();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark invoice as paid');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadPDF = (invoiceId: string) => {
    const pdfUrl = invoiceAPI.getInvoicePdfUrl(invoiceId);
    window.open(pdfUrl, '_blank');
  };

  const getStatusBadge = (status: InvoiceStatus) => {
    const variants: Record<
      InvoiceStatus,
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: any }
    > = {
      [InvoiceStatus.DRAFT]: { variant: 'secondary', icon: FileText },
      [InvoiceStatus.ISSUED]: { variant: 'outline', icon: Clock },
      [InvoiceStatus.PAID]: {
        variant: 'default',
        icon: CheckCircle2,
      },
      [InvoiceStatus.OVERDUE]: {
        variant: 'destructive',
        icon: AlertCircle,
      },
      [InvoiceStatus.CANCELLED]: {
        variant: 'destructive',
        icon: XCircle,
      },
    };

    const config = variants[status];
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status.toUpperCase()}
      </Badge>
    );
  };

  if (loading && !invoices) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Invoices</h1>
          <p className="text-muted-foreground">Manage invoices and payments</p>
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

  if (error && !invoices) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
            </div>
            <Button onClick={loadInvoices} variant="outline" className="mt-4">
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
        <h1 className="text-3xl font-bold tracking-tight">Invoices</h1>
        <p className="text-muted-foreground">Manage invoices and track payments</p>
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
        {/* Invoice List */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Invoices ({invoices?.total || 0})</span>
                <div className="flex items-center gap-2">
                  <select
                    value={statusFilter || ''}
                    onChange={(e) =>
                      setStatusFilter(
                        e.target.value ? (e.target.value as InvoiceStatus) : undefined
                      )
                    }
                    className="text-sm border rounded px-2 py-1"
                  >
                    <option value="">All Status</option>
                    <option value={InvoiceStatus.DRAFT}>Draft</option>
                    <option value={InvoiceStatus.ISSUED}>Issued</option>
                    <option value={InvoiceStatus.PAID}>Paid</option>
                    <option value={InvoiceStatus.OVERDUE}>Overdue</option>
                    <option value={InvoiceStatus.CANCELLED}>Cancelled</option>
                  </select>
                  <Button onClick={loadInvoices} variant="outline" size="sm">
                    Refresh
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {invoices?.invoices.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No invoices found</p>
                </div>
              ) : (
                <>
                  {invoices?.invoices.map((invoice) => (
                    <Card
                      key={invoice.id}
                      className={`cursor-pointer hover:border-primary transition-colors ${selectedInvoice?.id === invoice.id ? 'border-primary' : ''
                        }`}
                      onClick={() => loadInvoiceDetails(invoice.id)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="font-medium">{invoice.invoice_number}</p>
                            <p className="text-sm text-muted-foreground">
                              Booking: {invoice.booking_id.slice(0, 8)}
                              ...
                            </p>
                          </div>
                          {getStatusBadge(invoice.status)}
                        </div>
                        <div className="flex items-center justify-between">
                          <p className="text-lg font-bold">${invoice.total_amount.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(invoice.issued_at).toLocaleDateString()}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {/* Pagination */}
                  {invoices && invoices.pages > 1 && (
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
                        Page {currentPage} of {invoices.pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(currentPage + 1)}
                        disabled={currentPage === invoices.pages}
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

        {/* Invoice Details */}
        <div>
          {selectedInvoice ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Invoice Details</span>
                  <Button
                    onClick={() => handleDownloadPDF(selectedInvoice.id)}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    PDF
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Invoice Number</p>
                  <p className="text-lg font-bold">{selectedInvoice.invoice_number}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Status</p>
                  <div className="mt-1">{getStatusBadge(selectedInvoice.status)}</div>
                </div>

                <div className="pt-4 border-t">
                  <p className="font-medium mb-3">Amount Breakdown</p>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subtotal</span>
                      <span className="font-medium">${selectedInvoice.subtotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Platform Fee</span>
                      <span className="font-medium">
                        ${selectedInvoice.platform_fee.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Tax</span>
                      <span className="font-medium">${selectedInvoice.tax_amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold pt-2 border-t">
                      <span>Total</span>
                      <span>${selectedInvoice.total_amount.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="font-medium mb-3">Invoice Information</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Issued</span>
                      <span>{new Date(selectedInvoice.issued_at).toLocaleDateString()}</span>
                    </div>
                    {selectedInvoice.due_date && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Due Date</span>
                        <span>{new Date(selectedInvoice.due_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    {selectedInvoice.paid_at && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Paid</span>
                        <span className="text-green-600 font-medium">
                          {new Date(selectedInvoice.paid_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                    {selectedInvoice.payment_method && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Payment Method</span>
                        <span className="capitalize">{selectedInvoice.payment_method}</span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedInvoice.stripe_invoice_id && (
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground">Stripe Invoice ID</p>
                    <p className="text-xs font-mono">{selectedInvoice.stripe_invoice_id}</p>
                  </div>
                )}

                {selectedInvoice.notes && (
                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground">Notes</p>
                    <p className="text-sm">{selectedInvoice.notes}</p>
                  </div>
                )}

                {/* Actions */}
                {selectedInvoice.status === InvoiceStatus.ISSUED ||
                  selectedInvoice.status === InvoiceStatus.OVERDUE ? (
                  <div className="pt-4 border-t">
                    <Button
                      onClick={handleMarkAsPaid}
                      disabled={actionLoading}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Mark as Paid
                    </Button>
                  </div>
                ) : null}

                {selectedInvoice.pdf_url && (
                  <div className="pt-4 border-t">
                    <Button variant="outline" className="w-full" asChild>
                      <a href={selectedInvoice.pdf_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View PDF in New Tab
                      </a>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-12 text-center text-muted-foreground">
                <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>Select an invoice to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
