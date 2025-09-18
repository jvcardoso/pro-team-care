/**
 * Component Types - Frontend específicos
 * Interfaces para componentes React e state management
 */

import { ReactNode } from "react";
import {
  Company,
  CompanyDetailed,
  CompanyCreate,
  ClientDetailed,
  ClientCreate,
  Phone,
  Email,
  Address,
  PersonStatus,
  ClientStatus,
  PersonForClient,
} from "./api";

// ===============================
// FORM TYPES
// ===============================

export interface FormFieldError {
  field: string;
  message: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: FormFieldError[];
}

export interface FormState<T> {
  data: T;
  errors: Record<string, string>;
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
}

// ===============================
// INPUT COMPONENT TYPES
// ===============================

export interface BaseInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onValidation?: (result: ValidationResult) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
  className?: string;
}

export interface InputValidationProps extends BaseInputProps {
  validator?: (value: string) => ValidationResult;
  formatter?: (value: string) => string;
  mask?: string;
  maxLength?: number;
}

// ===============================
// COMPANY FORM TYPES
// ===============================

export interface CompanyFormData {
  people: {
    person_type: "PF" | "PJ";
    name: string;
    trade_name?: string;
    tax_id: string;
    secondary_tax_id?: string;
    incorporation_date?: string;
    tax_regime?: string;
    legal_nature?: string;
    municipal_registration?: string;
    website?: string;
    description?: string;
    status: PersonStatus;
  };
  company: {
    settings?: Record<string, any>;
    metadata?: Record<string, any>;
    display_order: number;
  };
  phones: Array<{
    country_code: string;
    number: string;
    type: string;
    is_principal: boolean;
    is_whatsapp: boolean;
  }>;
  emails: Array<{
    email_address: string;
    type: string;
    is_principal: boolean;
  }>;
  addresses: Array<{
    street: string;
    number?: string;
    details?: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
    type: string;
    is_principal: boolean;
    latitude?: number;
    longitude?: number;
  }>;
}

export interface CompanyFormProps {
  initialData?: CompanyDetailed;
  onSubmit: (data: CompanyCreate) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  mode?: "create" | "edit";
}

// ===============================
// CLIENT FORM TYPES
// ===============================

export interface ClientFormData {
  establishment_id: number;
  client_code?: string;
  status: ClientStatus;
  person?: {
    name: string;
    trade_name?: string;
    tax_id: string;
    secondary_tax_id?: string;
    person_type: "PF" | "PJ";
    birth_date?: string;
    gender?: "male" | "female" | "non_binary" | "not_informed";
    marital_status?:
      | "single"
      | "married"
      | "divorced"
      | "widowed"
      | "stable_union"
      | "not_informed";
    occupation?: string;
    incorporation_date?: string;
    tax_regime?: string;
    legal_nature?: string;
    municipal_registration?: string;
    website?: string;
    description?: string;
    lgpd_consent_version?: string;
  };
  existing_person_id?: number;
  phones: Array<{
    country_code: string;
    area_code?: string;
    number: string;
    extension?: string;
    type: string;
    is_principal: boolean;
    is_whatsapp: boolean;
    description?: string;
  }>;
  emails: Array<{
    email_address: string;
    type: string;
    is_principal: boolean;
    is_verified: boolean;
    description?: string;
  }>;
  addresses: Array<{
    street: string;
    number?: string;
    complement?: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
    type: string;
    is_principal: boolean;
    latitude?: number;
    longitude?: number;
    ibge_city_code?: string;
    gia_code?: string;
    siafi_code?: string;
    area_code?: string;
    description?: string;
  }>;
}

export interface ClientFormProps {
  initialData?: ClientDetailed;
  onSubmit: (data: ClientCreate) => Promise<void>;
  onCancel?: () => void;
  isLoading?: boolean;
  mode?: "create" | "edit";
  availableEstablishments?: Array<{
    id: number;
    name: string;
    establishment_code: string;
  }>;
  existingPersons?: Array<{
    id: number;
    name: string;
    tax_id: string;
    person_type: "PF" | "PJ";
  }>;
}

// ===============================
// TABLE/LIST TYPES
// ===============================

export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (item: T) => ReactNode;
}

export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  onRowClick?: (item: T) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

// ===============================
// UI COMPONENT TYPES
// ===============================

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "danger"
  | "ghost"
  | "outline";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  showCloseButton?: boolean;
}

export interface ToastProps {
  type: "success" | "error" | "warning" | "info";
  message: string;
  duration?: number;
}

// ===============================
// CONTEXT TYPES
// ===============================

export interface ThemeContextType {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

export interface AuthContextType {
  user: any; // TODO: Define User type
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// ===============================
// API SERVICE TYPES
// ===============================

export interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers?: Record<string, string>;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

// ===============================
// UTILITY TYPES
// ===============================

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type WithId<T> = T & { id: number };

export type CreateType<T> = Omit<
  T,
  "id" | "created_at" | "updated_at" | "deleted_at"
>;

export type UpdateType<T> = Partial<CreateType<T>>;

// ===============================
// HOOK TYPES
// ===============================

export interface UseFormReturn<T> {
  formData: T;
  errors: Record<keyof T, string>;
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
  handleChange: (field: keyof T, value: any) => void;
  handleSubmit: (onSubmit: (data: T) => Promise<void>) => Promise<void>;
  resetForm: (newData?: Partial<T>) => void;
  setFieldError: (field: keyof T, error: string) => void;
  clearErrors: () => void;
}
