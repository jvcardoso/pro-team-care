/**
 * Billing Service - Frontend API Layer
 * Handles all billing-related API calls
 */

import api from "./api.js";
import {
  BillingSchedule,
  BillingScheduleCreate,
  BillingScheduleUpdate,
  BillingScheduleListParams,
  BillingScheduleListResponse,
  Invoice,
  InvoiceDetailed,
  InvoiceCreate,
  InvoiceUpdate,
  InvoiceListParams,
  InvoiceListResponse,
  PaymentReceipt,
  PaymentReceiptCreate,
  ReceiptListParams,
  ReceiptListResponse,
  BillingDashboardResponse,
  BillingMetrics,
  PaymentDetails,
  InvoiceStatus,
  VerificationStatus,
  BulkInvoiceGeneration,
  BulkInvoiceGenerationResponse,
  BulkStatusUpdate,
  BulkStatusUpdateResponse,
  AutoBillingRequest,
  AutoBillingResult,
  ApiResponse,
} from "../types/billing.types";
import {
  BillingMethodStatus,
  BillingMethodUpdate,
  RecurrentBillingSetupRequest,
  RecurrentBillingSetupResponse,
  CheckoutSessionRequest,
  CheckoutSessionResponse,
  SubscriptionCancelRequest,
  SubscriptionCancelResponse,
  AutomaticBillingRequest,
  AutomaticBillingResponse,
  TransactionsListResponse,
} from "../types/pagbank.types";

const BASE_URL = "/api/v1/billing";

class BillingService {
  // ==========================================
  // BILLING SCHEDULES
  // ==========================================

  async listBillingSchedules(
    params: BillingScheduleListParams = {}
  ): Promise<BillingScheduleListResponse> {
    const response = await api.get<BillingScheduleListResponse>(
      `${BASE_URL}/schedules`,
      {
        params: {
          contract_id: params.contract_id,
          billing_cycle: params.billing_cycle,
          is_active: params.is_active,
          next_billing_before: params.next_billing_before,
          page: params.page || 1,
          size: params.size || 50,
        },
      }
    );
    return response.data;
  }

  async getBillingSchedule(id: number): Promise<BillingSchedule> {
    const response = await api.get<BillingSchedule>(
      `${BASE_URL}/schedules/${id}`
    );
    return response.data;
  }

  async createBillingSchedule(
    data: BillingScheduleCreate
  ): Promise<BillingSchedule> {
    const response = await api.post<BillingSchedule>(
      `${BASE_URL}/schedules`,
      data
    );
    return response.data;
  }

  async updateBillingSchedule(
    id: number,
    data: BillingScheduleUpdate
  ): Promise<BillingSchedule> {
    const response = await api.put<BillingSchedule>(
      `${BASE_URL}/schedules/${id}`,
      data
    );
    return response.data;
  }

  // ==========================================
  // INVOICES
  // ==========================================

  async listInvoices(
    params: InvoiceListParams = {}
  ): Promise<InvoiceListResponse> {
    const response = await api.get<InvoiceListResponse>(
      `${BASE_URL}/invoices`,
      {
        params: {
          contract_id: params.contract_id,
          status: params.status,
          start_date: params.start_date,
          end_date: params.end_date,
          overdue_only: params.overdue_only,
          page: params.page || 1,
          size: params.size || 50,
        },
      }
    );
    return response.data;
  }

  async getInvoice(id: number): Promise<InvoiceDetailed> {
    const response = await api.get<InvoiceDetailed>(
      `${BASE_URL}/invoices/${id}`
    );
    return response.data;
  }

  async createInvoice(data: InvoiceCreate): Promise<Invoice> {
    const response = await api.post<Invoice>(`${BASE_URL}/invoices`, data);
    return response.data;
  }

  async updateInvoice(id: number, data: InvoiceUpdate): Promise<Invoice> {
    const response = await api.put<Invoice>(`${BASE_URL}/invoices/${id}`, data);
    return response.data;
  }

