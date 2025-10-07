/**
 * Tipos TypeScript para sistema de cobrança B2B Pro Team Care
 */

export interface SubscriptionPlan {
  id: number;
  name: string;
  description?: string;
  monthly_price: number;
  features?: Record<string, any>;
  max_users?: number;
  max_establishments?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CompanySubscription {
  id: number;
  company_id: number;
  plan_id: number;
  status: "active" | "cancelled" | "suspended" | "expired";
  start_date: string;
  end_date?: string;
  billing_day: number;
  payment_method: "manual" | "recurrent";
  pagbank_subscription_id?: string;
  auto_renew: boolean;
  created_at: string;
  updated_at?: string;
  plan?: SubscriptionPlan;
}

export interface ProTeamCareInvoice {
  id: number;
  company_id: number;
  subscription_id: number;
  invoice_number: string;
  amount: number | string; // Can be string from API or number in frontend
  billing_period_start: string;
  billing_period_end: string;
  due_date: string;
  status: "pending" | "paid" | "overdue" | "cancelled";
  payment_method: "manual" | "recurrent";
  paid_at?: string;
  pagbank_checkout_url?: string;
  pagbank_session_id?: string;
  pagbank_transaction_id?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface B2BBillingMetrics {
  total_companies: number;
  active_subscriptions: number;
  monthly_revenue: number;
  pending_invoices: number;
  overdue_invoices: number;
  paid_invoices_this_month: number;
  total_revenue_this_month: number;
}

export interface CompanyBillingStatus {
  company_id: number;
  company_name: string;
  plan_name: string;
  monthly_amount: number;
  last_payment?: string;
  next_billing?: string;
  status: string;
  overdue_amount: number;
  payment_method: string;
}

export interface B2BDashboardData {
  metrics: B2BBillingMetrics;
  companies_status: CompanyBillingStatus[];
  recent_payments: ProTeamCareInvoice[];
  plan_distribution: Record<string, number>;
}

export interface CreateSubscriptionRequest {
  company_id: number;
  plan_id: number;
  start_date: string;
  billing_day?: number;
  payment_method?: "manual" | "recurrent";
  auto_renew?: boolean;
}

export interface CreateInvoiceRequest {
  company_id: number;
  subscription_id: number;
  billing_period_start: string;
  billing_period_end: string;
  due_date: string;
  amount: number;
  notes?: string;
}

export interface BulkInvoiceGenerationRequest {
  target_month: number;
  target_year: number;
  company_ids?: number[];
  send_emails?: boolean;
}

export interface BulkInvoiceGenerationResponse {
  success: boolean;
  total_companies: number;
  invoices_created: number;
  invoices_failed: number;
  total_amount: number;
  errors: string[];
}

export interface CheckoutSessionResponse {
  success: boolean;
  invoice_id: number;
  checkout_url: string;
  session_id: string;
  expires_at: string;
  qr_code?: string;
  transaction_id?: number;
}

export interface PaymentConfirmationRequest {
  invoice_id: number;
  payment_method: string;
  payment_date: string;
  transaction_reference?: string;
  notes?: string;
}

// Estados dos componentes
export interface B2BBillingComponentState {
  loading: boolean;
  error?: string;
  subscriptions?: CompanySubscription[];
  invoices?: ProTeamCareInvoice[];
  metrics?: B2BBillingMetrics;
}

// Props dos componentes
export interface CompanyBillingCardProps {
  company: {
    id: number;
    name: string;
    tax_id?: string;
  };
  subscription?: CompanySubscription;
  onCreateSubscription?: (companyId: number) => void;
  onManageSubscription?: (subscription: CompanySubscription) => void;
  onCreateInvoice?: (
    companyId: number,
    subscription?: CompanySubscription
  ) => void;
}

export interface InvoiceListProps {
  companyId?: number;
  status?: string;
  limit?: number;
  onInvoiceClick?: (invoice: ProTeamCareInvoice) => void;
  onPaymentConfirm?: (invoice: ProTeamCareInvoice) => void;
}

export interface B2BDashboardProps {
  refreshInterval?: number;
  onCompanyClick?: (companyId: number) => void;
  onInvoiceClick?: (invoice: ProTeamCareInvoice) => void;
}
