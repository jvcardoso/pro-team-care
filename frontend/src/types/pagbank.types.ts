/**
 * PagBank Integration Types
 * TypeScript interfaces for PagBank payment integration
 */

export interface PagBankBaseResponse {
  success: boolean;
  message?: string;
  error?: string;
}

// ==========================================
// BILLING METHOD TYPES
// ==========================================

export interface BillingMethodUpdate {
  billing_method: "recurrent" | "manual";
  auto_fallback_enabled?: boolean;
}

export interface BillingMethodStatus {
  contract_id: number;
  billing_method: "recurrent" | "manual";
  is_active: boolean;
  next_billing_date?: string;
  auto_fallback_enabled: boolean;
  attempt_count: number;
  last_attempt_date?: string;
  pagbank_data?: {
    subscription_id?: string;
    customer_id?: string;
    subscription_status?: string;
    next_billing_date?: string;
    status_check_error?: string;
  };
}

// ==========================================
// RECURRENT BILLING TYPES
// ==========================================

export interface CardData {
  card_number: string;
  card_expiry_month: string;
  card_expiry_year: string;
  card_cvv: string;
  card_holder_name: string;
}

export interface AddressData {
  street: string;
  number: string;
  details?: string;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
}

export interface ClientDataForRecurrent {
  client_id: number;
  name: string;
  email: string;
  tax_id: string;
  phone_area: string;
  phone_number: string;
  address: AddressData;
  card_data: CardData;
}

export interface RecurrentBillingSetupRequest {
  contract_id: number;
  client_data: ClientDataForRecurrent;
}

export interface RecurrentBillingSetupResponse extends PagBankBaseResponse {
  contract_id?: number;
  billing_method?: string;
  pagbank_subscription_id?: string;
  pagbank_customer_id?: string;
  next_billing_date?: string;
  setup_details?: {
    plan?: any;
    customer?: any;
    subscription?: any;
  };
}

// ==========================================
// CHECKOUT TYPES
// ==========================================

export interface CheckoutSessionRequest {
  invoice_id: number;
}

export interface CheckoutSessionResponse extends PagBankBaseResponse {
  invoice_id?: number;
  checkout_url?: string;
  session_id?: string;
  expires_at?: string;
  qr_code?: string;
  transaction_id?: number;
}

// ==========================================
// TRANSACTION TYPES
// ==========================================

export interface PagBankTransaction {
  id: number;
  invoice_id: number;
  transaction_type: "recurrent" | "checkout";
  pagbank_transaction_id?: string;
  pagbank_charge_id?: string;
  status: "pending" | "approved" | "declined" | "failed" | "cancelled";
  amount: number;
  payment_method?: string;
  error_message?: string;
  webhook_data?: any;
  created_at: string;
  updated_at: string;
}

export interface TransactionsListResponse {
  transactions: PagBankTransaction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==========================================
// SUBSCRIPTION MANAGEMENT TYPES
// ==========================================

export interface SubscriptionCancelRequest {
  contract_id: number;
  reason?: string;
}

export interface SubscriptionCancelResponse extends PagBankBaseResponse {
  contract_id?: number;
  cancelled_subscription_id?: string;
  new_billing_method?: string;
  cancellation_details?: any;
}

// ==========================================
// BILLING AUTOMATION TYPES
// ==========================================

export interface AutomaticBillingRequest {
  billing_date?: string;
  force_regenerate?: boolean;
  contract_ids?: number[];
}

export interface AutomaticBillingResponse extends PagBankBaseResponse {
  total_processed?: number;
  successful?: number;
  failed?: number;
  errors?: string[];
  results?: Array<{
    schedule_id: number;
    contract_id: number;
    status: "success" | "failed" | "error";
    invoice_id?: number;
    error?: string;
    failure_result?: any;
  }>;
  executed_at?: string;
}

// ==========================================
// DASHBOARD TYPES
// ==========================================

export interface BillingMethodStats {
  total_contracts: number;
  recurrent_count: number;
  manual_count: number;
  recurrent_percentage: number;
  manual_percentage: number;
  failed_recurrent_count: number;
  fallback_triggered_count: number;
}

export interface PagBankDashboardResponse {
  billing_method_stats: BillingMethodStats;
  recent_transactions: PagBankTransaction[];
  pending_checkouts: number;
  failed_recurrent_billings: number;
  total_revenue_recurrent: number;
  total_revenue_manual: number;
}

// ==========================================
// WEBHOOK TYPES
// ==========================================

export interface WebhookResponse extends PagBankBaseResponse {
  notification_type?: string;
  processed_data?: any;
}

// ==========================================
// FORM TYPES
// ==========================================

export interface CreditCardFormData {
  cardNumber: string;
  expiryMonth: string;
  expiryYear: string;
  cvv: string;
  holderName: string;
}

export interface PaymentMethodSelectionData {
  method: "recurrent" | "manual";
  autoFallback: boolean;
}

// ==========================================
// ERROR TYPES
// ==========================================

export interface PagBankError extends Error {
  error_code?: string;
  details?: any;
  timestamp?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

export interface ErrorResponse extends PagBankBaseResponse {
  error_code?: string;
  validation_errors?: ValidationError[];
  details?: any;
}

// ==========================================
// UI STATE TYPES
// ==========================================

export interface PagBankFormState {
  loading: boolean;
  error?: string;
  success?: boolean;
  data?: any;
}

export interface CheckoutState {
  loading: boolean;
  checkoutUrl?: string;
  sessionId?: string;
  expiresAt?: string;
  qrCode?: string;
  error?: string;
}

export interface BillingMethodState {
  current: BillingMethodStatus | null;
  loading: boolean;
  error?: string;
  updating: boolean;
}