  async updateInvoiceStatus(
    id: number,
    status: InvoiceStatus,
    paymentDetails?: PaymentDetails
  ): Promise<Invoice> {
    const params = new URLSearchParams({
      status: status.toString(),
      ...(paymentDetails?.paid_date && { paid_date: paymentDetails.paid_date }),
      ...(paymentDetails?.payment_method && {
        payment_method: paymentDetails.payment_method,
      }),
      ...(paymentDetails?.payment_reference && {
        payment_reference: paymentDetails.payment_reference,
      }),
      ...(paymentDetails?.payment_notes && {
        payment_notes: paymentDetails.payment_notes,
      }),
    });

    const response = await api.patch<Invoice>(
      `${BASE_URL}/invoices/${id}/status?${params}`
    );
    return response.data;
  }

  // ==========================================
  // PAYMENT RECEIPTS
  // ==========================================

  async listPaymentReceipts(
    params: ReceiptListParams = {}
  ): Promise<ReceiptListResponse> {
    const response = await api.get<ReceiptListResponse>(
      `${BASE_URL}/receipts`,
      {
        params: {
          invoice_id: params.invoice_id,
          verification_status: params.verification_status,
          uploaded_by: params.uploaded_by,
          start_date: params.start_date,
          end_date: params.end_date,
          page: params.page || 1,
          size: params.size || 50,
        },
      }
    );
    return response.data;
  }

  async getPaymentReceipt(id: number): Promise<PaymentReceipt> {
    const response = await api.get<PaymentReceipt>(
      `${BASE_URL}/receipts/${id}`
    );
    return response.data;
  }

