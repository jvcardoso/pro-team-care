/**
 * Interfaces TypeScript sincronizadas com backend FastAPI
 * Baseado em: app/domain/entities/models.py
 * 🔄 MANTER SINCRONIZADO com backend
 */

import {
  PhoneType,
  EmailType,
  AddressType,
  PersonType,
  CompanyStatus,
  TaxRegime,
  CountryCode,
  BrazilianState,
} from "./enums";

// 📱 Phone Interface - Sincronizado com Phone model
export interface Phone {
  id?: number;
  country_code: string;
  area_code?: string;
  number: string;
  extension?: string;
  type: PhoneType;
  is_principal: boolean;
  is_whatsapp: boolean;
  description?: string;
}

// 📧 Email Interface - Sincronizado com Email model
export interface Email {
  id?: number;
  email_address: string;
  type: EmailType;
  is_principal: boolean;
  is_verified: boolean;
  description?: string;
}

// 🏠 Address Interface - Sincronizado com Address model
export interface Address {
  id?: number;
  type: AddressType;
  street: string;
  number?: string;
  complement?: string;
  neighborhood: string;
  city: string;
  state: BrazilianState;
  zip_code: string;
  country: CountryCode;
  is_principal: boolean;
  latitude?: number;
  longitude?: number;
  ibge_city_code?: string;
  gia_code?: string;
  siafi_code?: string;
  area_code?: string;
  description?: string;
}

// 👥 People Interface - Sincronizado com People model
export interface People {
  id?: number;
  person_type: PersonType;
  name: string;
  trade_name?: string;
  tax_id: string;
  secondary_tax_id?: string;
  incorporation_date?: string;
  legal_nature?: string;
  status: CompanyStatus;
  tax_regime?: TaxRegime;
  share_capital?: number;
  description?: string;
  metadata?: Record<string, any>;
}

// 🏢 Company Interface - Sincronizado com Company model
export interface Company {
  id?: number;
  people: People;
  phones: Phone[];
  emails: Email[];
  addresses: Address[];
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

// 🔐 Auth Interfaces - Sincronizado com auth models
export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user?: UserInfo;
}

export interface UserInfo {
  id: number;
  email: string;
  name?: string;
  is_active: boolean;
  created_at?: string;
}

// 📊 API Response Interfaces
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  type?: string;
  code?: string;
}

// 🔍 Search/Filter Interfaces
export interface CompanyFilters {
  search?: string;
  status?: CompanyStatus;
  tax_regime?: TaxRegime;
  person_type?: PersonType;
  city?: string;
  state?: BrazilianState;
  page?: number;
  size?: number;
}

// 📝 Form Data Interfaces (para uso interno do frontend)
export interface CompanyFormData {
  people: Partial<People>;
  phones: Phone[];
  emails: Email[];
  addresses: Address[];
}

// 🏥 Health Check Interface
export interface HealthStatus {
  status: "healthy" | "unhealthy";
  timestamp: string;
  version?: string;
  database?: {
    status: string;
    response_time_ms?: number;
  };
  external_services?: Record<
    string,
    {
      status: string;
      response_time_ms?: number;
    }
  >;
}

// 🔄 Utility type para criar requests de update (Partial de todos os campos)
export type CompanyUpdateRequest = Partial<Company>;
export type PeopleUpdateRequest = Partial<People>;

// 🎯 Type guards para runtime validation
export const isCompany = (obj: any): obj is Company => {
  return obj && typeof obj === "object" && "people" in obj;
};

export const isPhone = (obj: any): obj is Phone => {
  return obj && typeof obj === "object" && "number" in obj && "type" in obj;
};

export const isEmail = (obj: any): obj is Email => {
  return (
    obj && typeof obj === "object" && "email_address" in obj && "type" in obj
  );
};

export const isAddress = (obj: any): obj is Address => {
  return obj && typeof obj === "object" && "street" in obj && "city" in obj;
};
