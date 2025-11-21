/**
 * Document Verification API client
 * Type-safe API calls for document verification and review
 */

import { apiClient } from "./client";

export enum DocumentType {
    BUSINESS_LICENSE = "business_license",
    LIABILITY_INSURANCE = "liability_insurance",
    WORKERS_COMP_INSURANCE = "workers_comp_insurance",
    DRIVERS_LICENSE = "drivers_license",
    BACKGROUND_CHECK = "background_check",
    VEHICLE_REGISTRATION = "vehicle_registration",
    DOT_NUMBER = "dot_number",
}

export enum VerificationStatus {
    PENDING = "pending",
    UNDER_REVIEW = "under_review",
    APPROVED = "approved",
    REJECTED = "rejected",
    RESUBMISSION_REQUIRED = "resubmission_required",
    EXPIRED = "expired",
}

export interface DocumentVerificationCreate {
    document_type: DocumentType;
    document_url: string;
    document_number?: string;
    expiry_date?: string;
    additional_data?: Record<string, any>;
}

export interface DocumentVerificationResponse {
    id: string;
    org_id: string | null;
    driver_id: string | null;
    document_type: DocumentType;
    document_url: string;
    document_number: string | null;
    expiry_date: string | null;
    status: VerificationStatus;
    submitted_at: string;
    reviewed_at: string | null;
    reviewer_id: string | null;
    review_notes: string | null;
    rejection_reason: string | null;
    expiry_reminder_sent_at: string | null;
    additional_data: Record<string, any> | null;
    created_at: string;
    updated_at: string;
}

export interface DocumentVerificationReview {
    status: VerificationStatus;
    review_notes?: string;
    rejection_reason?: string;
}

export interface DocumentVerificationListResponse {
    verifications: DocumentVerificationResponse[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

export interface OrganizationVerificationStatus {
    org_id: string;
    business_name: string;
    is_verified: boolean;
    required_documents: Record<string, boolean>;
    missing_documents: string[];
    expiring_documents: string[];
    total_documents: number;
    approved_documents: number;
    pending_documents: number;
    rejected_documents: number;
}

export interface DriverVerificationStatus {
    driver_id: string;
    driver_name: string;
    is_verified: boolean;
    required_documents: Record<string, boolean>;
    missing_documents: string[];
    expiring_documents: string[];
    total_documents: number;
    approved_documents: number;
    pending_documents: number;
    rejected_documents: number;
}

export interface DocumentVerificationStats {
    total_pending: number;
    total_under_review: number;
    total_approved: number;
    total_rejected: number;
    total_expired: number;
    documents_expiring_soon: number;
}

export const verificationAPI = {
    /**
     * Submit organization document
     */
    submitOrganizationDocument: async (
        orgId: string,
        document: DocumentVerificationCreate
    ): Promise<DocumentVerificationResponse> => {
        const response = await apiClient.post(
            `/api/v1/verification/organization/${orgId}/documents`,
            document
        );
        return response.data;
    },

    /**
     * Submit driver document
     */
    submitDriverDocument: async (
        driverId: string,
        document: DocumentVerificationCreate
    ): Promise<DocumentVerificationResponse> => {
        const response = await apiClient.post(
            `/api/v1/verification/driver/${driverId}/documents`,
            document
        );
        return response.data;
    },

    /**
     * Review document (admin only)
     */
    reviewDocument: async (
        verificationId: string,
        review: DocumentVerificationReview
    ): Promise<DocumentVerificationResponse> => {
        const response = await apiClient.post(
            `/api/v1/verification/documents/${verificationId}/review`,
            review
        );
        return response.data;
    },

    /**
     * List pending verifications (admin only)
     */
    listPendingVerifications: async (
        page: number = 1,
        pageSize: number = 20
    ): Promise<DocumentVerificationListResponse> => {
        const params = new URLSearchParams();
        params.append("page", page.toString());
        params.append("page_size", pageSize.toString());

        const response = await apiClient.get(
            `/api/v1/verification/documents/pending?${params.toString()}`
        );
        return response.data;
    },

    /**
     * Get organization verification status
     */
    getOrganizationStatus: async (
        orgId: string
    ): Promise<OrganizationVerificationStatus> => {
        const response = await apiClient.get(
            `/api/v1/verification/organization/${orgId}/status`
        );
        return response.data;
    },

    /**
     * Get driver verification status
     */
    getDriverStatus: async (
        driverId: string
    ): Promise<DriverVerificationStatus> => {
        const response = await apiClient.get(
            `/api/v1/verification/driver/${driverId}/status`
        );
        return response.data;
    },

    /**
     * Get verification statistics
     */
    getStats: async (): Promise<DocumentVerificationStats> => {
        const response = await apiClient.get("/api/v1/verification/stats");
        return response.data;
    },

    /**
     * Get document details
     */
    getDocument: async (
        verificationId: string
    ): Promise<DocumentVerificationResponse> => {
        const response = await apiClient.get(
            `/api/v1/verification/documents/${verificationId}`
        );
        return response.data;
    },

    /**
     * Preview expiring documents
     */
    previewExpiringDocuments: async (
        daysThreshold: number = 30
    ): Promise<{
        total_expiring: number;
        days_threshold: number;
        documents: Array<{
            verification_id: string;
            document_type: string;
            expiry_date: string | null;
            days_until_expiry: number;
            org_id: string | null;
            driver_id: string | null;
        }>;
    }> => {
        const params = new URLSearchParams();
        params.append("days_threshold", daysThreshold.toString());

        const response = await apiClient.get(
            `/api/v1/verification/expiry-reminders/preview?${params.toString()}`
        );
        return response.data;
    },

    /**
     * Send expiry reminders (admin only)
     */
    sendExpiryReminders: async (
        daysThreshold: number = 30
    ): Promise<{
        total_expiring: number;
        reminders_sent: number;
        days_threshold: number;
    }> => {
        const params = new URLSearchParams();
        params.append("days_threshold", daysThreshold.toString());

        const response = await apiClient.post(
            `/api/v1/verification/expiry-reminders/send?${params.toString()}`
        );
        return response.data;
    },
};
