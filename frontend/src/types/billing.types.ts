/**
 * Types for Billing System Frontend
 * Mirrors backend schemas with frontend-specific additions
 */

import { BaseEntity } from "./dataTable.types";

// ==========================================
// ENUMS
// ==========================================

export enum BillingCycle {
  DAILY = "DAILY",
  WEEKLY = "WEEKLY",
  MONTHLY = "MONTHLY",
  QUARTERLY = "QUARTERLY",
  SEMI_ANNUAL = "SEMI_ANNUAL",
  ANNUAL = "ANNUAL",
}

export enum InvoiceStatus {
  PENDENTE = "pendente",
  ENVIADA = "enviada",
  PAGA = "paga",
  VENCIDA = "vencida",
  CANCELADA = "cancelada",
  EM_ATRASO = "em_atraso",
}

export enum VerificationStatus {
  PENDENTE = "pendente",
  APROVADO = "aprovado",
  REJEITADO = "rejeitado",
}

export enum PaymentMethod {
  PIX = "PIX",
  TRANSFERENCIA = "TRANSFERENCIA",
  TED = "TED",
  BOLETO = "BOLETO",
  CARTAO = "CARTAO",
  DINHEIRO = "DINHEIRO",
  DEPOSITO = "DEPOSITO",
}

// ==========================================
// BILLING SCHEDULE TYPES
// ==========================================

export interface BillingSchedule extends BaseEntity {
  contract_id: number;
  billing_cycle: BillingCycle;
  billing_day: number;
  next_billing_date: string;
  amount_per_cycle: number;
  is_active: boolean;
  created_by?: number;
  contract?: {
    id: number;
    contract_number: string;
    client_name?: string;
  };
}

export interface BillingScheduleCreate {
  contract_id: number;
  billing_cycle: BillingCycle;
  billing_day: number;
  next_billing_date: string;
  amount_per_cycle: number;
  is_active?: boolean;
}

export interface BillingScheduleUpdate {
  billing_cycle?: BillingCycle;
  billing_day?: number;
  next_billing_date?: string;
  amount_per_cycle?: number;
  is_active?: boolean;
}

export interface BillingScheduleListParams {
  contract_id?: number;
  billing_cycle?: BillingCycle;
  is_active?: boolean;
  next_billing_before?: string;
  page?: number;
  size?: number;
}

