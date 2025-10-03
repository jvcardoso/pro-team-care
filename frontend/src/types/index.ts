/**
 * Types Index - Exportação centralizada
 * Ponto único de importação para todos os tipos
 */

// 🔄 Enums sincronizados com backend
export * from "./enums";

// 🏢 API Types (sincronizados com backend)
export * from "./api";

// 🎨 Component Types (frontend específicos)
export * from "./components";

// Re-exports mais utilizados (tipos)
export type {
  People,
  Phone,
  Email,
  Address,
  Token,
  UserInfo,
  CompanyFormData,
  PaginatedResponse,
  HealthStatus,
  ApiResponse,
  ApiError,
  // Client types
  ClientDetailed,
  ClientCreate,
  ClientUpdate,
  ClientListResponse,
  ClientValidationResponse,
  PersonForClient,
} from "./api";

// Company types
export type {
  Company,
  CompanyDetailed,
  CompanyCreate,
  CompanyUpdate,
} from "./company.types";

// Re-exports de enums (valores) - SINCRONIZADOS
export {
  PersonType,
  PhoneType,
  EmailType,
  AddressType,
  CompanyStatus,
  TaxRegime,
  CountryCode,
  BrazilianState,
} from "./enums";

// Re-exports de labels para display
export {
  PhoneTypeLabels,
  EmailTypeLabels,
  AddressTypeLabels,
  PersonTypeLabels,
  CompanyStatusLabels,
  TaxRegimeLabels,
} from "./enums";

export type {
  FormState,
  ValidationResult,
  CompanyFormData,
  CompanyFormProps,
  ClientFormData,
  ClientFormProps,
  ButtonProps,
  TableProps,
  UseFormReturn,
  RequestOptions,
} from "./components";
