/**
 * Types Index - Exportação centralizada
 * Ponto único de importação para todos os tipos
 */

// API Types (sincronizados com backend)
export * from './api';

// Component Types (frontend específicos)  
export * from './components';

// Re-exports mais utilizados (tipos)
export type {
  Company,
  CompanyDetailed,
  CompanyCreate,
  CompanyUpdate,
  CompanyList,
  People,
  Phone,
  Email,
  Address
} from './api';

// Re-exports de enums (valores)
export {
  PersonType,
  PersonStatus,
  PhoneType,
  EmailType,
  AddressType
} from './api';

export type {
  FormState,
  ValidationResult,
  CompanyFormData,
  CompanyFormProps,
  ButtonProps,
  TableProps,
  UseFormReturn
} from './components';