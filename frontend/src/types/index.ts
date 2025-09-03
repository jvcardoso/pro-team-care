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
  Company,
  People,
  Phone,
  Email,
  Address,
  Token,
  UserInfo,
  CompanyFormData,
  PaginatedResponse,
  HealthStatus,
} from "./api";

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
  ButtonProps,
  TableProps,
  UseFormReturn,
} from "./components";
