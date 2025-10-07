/**
 * Serviço para comunicação com APIs de cobrança B2B Pro Team Care
 */
import { api } from "./api";
import type {
  B2BDashboardData,
  BulkInvoiceGenerationRequest,
  BulkInvoiceGenerationResponse,
  CheckoutSessionResponse,
  CompanySubscription,
  CreateInvoiceRequest,
  CreateSubscriptionRequest,
  PaymentConfirmationRequest,
  ProTeamCareInvoice,
  SubscriptionPlan,
} from "../types/b2b-billing.types";

const BASE_URL = "/api/v1/b2b-billing";

export class B2BBillingService {
  // ==========================================
  // SUBSCRIPTION PLANS
  // ==========================================

  static async getSubscriptionPlans(
    activeOnly: boolean = true
  ): Promise<SubscriptionPlan[]> {
    const response = await api.get(`${BASE_URL}/plans`, {
      params: { active_only: activeOnly },
    });
    return response.data;
  }

  static async getSubscriptionPlan(planId: number): Promise<SubscriptionPlan> {
    const response = await api.get(`${BASE_URL}/plans/${planId}`);
    return response.data;
  }

  static async createSubscriptionPlan(
    planData: Omit<SubscriptionPlan, "id" | "created_at" | "updated_at">
  ): Promise<SubscriptionPlan> {
    const response = await api.post(`${BASE_URL}/plans`, planData);
    return response.data;
  }

  static async updateSubscriptionPlan(
    planId: number,
    planData: Partial<
      Omit<SubscriptionPlan, "id" | "created_at" | "updated_at">
    >
  ): Promise<SubscriptionPlan> {
    const response = await api.put(`${BASE_URL}/plans/${planId}`, planData);
    return response.data;
  }