  async uploadPaymentReceipt(
    invoiceId: number,
    file: File,
    notes?: string
  ): Promise<PaymentReceipt> {
    const formData = new FormData();
    formData.append("invoice_id", invoiceId.toString());
    formData.append("file", file);
    if (notes) {
      formData.append("notes", notes);
    }

    const response = await api.post<PaymentReceipt>(
      `${BASE_URL}/receipts/upload`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  }

  async verifyPaymentReceipt(
    id: number,
    verificationStatus: VerificationStatus,
    notes?: string
  ): Promise<PaymentReceipt> {
    const params = new URLSearchParams({
      verification_status: verificationStatus,
      ...(notes && { notes }),
    });

    const response = await api.patch<PaymentReceipt>(
      `${BASE_URL}/receipts/${id}/verify?${params}`
    );
    return response.data;
  }

  // ==========================================
  // DASHBOARD & ANALYTICS
  // ==========================================

  async getBillingDashboard(): Promise<BillingDashboardResponse> {
    const response = await api.get<BillingDashboardResponse>(
      `${BASE_URL}/dashboard`
    );
    return response.data;
  }

  async getBillingMetrics(companyId?: number): Promise<BillingMetrics> {
    const params = companyId ? { company_id: companyId } : {};
    const response = await api.get<BillingMetrics>(
      `${BASE_URL}/analytics/metrics`,
      { params }
    );
    return response.data;
  }

  async getContractBillingStatus(contractId: number): Promise<any> {
    const response = await api.get(
      `${BASE_URL}/contracts/${contractId}/status`
    );
    return response.data;
  }

  // ==========================================
  // BULK OPERATIONS
  // ==========================================

  async bulkGenerateInvoices(
    data: BulkInvoiceGeneration
  ): Promise<BulkInvoiceGenerationResponse> {
    const response = await api.post<BulkInvoiceGenerationResponse>(
      `${BASE_URL}/invoices/bulk-generate`,
      data
    );
    return response.data;
  }

  async bulkUpdateInvoiceStatus(
    data: BulkStatusUpdate
  ): Promise<BulkStatusUpdateResponse> {
    const response = await api.patch<BulkStatusUpdateResponse>(
      `${BASE_URL}/invoices/bulk-status`,
      data
    );
    return response.data;
  }

  // ==========================================
  // AUTOMATIC BILLING
  // ==========================================

  async runAutomaticBilling(
    data: AutoBillingRequest = {}
  ): Promise<AutoBillingResult> {
    const params = new URLSearchParams({
      ...(data.billing_date && { billing_date: data.billing_date }),
      ...(data.force_regenerate !== undefined && {
        force_regenerate: data.force_regenerate.toString(),
      }),
    });

    const response = await api.post<AutoBillingResult>(
      `${BASE_URL}/auto-billing/run?${params}`
    );
    return response.data;
  }

  async getUpcomingBillings(daysAhead: number = 30): Promise<any> {
    const response = await api.get(`${BASE_URL}/auto-billing/upcoming`, {
      params: { days_ahead: daysAhead },
    });
    return response.data;
  }

  // ==========================================
  // UTILITY METHODS
  // ==========================================

  /**
   * Calculate total amount from invoice components
   */
  calculateTotalAmount(
    baseAmount: number,
    additionalServices: number = 0,
    taxes: number = 0,
    discounts: number = 0
  ): number {
    return baseAmount + additionalServices + taxes - discounts;
  }

  /**
   * Check if invoice is overdue
   */
  isInvoiceOverdue(invoice: Invoice): boolean {
    const today = new Date();
    const dueDate = new Date(invoice.due_date);
    return dueDate < today && !["paga", "cancelada"].includes(invoice.status);
  }

  /**
   * Calculate days overdue
   */
  getDaysOverdue(invoice: Invoice): number {
    if (!this.isInvoiceOverdue(invoice)) return 0;

    const today = new Date();
    const dueDate = new Date(invoice.due_date);
    const diffTime = today.getTime() - dueDate.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  /**
   * Format currency for display
   */
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(amount);
  }

  /**
   * Format date for display
   */
  formatDate(dateString: string): string {
    return new Intl.DateTimeFormat("pt-BR").format(new Date(dateString));
  }

  /**
   * Get status color for badges
   */
  getInvoiceStatusColor(status: InvoiceStatus): string {
    const colors = {
      [InvoiceStatus.PENDENTE]: "yellow",
      [InvoiceStatus.ENVIADA]: "blue",
      [InvoiceStatus.PAGA]: "green",
      [InvoiceStatus.VENCIDA]: "red",
      [InvoiceStatus.CANCELADA]: "gray",
      [InvoiceStatus.EM_ATRASO]: "red",
    };
    return colors[status] || "gray";
  }

  /**
   * Get verification status color
   */
  getVerificationStatusColor(status: VerificationStatus): string {
    const colors = {
      [VerificationStatus.PENDENTE]: "yellow",
      [VerificationStatus.APROVADO]: "green",
      [VerificationStatus.REJEITADO]: "red",
    };
    return colors[status] || "gray";
  }

  /**
   * Validate file for receipt upload
   */
  validateReceiptFile(
    file: File,
    maxSize: number = 10 * 1024 * 1024
  ): { valid: boolean; error?: string } {
    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "application/pdf",
    ];

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: "Tipo de arquivo não permitido. Use JPG, PNG ou PDF.",
      };
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: `Arquivo muito grande. Tamanho máximo: ${Math.round(
          maxSize / 1024 / 1024
        )}MB`,
      };
    }

    return { valid: true };
  }

  /**
   * Generate invoice number preview
   */
  generateInvoiceNumberPreview(contractId: number): string {
    const now = new Date();
    const yearMonth = now.toISOString().slice(0, 7).replace("-", "");
    return `INV-${yearMonth}-${contractId.toString().padStart(6, "0")}-001`;
  }

  /**
   * Calculate collection rate
   */
  calculateCollectionRate(paidAmount: number, totalAmount: number): number {
    if (totalAmount === 0) return 0;
    return Math.round((paidAmount / totalAmount) * 100 * 100) / 100; // Round to 2 decimals
  }

  // ==========================================
  // PAGBANK INTEGRATION METHODS
  // ==========================================

  /**
   * Get billing method status for a contract
   */
  async getBillingMethodStatus(
    contractId: number
  ): Promise<BillingMethodStatus> {
    const response = await api.get<BillingMethodStatus>(
      `${BASE_URL}/pagbank/billing-method/${contractId}`
    );
    return response.data;
  }

  /**
   * Setup recurrent billing with PagBank
   */
  async setupRecurrentBilling(
    request: RecurrentBillingSetupRequest
  ): Promise<RecurrentBillingSetupResponse> {
    const response = await api.post<RecurrentBillingSetupResponse>(
      `${BASE_URL}/pagbank/setup-recurrent`,
      request
    );
    return response.data;
  }

  /**
   * Setup manual billing for a contract
   */
  async setupManualBilling(contractId: number): Promise<ApiResponse<any>> {
    const response = await api.post<ApiResponse<any>>(
      `${BASE_URL}/pagbank/setup-manual/${contractId}`
    );
    return response.data;
  }

  /**
   * Create checkout session for an invoice
   */
  async createCheckoutSession(
    request: CheckoutSessionRequest
  ): Promise<CheckoutSessionResponse> {
    const response = await api.post<CheckoutSessionResponse>(
      `${BASE_URL}/pagbank/create-checkout`,
      request
    );
    return response.data;
  }

  /**
   * Cancel recurrent subscription
   */
  async cancelRecurrentSubscription(
    request: SubscriptionCancelRequest
  ): Promise<SubscriptionCancelResponse> {
    const response = await api.post<SubscriptionCancelResponse>(
      `${BASE_URL}/pagbank/cancel-subscription`,
      request
    );
    return response.data;
  }

  /**
   * Run automatic recurrent billing (admin only)
   */
  async runAutomaticRecurrentBilling(): Promise<AutomaticBillingResponse> {
    const response = await api.post<AutomaticBillingResponse>(
      `${BASE_URL}/pagbank/run-recurrent-billing`
    );
    return response.data;
  }

  /**
   * Get PagBank transactions for an invoice
   */
  async getInvoicePagBankTransactions(
    invoiceId: number
  ): Promise<TransactionsListResponse> {
    const response = await api.get<TransactionsListResponse>(
      `${BASE_URL}/pagbank/transactions/${invoiceId}`
    );
    return response.data;
  }

  // ==========================================
  // PAGBANK UTILITY METHODS
  // ==========================================

  /**
   * Format payment method for display
   */
  formatPaymentMethod(method: "recurrent" | "manual"): string {
    const methods = {
      recurrent: "Cobrança Recorrente",
      manual: "Cobrança Manual",
    };
    return methods[method] || method;
  }

  /**
   * Format transaction status for display
   */
  formatTransactionStatus(status: string): { label: string; color: string } {
    const statusMap = {
      pending: { label: "Pendente", color: "yellow" },
      approved: { label: "Aprovado", color: "green" },
      declined: { label: "Recusado", color: "red" },
      failed: { label: "Falhou", color: "red" },
      cancelled: { label: "Cancelado", color: "gray" },
    } as const;

    return (
      statusMap[status as keyof typeof statusMap] || {
        label: status,
        color: "gray",
      }
    );
  }

  /**
   * Calculate billing method statistics
   */
  calculateBillingMethodStats(schedules: BillingSchedule[]) {
    const total = schedules.length;
    const recurrent = schedules.filter(
      (s) => (s as any).billing_method === "recurrent"
    ).length;
    const manual = total - recurrent;

    return {
      total,
      recurrent,
      manual,
      recurrentPercentage:
        total > 0 ? Math.round((recurrent / total) * 100) : 0,
      manualPercentage: total > 0 ? Math.round((manual / total) * 100) : 0,
    };
  }

  /**
   * Check if checkout session is expired
   */
  isCheckoutExpired(expiresAt: string): boolean {
    return new Date(expiresAt) < new Date();
  }

  /**
   * Get time remaining until checkout expires
   */
  getCheckoutTimeRemaining(expiresAt: string): string {
    const now = new Date().getTime();
    const expiry = new Date(expiresAt).getTime();
    const diff = expiry - now;

    if (diff <= 0) return "Expirado";

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }
}

// Export singleton instance
export const billingService = new BillingService();
export default billingService;

// Export types for convenience
export type {
  BillingSchedule,
  BillingScheduleCreate,
  BillingScheduleUpdate,
  Invoice,
  InvoiceDetailed,
  InvoiceCreate,
  InvoiceUpdate,
  PaymentReceipt,
  BillingDashboardResponse,
  BillingMetrics,
} from "../types/billing.types";
