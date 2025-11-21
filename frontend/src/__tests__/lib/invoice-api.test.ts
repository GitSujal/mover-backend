import { invoiceAPI, InvoiceStatus } from "@/lib/api/invoice-api";
import { apiClient } from "@/lib/api/client";

// Mock the apiClient
jest.mock("@/lib/api/client");
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe("Invoice API", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe("listOrganizationInvoices", () => {
        it("fetches organization invoices successfully", async () => {
            const mockResponse = {
                invoices: [
                    {
                        id: "invoice-1",
                        booking_id: "booking-1",
                        invoice_number: "INV-12345",
                        subtotal: 500.0,
                        platform_fee: 50.0,
                        tax_amount: 45.0,
                        total_amount: 595.0,
                        status: InvoiceStatus.ISSUED,
                        issued_at: "2025-01-15T10:00:00Z",
                        paid_at: null,
                        due_date: "2025-02-15T10:00:00Z",
                        payment_method: null,
                        stripe_invoice_id: null,
                        stripe_payment_intent_id: null,
                        pdf_url: null,
                        notes: null,
                        created_at: "2025-01-15T10:00:00Z",
                        updated_at: "2025-01-15T10:00:00Z",
                    },
                ],
                total: 1,
                page: 1,
                page_size: 20,
                pages: 1,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            const result = await invoiceAPI.listOrganizationInvoices("org-1", 1, 20);

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining(
                    "/api/v1/invoices/organization/org-1/list"
                )
            );
            expect(result).toEqual(mockResponse);
        });

        it("includes status filter in request", async () => {
            const mockResponse = {
                invoices: [],
                total: 0,
                page: 1,
                page_size: 20,
                pages: 1,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockResponse });

            await invoiceAPI.listOrganizationInvoices(
                "org-1",
                1,
                20,
                InvoiceStatus.PAID
            );

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                expect.stringContaining("status_filter=paid")
            );
        });
    });

    describe("getInvoice", () => {
        it("fetches invoice details successfully", async () => {
            const mockInvoice = {
                id: "invoice-1",
                booking_id: "booking-1",
                invoice_number: "INV-12345",
                subtotal: 500.0,
                platform_fee: 50.0,
                tax_amount: 45.0,
                total_amount: 595.0,
                status: InvoiceStatus.ISSUED,
                issued_at: "2025-01-15T10:00:00Z",
                paid_at: null,
                due_date: "2025-02-15T10:00:00Z",
                payment_method: null,
                stripe_invoice_id: null,
                stripe_payment_intent_id: null,
                pdf_url: "https://example.com/invoice.pdf",
                notes: "Payment due within 30 days",
                created_at: "2025-01-15T10:00:00Z",
                updated_at: "2025-01-15T10:00:00Z",
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockInvoice });

            const result = await invoiceAPI.getInvoice("invoice-1");

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                "/api/v1/invoices/invoice-1"
            );
            expect(result).toEqual(mockInvoice);
        });
    });

    describe("createInvoice", () => {
        it("creates invoice successfully", async () => {
            const mockInvoice = {
                id: "invoice-1",
                booking_id: "booking-1",
                invoice_number: "INV-12345",
                status: InvoiceStatus.DRAFT,
            } as any;

            mockedApiClient.post.mockResolvedValueOnce({ data: mockInvoice });

            const result = await invoiceAPI.createInvoice({
                booking_id: "booking-1",
                notes: "Thank you for your business",
            });

            expect(mockedApiClient.post).toHaveBeenCalledWith(
                "/api/v1/invoices",
                {
                    booking_id: "booking-1",
                    notes: "Thank you for your business",
                }
            );
            expect(result.booking_id).toBe("booking-1");
        });
    });

    describe("updateInvoice", () => {
        it("updates invoice status successfully", async () => {
            const mockInvoice = {
                id: "invoice-1",
                status: InvoiceStatus.CANCELLED,
            } as any;

            mockedApiClient.patch.mockResolvedValueOnce({ data: mockInvoice });

            const result = await invoiceAPI.updateInvoice("invoice-1", {
                status: InvoiceStatus.CANCELLED,
            });

            expect(mockedApiClient.patch).toHaveBeenCalledWith(
                "/api/v1/invoices/invoice-1",
                { status: InvoiceStatus.CANCELLED }
            );
            expect(result.status).toBe(InvoiceStatus.CANCELLED);
        });
    });

    describe("markAsPaid", () => {
        it("marks invoice as paid successfully", async () => {
            const mockInvoice = {
                id: "invoice-1",
                status: InvoiceStatus.PAID,
                payment_method: "stripe",
                paid_at: "2025-01-20T15:00:00Z",
            } as any;

            mockedApiClient.post.mockResolvedValueOnce({ data: mockInvoice });

            const result = await invoiceAPI.markAsPaid("invoice-1", "stripe");

            expect(mockedApiClient.post).toHaveBeenCalledWith(
                expect.stringContaining("/api/v1/invoices/invoice-1/mark-paid")
            );
            expect(mockedApiClient.post).toHaveBeenCalledWith(
                expect.stringContaining("payment_method=stripe")
            );
            expect(result.status).toBe(InvoiceStatus.PAID);
        });

        it("uses default payment method when not provided", async () => {
            const mockInvoice = {
                id: "invoice-1",
                status: InvoiceStatus.PAID,
            } as any;

            mockedApiClient.post.mockResolvedValueOnce({ data: mockInvoice });

            await invoiceAPI.markAsPaid("invoice-1");

            expect(mockedApiClient.post).toHaveBeenCalledWith(
                expect.stringContaining("payment_method=stripe")
            );
        });
    });

    describe("getOrganizationStats", () => {
        it("fetches organization invoice statistics", async () => {
            const mockStats = {
                total_invoices: 100,
                draft_invoices: 5,
                issued_invoices: 20,
                paid_invoices: 70,
                overdue_invoices: 5,
                total_revenue: 50000,
                total_outstanding: 15000,
                average_invoice_amount: 500,
                payment_rate: 0.7,
            };

            mockedApiClient.get.mockResolvedValueOnce({ data: mockStats });

            const result = await invoiceAPI.getOrganizationStats("org-1");

            expect(mockedApiClient.get).toHaveBeenCalledWith(
                "/api/v1/invoices/organization/org-1/stats"
            );
            expect(result).toEqual(mockStats);
        });
    });

    describe("getInvoicePdfUrl", () => {
        it("generates correct PDF URL", () => {
            const url = invoiceAPI.getInvoicePdfUrl("invoice-1");

            expect(url).toContain("/api/v1/invoices/invoice-1/pdf");
            expect(url).toMatch(/^https?:\/\//);
        });
    });

    describe("Error Handling", () => {
        it("handles API errors", async () => {
            const mockError = new Error("Network error");
            mockedApiClient.get.mockRejectedValueOnce(mockError);

            await expect(
                invoiceAPI.listOrganizationInvoices("org-1")
            ).rejects.toThrow("Network error");
        });
    });
});