  static async deleteSubscriptionPlan(
    planId: number
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`${BASE_URL}/plans/${planId}`);
    return response.data;
  }

  // ==========================================
  // COMPANY SUBSCRIPTIONS
  // ==========================================

  static async createCompanySubscription(
    data: CreateSubscriptionRequest
  ): Promise<CompanySubscription> {
    const response = await api.post(`${BASE_URL}/subscriptions`, data);
    return response.data;
  }

  static async getCompanySubscription(
    companyId: number
  ): Promise<CompanySubscription | null> {
    try {
      const response = await api.get(
        `${BASE_URL}/subscriptions/company/${companyId}`
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Buscar assinaturas de múltiplas empresas (bulk operation)
   * @param companyIds IDs das empresas
   * @returns Array de subscriptions (null para empresas sem assinatura)
   */
  static async getCompanySubscriptionsBatch(
    companyIds: number[]
  ): Promise<(CompanySubscription | null)[]> {
    if (!companyIds || companyIds.length === 0) {
      return [];
    }

    const response = await api.post(`${BASE_URL}/subscriptions/batch`, {
      company_ids: companyIds,
    });

    return response.data.subscriptions;
  }

  static async updateCompanySubscription(
    subscriptionId: number,
    updateData: Partial<CompanySubscription>
  ): Promise<CompanySubscription> {
    const response = await api.put(
      `${BASE_URL}/subscriptions/${subscriptionId}`,
      updateData
    );
    return response.data;
  }

  // ==========================================
  // INVOICES
  // ==========================================

  static async createManualInvoice(
    data: CreateInvoiceRequest
  ): Promise<ProTeamCareInvoice> {
    const response = await api.post(`${BASE_URL}/invoices`, data);
    return response.data;
  }

  static async getInvoice(invoiceId: number): Promise<ProTeamCareInvoice> {
    const response = await api.get(`${BASE_URL}/invoices/${invoiceId}`);
    return response.data;
  }

  static async getCompanyInvoices(
    companyId: number,
    status?: string,
    limit: number = 50
  ): Promise<ProTeamCareInvoice[]> {
    const response = await api.get(
      `${BASE_URL}/invoices/company/${companyId}`,
      {
        params: { status_filter: status, limit },
      }
    );
    return response.data;
  }

  static async getInvoicesByStatus(
    status: string,
    limit: number = 100
  ): Promise<ProTeamCareInvoice[]> {
    const response = await api.get(`${BASE_URL}/invoices/status/${status}`, {
      params: { limit },
    });
    return response.data;
  }

  static async getOverdueInvoices(): Promise<ProTeamCareInvoice[]> {
    const response = await api.get(`${BASE_URL}/invoices/overdue/list`);
    return response.data;
  }

  // ==========================================
  // PAYMENTS
  // ==========================================

  static async createCheckoutSession(
    invoiceId: number
  ): Promise<CheckoutSessionResponse> {
    const response = await api.post(
      `${BASE_URL}/invoices/${invoiceId}/checkout`
    );
    return response.data;
  }

  static async markInvoiceAsPaid(
    invoiceId: number,
    paymentData: PaymentConfirmationRequest
  ): Promise<{ success: boolean; message: string }> {
    const response = await api.post(
      `${BASE_URL}/invoices/${invoiceId}/mark-paid`,
      paymentData
    );
    return response.data;
  }

  // ==========================================
  // BULK OPERATIONS
  // ==========================================

  static async bulkGenerateInvoices(
    data: BulkInvoiceGenerationRequest
  ): Promise<BulkInvoiceGenerationResponse> {
    const response = await api.post(`${BASE_URL}/invoices/bulk-generate`, data);
    return response.data;
  }

  // ==========================================
  // DASHBOARD
  // ==========================================

  static async getDashboardData(): Promise<B2BDashboardData> {
    const response = await api.get(`${BASE_URL}/dashboard`);
    return response.data;
  }

  // ==========================================
  // UTILITIES
  // ==========================================

  static async getCompaniesForBilling(billingDay: number) {
    const response = await api.get(`${BASE_URL}/companies-for-billing`, {
      params: { billing_day: billingDay },
    });
    return response.data;
  }

  // ==========================================
  // FORMATTERS
  // ==========================================

  static formatCurrency(amount: number | string): string {
    const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(numAmount);
  }

  static formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("pt-BR");
  }

  static formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString("pt-BR");
  }

  static getStatusLabel(status: string): string {
    const statusLabels: Record<string, string> = {
      pending: "Pendente",
      paid: "Pago",
      overdue: "Vencido",
      cancelled: "Cancelado",
      active: "Ativo",
      suspended: "Suspenso",
      expired: "Expirado",
    };
    return statusLabels[status] || status;
  }

  static getStatusColor(status: string): string {
    const statusColors: Record<string, string> = {
      pending: "text-yellow-600 bg-yellow-100",
      paid: "text-green-600 bg-green-100",
      overdue: "text-red-600 bg-red-100",
      cancelled: "text-gray-600 bg-gray-100",
      active: "text-green-600 bg-green-100",
      suspended: "text-orange-600 bg-orange-100",
      expired: "text-red-600 bg-red-100",
    };
    return statusColors[status] || "text-gray-600 bg-gray-100";
  }

  static isOverdue(invoice: ProTeamCareInvoice): boolean {
    if (invoice.status === "paid") return false;
    const dueDate = new Date(invoice.due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return dueDate < today;
  }

  static getDaysUntilDue(invoice: ProTeamCareInvoice): number {
    const dueDate = new Date(invoice.due_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffTime = dueDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  static getPlanFeaturesList(plan: SubscriptionPlan): string[] {
    if (!plan.features) return [];

    const features: string[] = [];

    if (plan.max_users) {
      features.push(`Até ${plan.max_users} usuários`);
    }

    if (plan.max_establishments) {
      features.push(`Até ${plan.max_establishments} estabelecimentos`);
    }

    if (plan.features.reports) {
      features.push(`Relatórios ${plan.features.reports}`);
    }

    if (plan.features.support) {
      features.push(`Suporte ${plan.features.support}`);
    }

    if (plan.features.integrations) {
      features.push(`Integrações ${plan.features.integrations}`);
    }

    if (plan.features.analytics) {
      features.push("Analytics avançado");
    }

    if (plan.features.custom_features) {
      features.push("Recursos personalizados");
    }

    return features;
  }

  static calculateNextBillingDate(subscription: CompanySubscription): Date {
    const today = new Date();
    const billingDay = subscription.billing_day;

    let nextBilling = new Date(
      today.getFullYear(),
      today.getMonth(),
      billingDay
    );

    // Se já passou do dia de cobrança neste mês, ir para o próximo
    if (nextBilling <= today) {
      nextBilling = new Date(
        today.getFullYear(),
        today.getMonth() + 1,
        billingDay
      );
    }

    return nextBilling;
  }
}