export interface BillingScheduleListResponse {
  schedules: BillingSchedule[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==========================================
// INVOICE TYPES
// ==========================================

export interface Invoice extends BaseEntity {
  contract_id: number;
  invoice_number: string;
  billing_period_start: string;
  billing_period_end: string;
  lives_count: number;
  base_amount: number;
  additional_services_amount: number;
  discounts: number;
  taxes: number;
  total_amount: number;
  status: InvoiceStatus;
  due_date: string;
  issued_date: string;
  paid_date?: string;
  payment_method?: PaymentMethod;
  payment_reference?: string;
  payment_notes?: string;
  observations?: string;
  created_by?: number;
  updated_by?: number;
  contract?: {
    id: number;
    contract_number: string;
    client_name?: string;
  };
}

export interface InvoiceDetailed extends Invoice {
  receipts_count: number;
  is_overdue: boolean;
  days_overdue: number;
  receipts?: PaymentReceipt[];
}

export interface InvoiceCreate {
  contract_id: number;
  billing_period_start: string;
  billing_period_end: string;
  lives_count: number;
  base_amount: number;
  additional_services_amount?: number;
  discounts?: number;
  taxes?: number;
  total_amount: number;
  due_date: string;
  issued_date?: string;
  observations?: string;
}

export interface InvoiceUpdate {
  billing_period_start?: string;
  billing_period_end?: string;
  lives_count?: number;
  base_amount?: number;
  additional_services_amount?: number;
  discounts?: number;
  taxes?: number;
  total_amount?: number;
  status?: InvoiceStatus;
  due_date?: string;
  paid_date?: string;
  payment_method?: PaymentMethod;
  payment_reference?: string;
  payment_notes?: string;
  observations?: string;
}

export interface InvoiceListParams {
  contract_id?: number;
  status?: InvoiceStatus;
  start_date?: string;
  end_date?: string;
  overdue_only?: boolean;
  page?: number;
  size?: number;
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaymentDetails {
  paid_date?: string;
  payment_method?: PaymentMethod;
  payment_reference?: string;
  payment_notes?: string;
}

// ==========================================
// PAYMENT RECEIPT TYPES
// ==========================================

export interface PaymentReceipt extends BaseEntity {
  invoice_id: number;
  file_name: string;
  file_path: string;
  file_type?: string;
  file_size?: number;
  upload_date: string;
  verification_status: VerificationStatus;
  verified_by?: number;
  verified_at?: string;
  notes?: string;
  uploaded_by?: number;
  invoice?: {
    id: number;
    invoice_number: string;
  };
}

export interface PaymentReceiptCreate {
  invoice_id: number;
  file_name: string;
  file_path: string;
  file_type?: string;
  file_size?: number;
  notes?: string;
}

export interface PaymentReceiptUpdate {
  file_name?: string;
  file_type?: string;
  verification_status?: VerificationStatus;
  notes?: string;
}

export interface ReceiptListParams {
  invoice_id?: number;
  verification_status?: VerificationStatus;
  uploaded_by?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

export interface ReceiptListResponse {
  receipts: PaymentReceipt[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==========================================
// DASHBOARD TYPES
// ==========================================

export interface BillingMetrics {
  total_pending_invoices: number;
  total_pending_amount: number;
  total_overdue_invoices: number;
  total_overdue_amount: number;
  total_paid_this_month: number;
  total_expected_this_month: number;
  collection_rate_percentage: number;
  average_payment_delay_days?: number;
}

export interface ContractBillingStatus {
  contract_id: number;
  contract_number: string;
  client_name: string;
  monthly_value: number;
  pending_invoices: number;
  pending_amount: number;
  overdue_invoices: number;
  overdue_amount: number;
  last_payment_date?: string;
  next_billing_date?: string;
  status: string;
}

export interface BillingDashboardResponse {
  metrics: BillingMetrics;
  recent_invoices: Invoice[];
  contracts_status: ContractBillingStatus[];
  upcoming_billings: BillingSchedule[];
}

// ==========================================
// BULK OPERATIONS TYPES
// ==========================================

export interface BulkInvoiceGeneration {
  contract_ids?: number[];
  billing_date?: string;
  force_regenerate?: boolean;
}

export interface BulkInvoiceGenerationResponse {
  total_processed: number;
  successful: number;
  failed: number;
  errors: string[];
  generated_invoices: number[];
}

export interface BulkStatusUpdate {
  invoice_ids: number[];
  new_status: InvoiceStatus;
  payment_date?: string;
  payment_method?: PaymentMethod;
  payment_reference?: string;
  notes?: string;
}

export interface BulkStatusUpdateResponse {
  total_processed: number;
  successful: number;
  failed: number;
  errors: string[];
  updated_invoices: number[];
}

// ==========================================
// AUTO BILLING TYPES
// ==========================================

export interface AutoBillingRequest {
  billing_date?: string;
  force_regenerate?: boolean;
}

export interface AutoBillingResult {
  message: string;
  result: {
    total_schedules_processed: number;
    successful_invoices: number;
    failed_invoices: number;
    generated_invoice_ids: number[];
    errors: string[];
    billing_date: string;
  };
}

// ==========================================
// UI SPECIFIC TYPES
// ==========================================

export interface InvoiceStatusBadgeProps {
  status: InvoiceStatus;
  isOverdue?: boolean;
  className?: string;
}

export interface PaymentMethodBadgeProps {
  method: PaymentMethod;
  className?: string;
}

export interface BillingMetricCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "purple" | "yellow" | "red" | "gray";
  percentage?: number;
  trend?: "up" | "down" | "neutral";
  loading?: boolean;
}

export interface ReceiptUploadProps {
  invoiceId: number;
  onUploadSuccess?: (receipt: PaymentReceipt) => void;
  onUploadError?: (error: string) => void;
  maxFileSize?: number;
  allowedTypes?: string[];
}

export interface InvoiceFiltersProps {
  filters: InvoiceListParams;
  onFiltersChange: (filters: InvoiceListParams) => void;
  onReset: () => void;
}

// ==========================================
// API RESPONSE WRAPPERS
// ==========================================

export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ==========================================
// FORM TYPES
// ==========================================

export interface InvoiceFormData {
  contract_id: number;
  billing_period_start: string;
  billing_period_end: string;
  lives_count: number;
  base_amount: number;
  additional_services_amount: number;
  discounts: number;
  taxes: number;
  due_date: string;
  observations?: string;
}

export interface PaymentFormData {
  status: InvoiceStatus;
  paid_date: string;
  payment_method: PaymentMethod;
  payment_reference?: string;
  payment_notes?: string;
}

export interface ReceiptVerificationFormData {
  verification_status: VerificationStatus;
  notes?: string;
}

// ==========================================
// TABLE CONFIG TYPES
// ==========================================

export interface InvoiceTableRow extends Invoice {
  client_name?: string;
  contract_number: string;
  is_overdue?: boolean;
  days_overdue?: number;
  receipts_count?: number;
}

export interface BillingScheduleTableRow extends BillingSchedule {
  client_name?: string;
  contract_number: string;
}

export interface PaymentReceiptTableRow extends PaymentReceipt {
  invoice_number: string;
  contract_number?: string;
}

// ==========================================
// CHART DATA TYPES
// ==========================================

export interface RevenueChartData {
  month: string;
  expected: number;
  received: number;
  pending: number;
}

export interface InvoiceStatusChartData {
  status: string;
  count: number;
  amount: number;
  color: string;
}

export interface CollectionRateData {
  period: string;
  rate: number;
  target: number;
}

// ==========================================
// EXPORT TYPES
// ==========================================

export interface ExportOptions {
  format: "csv" | "xlsx" | "pdf";
  filters?: InvoiceListParams;
  includeDetails?: boolean;
}

export interface ExportResult {
  filename: string;
  url: string;
  size: number;
  generated_at: string;
}
