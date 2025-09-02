/**
 * API Types - Sincronizados com Backend Pydantic Models
 * Baseado em: app/presentation/schemas/
 */

// ===============================
// ENUMS - Sincronizados com Backend
// ===============================

export enum PersonType {
  PF = "PF",
  PJ = "PJ"
}

export enum PersonStatus {
  ACTIVE = "active",
  INACTIVE = "inactive", 
  PENDING = "pending",
  SUSPENDED = "suspended",
  BLOCKED = "blocked"
}

export enum PhoneType {
  LANDLINE = "landline",
  MOBILE = "mobile",
  WHATSAPP = "whatsapp",
  COMMERCIAL = "commercial",
  EMERGENCY = "emergency",
  FAX = "fax"
}

export enum LineType {
  PREPAID = "prepaid",
  POSTPAID = "postpaid",
  CORPORATE = "corporate"
}

export enum EmailType {
  PERSONAL = "personal",
  WORK = "work",
  BILLING = "billing",
  CONTACT = "contact"
}

export enum AddressType {
  RESIDENTIAL = "residential",
  COMMERCIAL = "commercial",
  CORRESPONDENCE = "correspondence",
  BILLING = "billing",
  DELIVERY = "delivery"
}

export enum AccessDifficulty {
  EASY = "easy",
  MEDIUM = "medium",
  HARD = "hard",
  UNKNOWN = "unknown"
}

// ===============================
// BASE INTERFACES
// ===============================

export interface BaseEntity {
  id: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

// ===============================
// PHONE INTERFACES
// ===============================

export interface PhoneBase {
  country_code: string;
  number: string;
  extension?: string;
  type: PhoneType;
  is_principal: boolean;
  is_active: boolean;
  phone_name?: string;
  is_whatsapp: boolean;
  whatsapp_verified: boolean;
  whatsapp_business: boolean;
  whatsapp_name?: string;
  accepts_whatsapp_marketing: boolean;
  accepts_whatsapp_notifications: boolean;
  whatsapp_preferred_time_start?: string;
  whatsapp_preferred_time_end?: string;
  carrier?: string;
  line_type?: LineType;
  contact_priority: number;
  can_receive_calls: boolean;
  can_receive_sms: boolean;
}

export interface Phone extends PhoneBase, BaseEntity {
  whatsapp_formatted?: string;
  whatsapp_verified_at?: string;
  last_contact_attempt?: string;
  last_contact_success?: string;
  contact_attempts_count: number;
  verified_at?: string;
  verification_method?: string;
}

export interface PhoneCreate extends PhoneBase {}

export interface PhoneUpdate extends Partial<PhoneBase> {}

// ===============================
// EMAIL INTERFACES
// ===============================

export interface EmailBase {
  email_address: string;
  type: EmailType;
  is_principal: boolean;
  is_active: boolean;
}

export interface Email extends EmailBase, BaseEntity {
  verified_at?: string;
}

export interface EmailCreate extends EmailBase {}
export interface EmailUpdate extends Partial<EmailBase> {}

// ===============================
// ADDRESS INTERFACES
// ===============================

export interface AddressBase {
  street: string;
  number?: string;
  details?: string;
  neighborhood: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  type: AddressType;
  is_principal: boolean;
  
  // Geocoding fields
  latitude?: number;
  longitude?: number;
  google_place_id?: string;
  geocoding_accuracy?: string;
  geocoding_source?: string;
  formatted_address?: string;
  coordinates_added_at?: string;
  coordinates_source?: string;
  
  // Enrichment metadata
  enriched_at?: string;
  enrichment_source?: string;
  validation_source?: string;
  last_validated_at?: string;
  is_validated: boolean;
  
  // Códigos oficiais brasileiros (ViaCEP)
  ibge_city_code?: number;
  ibge_state_code?: number;
  gia_code?: string;
  siafi_code?: string;
  area_code?: string;
}

export interface Address extends AddressBase, BaseEntity {
  region?: string;
  microregion?: string;
  mesoregion?: string;
  within_coverage?: boolean;
  distance_to_establishment?: number;
  estimated_travel_time?: number;
  access_difficulty?: AccessDifficulty;
  access_notes?: string;
  quality_score?: number;
  api_data?: Record<string, any>;
}

export interface AddressCreate extends AddressBase {}
export interface AddressUpdate extends Partial<AddressBase> {}

// ===============================
// PEOPLE INTERFACES
// ===============================

export interface PeopleBase {
  person_type: PersonType;
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
}

export interface People extends PeopleBase, BaseEntity {
  lgpd_consent_version?: string;
  lgpd_consent_given_at?: string;
  lgpd_data_retention_expires_at?: string;
}

export interface PeopleCreate extends PeopleBase {}
export interface PeopleUpdate extends Partial<PeopleBase> {}

// ===============================
// COMPANY INTERFACES
// ===============================

export interface CompanyBase {
  settings?: Record<string, any>;
  metadata?: Record<string, any>;
  display_order: number;
}

export interface Company extends CompanyBase, BaseEntity {
  person_id: number;
}

export interface CompanyDetailed extends Company {
  people: People;
  phones: Phone[];
  emails: Email[];
  addresses: Address[];
}

export interface CompanyCreate {
  people: PeopleCreate;
  company: CompanyBase;
  phones?: PhoneCreate[];
  emails?: EmailCreate[];
  addresses?: AddressCreate[];
}

export interface CompanyUpdate {
  people?: PeopleUpdate;
  company?: Partial<CompanyBase>;
  phones?: PhoneCreate[];
  emails?: EmailCreate[];
  addresses?: AddressCreate[];
}

export interface CompanyList {
  id: number;
  person_id: number;
  name: string;
  trade_name?: string;
  tax_id: string;
  status: PersonStatus;
  phones_count: number;
  emails_count: number;
  addresses_count: number;
  created_at: string;
  updated_at: string;
}

// ===============================
// AUTH INTERFACES
// ===============================

export interface Token {
  access_token: string;
  token_type: string;
}

export interface TokenData {
  email?: string;
}

// ===============================
// API RESPONSE TYPES
// ===============================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  detail: string;
  type?: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}