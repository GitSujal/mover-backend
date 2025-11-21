"use client";

import { useState, useEffect } from "react";
import {
    verificationAPI,
    DocumentVerificationResponse,
    DocumentVerificationListResponse,
    VerificationStatus,
    DocumentType,
} from "@/lib/api/verification-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    FileCheck,
    FileX,
    Clock,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    ExternalLink,
    ChevronLeft,
    ChevronRight,
} from "lucide-react";

// Mock org ID - TODO: Replace with actual auth context
const MOCK_ORG_ID = "550e8400-e29b-41d4-a716-446655440000";

export default function VerificationPage() {
    const [verifications, setVerifications] =
        useState<DocumentVerificationListResponse | null>(null);
    const [selectedDoc, setSelectedDoc] =
        useState<DocumentVerificationResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [reviewLoading, setReviewLoading] = useState(false);

    useEffect(() => {
        loadPendingVerifications();
    }, [currentPage]);

    const loadPendingVerifications = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await verificationAPI.listPendingVerifications(
                currentPage,
                20
            );
            setVerifications(data);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load pending verifications"
            );
        } finally {
            setLoading(false);
        }
    };

    const handleReviewDocument = async (
        verificationId: string,
        status: VerificationStatus,
        notes?: string,
        rejectionReason?: string
    ) => {
        try {
            setReviewLoading(true);
            await verificationAPI.reviewDocument(verificationId, {
                status,
                review_notes: notes,
                rejection_reason: rejectionReason,
            });

            // Refresh the list
            await loadPendingVerifications();
            setSelectedDoc(null);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to review document"
            );
        } finally {
            setReviewLoading(false);
        }
    };

    const getStatusBadge = (status: VerificationStatus) => {
        const variants: Record<
            VerificationStatus,
            { variant: "default" | "secondary" | "destructive" | "outline"; icon: any }
        > = {
            [VerificationStatus.PENDING]: {
                variant: "secondary",
                icon: Clock,
            },
            [VerificationStatus.UNDER_REVIEW]: {
                variant: "outline",
                icon: FileCheck,
            },
            [VerificationStatus.APPROVED]: {
                variant: "default",
                icon: CheckCircle2,
            },
            [VerificationStatus.REJECTED]: {
                variant: "destructive",
                icon: XCircle,
            },
            [VerificationStatus.RESUBMISSION_REQUIRED]: {
                variant: "outline",
                icon: AlertTriangle,
            },
            [VerificationStatus.EXPIRED]: {
                variant: "destructive",
                icon: FileX,
            },
        };

        const config = variants[status];
        const Icon = config.icon;

        return (
            <Badge variant={config.variant} className="flex items-center gap-1">
                <Icon className="h-3 w-3" />
                {status.replace(/_/g, " ").toUpperCase()}
            </Badge>
        );
    };

    const getDocumentTypeLabel = (type: DocumentType): string => {
        const labels: Record<DocumentType, string> = {
            [DocumentType.BUSINESS_LICENSE]: "Business License",
            [DocumentType.LIABILITY_INSURANCE]: "Liability Insurance",
            [DocumentType.WORKERS_COMP_INSURANCE]: "Workers Comp Insurance",
            [DocumentType.DRIVERS_LICENSE]: "Driver's License",
            [DocumentType.BACKGROUND_CHECK]: "Background Check",
            [DocumentType.VEHICLE_REGISTRATION]: "Vehicle Registration",
            [DocumentType.DOT_NUMBER]: "DOT Number",
        };
        return labels[type];
    };

    if (loading && !verifications) {
        return (
            <div className="container mx-auto p-6">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold tracking-tight">
                        Document Verification
                    </h1>
                    <p className="text-muted-foreground">
                        Review and approve pending documents
                    </p>
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

    if (error) {
        return (
            <div className="container mx-auto p-6">
                <Card className="border-destructive">
                    <CardContent className="p-6">
                        <div className="flex items-center gap-2 text-destructive">
                            <XCircle className="h-5 w-5" />
                            <p>{error}</p>
                        </div>
                        <Button
                            onClick={loadPendingVerifications}
                            variant="outline"
                            className="mt-4"
                        >
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
                <h1 className="text-3xl font-bold tracking-tight">
                    Document Verification
                </h1>
                <p className="text-muted-foreground">
                    Review and approve pending documents from organizations and
                    drivers
                </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Document List */}
                <div className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center justify-between">
                                <span>
                                    Pending Documents (
                                    {verifications?.total || 0})
                                </span>
                                <Button
                                    onClick={loadPendingVerifications}
                                    variant="outline"
                                    size="sm"
                                >
                                    Refresh
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {verifications?.verifications.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                    <FileCheck className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                    <p>No pending documents to review</p>
                                </div>
                            ) : (
                                <>
                                    {verifications?.verifications.map((doc) => (
                                        <Card
                                            key={doc.id}
                                            className={`cursor-pointer hover:border-primary transition-colors ${
                                                selectedDoc?.id === doc.id
                                                    ? "border-primary"
                                                    : ""
                                            }`}
                                            onClick={() => setSelectedDoc(doc)}
                                        >
                                            <CardContent className="p-4">
                                                <div className="flex items-start justify-between">
                                                    <div className="space-y-1">
                                                        <p className="font-medium">
                                                            {getDocumentTypeLabel(
                                                                doc.document_type
                                                            )}
                                                        </p>
                                                        <p className="text-sm text-muted-foreground">
                                                            {doc.org_id
                                                                ? "Organization"
                                                                : "Driver"}{" "}
                                                            Document
                                                        </p>
                                                        {doc.document_number && (
                                                            <p className="text-xs text-muted-foreground">
                                                                #
                                                                {
                                                                    doc.document_number
                                                                }
                                                            </p>
                                                        )}
                                                    </div>
                                                    {getStatusBadge(doc.status)}
                                                </div>
                                                <div className="mt-2 text-xs text-muted-foreground">
                                                    Submitted:{" "}
                                                    {new Date(
                                                        doc.submitted_at
                                                    ).toLocaleDateString()}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}

                                    {/* Pagination */}
                                    {verifications &&
                                        verifications.pages > 1 && (
                                            <div className="flex items-center justify-between pt-4">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() =>
                                                        setCurrentPage(
                                                            currentPage - 1
                                                        )
                                                    }
                                                    disabled={currentPage === 1}
                                                >
                                                    <ChevronLeft className="h-4 w-4 mr-1" />
                                                    Previous
                                                </Button>
                                                <span className="text-sm text-muted-foreground">
                                                    Page {currentPage} of{" "}
                                                    {verifications.pages}
                                                </span>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() =>
                                                        setCurrentPage(
                                                            currentPage + 1
                                                        )
                                                    }
                                                    disabled={
                                                        currentPage ===
                                                        verifications.pages
                                                    }
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

                {/* Document Details & Review */}
                <div>
                    {selectedDoc ? (
                        <Card>
                            <CardHeader>
                                <CardTitle>Document Review</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-3">
                                    <div>
                                        <p className="text-sm text-muted-foreground">
                                            Document Type
                                        </p>
                                        <p className="font-medium">
                                            {getDocumentTypeLabel(
                                                selectedDoc.document_type
                                            )}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-sm text-muted-foreground">
                                            Status
                                        </p>
                                        <div className="mt-1">
                                            {getStatusBadge(selectedDoc.status)}
                                        </div>
                                    </div>

                                    {selectedDoc.document_number && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">
                                                Document Number
                                            </p>
                                            <p className="font-medium">
                                                {selectedDoc.document_number}
                                            </p>
                                        </div>
                                    )}

                                    {selectedDoc.expiry_date && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">
                                                Expiry Date
                                            </p>
                                            <p className="font-medium">
                                                {new Date(
                                                    selectedDoc.expiry_date
                                                ).toLocaleDateString()}
                                            </p>
                                        </div>
                                    )}

                                    <div>
                                        <p className="text-sm text-muted-foreground">
                                            Submitted
                                        </p>
                                        <p className="font-medium">
                                            {new Date(
                                                selectedDoc.submitted_at
                                            ).toLocaleString()}
                                        </p>
                                    </div>

                                    {selectedDoc.reviewed_at && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">
                                                Reviewed
                                            </p>
                                            <p className="font-medium">
                                                {new Date(
                                                    selectedDoc.reviewed_at
                                                ).toLocaleString()}
                                            </p>
                                        </div>
                                    )}

                                    {selectedDoc.review_notes && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">
                                                Review Notes
                                            </p>
                                            <p className="text-sm">
                                                {selectedDoc.review_notes}
                                            </p>
                                        </div>
                                    )}

                                    {selectedDoc.rejection_reason && (
                                        <div>
                                            <p className="text-sm text-muted-foreground">
                                                Rejection Reason
                                            </p>
                                            <p className="text-sm text-destructive">
                                                {selectedDoc.rejection_reason}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                <div>
                                    <Button
                                        variant="outline"
                                        className="w-full"
                                        asChild
                                    >
                                        <a
                                            href={selectedDoc.document_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            <ExternalLink className="h-4 w-4 mr-2" />
                                            View Document
                                        </a>
                                    </Button>
                                </div>

                                {selectedDoc.status ===
                                    VerificationStatus.PENDING ||
                                selectedDoc.status ===
                                    VerificationStatus.UNDER_REVIEW ? (
                                    <div className="space-y-2 pt-4 border-t">
                                        <p className="font-medium">
                                            Review Actions
                                        </p>
                                        <div className="grid grid-cols-2 gap-2">
                                            <Button
                                                onClick={() =>
                                                    handleReviewDocument(
                                                        selectedDoc.id,
                                                        VerificationStatus.APPROVED,
                                                        "Document verified and approved"
                                                    )
                                                }
                                                disabled={reviewLoading}
                                                className="bg-green-600 hover:bg-green-700"
                                            >
                                                <CheckCircle2 className="h-4 w-4 mr-2" />
                                                Approve
                                            </Button>
                                            <Button
                                                onClick={() => {
                                                    const reason =
                                                        prompt(
                                                            "Enter rejection reason:"
                                                        );
                                                    if (reason) {
                                                        handleReviewDocument(
                                                            selectedDoc.id,
                                                            VerificationStatus.REJECTED,
                                                            "Document rejected",
                                                            reason
                                                        );
                                                    }
                                                }}
                                                disabled={reviewLoading}
                                                variant="destructive"
                                            >
                                                <XCircle className="h-4 w-4 mr-2" />
                                                Reject
                                            </Button>
                                        </div>
                                        <Button
                                            onClick={() => {
                                                const reason =
                                                    prompt(
                                                        "Enter reason for resubmission request:"
                                                    );
                                                if (reason) {
                                                    handleReviewDocument(
                                                        selectedDoc.id,
                                                        VerificationStatus.RESUBMISSION_REQUIRED,
                                                        "Resubmission required",
                                                        reason
                                                    );
                                                }
                                            }}
                                            disabled={reviewLoading}
                                            variant="outline"
                                            className="w-full"
                                        >
                                            <AlertTriangle className="h-4 w-4 mr-2" />
                                            Request Resubmission
                                        </Button>
                                    </div>
                                ) : null}
                            </CardContent>
                        </Card>
                    ) : (
                        <Card>
                            <CardContent className="p-12 text-center text-muted-foreground">
                                <FileCheck className="h-16 w-16 mx-auto mb-4 opacity-50" />
                                <p>Select a document to review</p>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
