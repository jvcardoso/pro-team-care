import {
  Phone,
  Email,
  Address,
  PhoneType,
  EmailType,
  AddressType,
} from "../types";

interface CompanyData {
  id: number;
  name: string;
  tax_id: string;
  people?: {
    name: string;
    tax_id: string;
    description?: string;
  };
  phones?: Array<{
    id?: number;
    country_code: string;
    number: string;
    extension?: string;
    type: string;
    is_principal: boolean;
    is_active: boolean;
    phone_name?: string;
    is_whatsapp: boolean;
    whatsapp_verified?: boolean;
    whatsapp_business?: boolean;
    whatsapp_name?: string;
    accepts_whatsapp_marketing: boolean;
    accepts_whatsapp_notifications: boolean;
    whatsapp_preferred_time_start?: string;
    whatsapp_preferred_time_end?: string;
    carrier?: string;
    line_type?: string;
    contact_priority: number;
    can_receive_calls: boolean;
    can_receive_sms: boolean;
  }>;
  emails?: Array<{
    id?: number;
    email_address: string;
    type: string;
    is_principal: boolean;
    is_active: boolean;
    verified_at?: string;
  }>;
  addresses?: Array<{
    id?: number;
    street: string;
    number?: string;
    details?: string;
    neighborhood?: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
    type: string;
    is_principal: boolean;
    latitude?: number;
    longitude?: number;
    google_place_id?: string;
    formatted_address?: string;
    geocoding_accuracy?: string;
    geocoding_source?: string;
    ibge_city_code?: string;
    ibge_state_code?: string;
    gia_code?: string;
    siafi_code?: string;
    area_code?: string;
  }>;
}

interface EstablishmentFormData {
  person: {
    name: string;
    tax_id: string;
    person_type: string;
    status: string;
    description: string;
  };
  establishment: {
    company_id: number;
    code: string;
    type: string;
    category: string;
    is_active: boolean;
    is_principal: boolean;
    display_order: number;
    settings: Record<string, any>;
    operating_hours: Record<string, any>;
    service_areas: Record<string, any>;
  };
  phones: Array<Partial<Phone>>;
  emails: Array<Partial<Email>>;
  addresses: Array<Partial<Address>>;
}

/**
 * Mapeia os dados da empresa para o formato do formulário de estabelecimento
 */
export const mapCompanyDataToEstablishment = (
  company: CompanyData,
  currentFormData: EstablishmentFormData
): EstablishmentFormData => {
  const mappedData: EstablishmentFormData = { ...currentFormData };

  // 1. Mapear dados da pessoa (establishment) - deixar CNPJ vazio para usuário preencher
  if (company.people) {
    mappedData.person = {
      ...mappedData.person,
      name: company.people.name || company.name,
      tax_id: "", // Deixar vazio para usuário preencher manualmente
      description: company.people.description || "",
    };
  } else {
    // Fallback se não houver dados de people
    mappedData.person = {
      ...mappedData.person,
      name: company.name,
      tax_id: "", // Deixar vazio para usuário preencher manualmente
      description: "",
    };
  }

  // 2. Atualizar company_id no establishment
  mappedData.establishment = {
    ...mappedData.establishment,
    company_id: company.id,
  };

  // 3. Mapear telefones
  if (company.phones && company.phones.length > 0) {
    mappedData.phones = company.phones.map((phone) => ({
      country_code: phone.country_code,
      number: phone.number,
      extension: phone.extension || "",
      type: mapPhoneType(phone.type),
      is_principal: phone.is_principal,
      is_active: phone.is_active,
      phone_name: phone.phone_name || "",
      is_whatsapp: phone.is_whatsapp,
      whatsapp_verified: phone.whatsapp_verified || false,
      whatsapp_business: phone.whatsapp_business || false,
      whatsapp_name: phone.whatsapp_name || "",
      accepts_whatsapp_marketing: phone.accepts_whatsapp_marketing,
      accepts_whatsapp_notifications: phone.accepts_whatsapp_notifications,
      whatsapp_preferred_time_start: phone.whatsapp_preferred_time_start || "",
      whatsapp_preferred_time_end: phone.whatsapp_preferred_time_end || "",
      carrier: phone.carrier || "",
      line_type: phone.line_type || "",
      contact_priority: phone.contact_priority,
      can_receive_calls: phone.can_receive_calls,
      can_receive_sms: phone.can_receive_sms,
    }));
  }

  // 4. Mapear emails
  if (company.emails && company.emails.length > 0) {
    mappedData.emails = company.emails.map((email) => ({
      email_address: email.email_address,
      type: mapEmailType(email.type),
      is_principal: email.is_principal,
      is_active: email.is_active,
    }));
  }

  // 5. Mapear endereços
  if (company.addresses && company.addresses.length > 0) {
    mappedData.addresses = company.addresses.map((address) => ({
      street: address.street,
      number: address.number || "",
      details: address.details || "",
      neighborhood: address.neighborhood || "",
      city: address.city,
      state: address.state,
      zip_code: address.zip_code,
      country: address.country,
      type: mapAddressType(address.type),
      is_principal: address.is_principal,
      latitude: address.latitude,
      longitude: address.longitude,
      google_place_id: address.google_place_id || "",
      formatted_address: address.formatted_address || "",
      geocoding_accuracy: address.geocoding_accuracy || "",
      geocoding_source: address.geocoding_source || "",
      ibge_city_code: address.ibge_city_code || "",
      ibge_state_code: address.ibge_state_code || "",
      gia_code: address.gia_code || "",
      siafi_code: address.siafi_code || "",
      area_code: address.area_code || "",
    }));
  }

  return mappedData;
};

/**
 * Mapeia o tipo de telefone da empresa para o tipo do estabelecimento
 */
const mapPhoneType = (companyPhoneType: string): PhoneType => {
  const typeMapping: Record<string, PhoneType> = {
    landline: PhoneType.LANDLINE,
    mobile: PhoneType.MOBILE,
    whatsapp: PhoneType.WHATSAPP,
    commercial: PhoneType.COMMERCIAL,
    emergency: PhoneType.EMERGENCY,
    fax: PhoneType.FAX,
  };

  return typeMapping[companyPhoneType] || PhoneType.COMMERCIAL;
};

/**
 * Mapeia o tipo de email da empresa para o tipo do estabelecimento
 */
const mapEmailType = (companyEmailType: string): EmailType => {
  const typeMapping: Record<string, EmailType> = {
    personal: EmailType.PERSONAL,
    work: EmailType.WORK,
    billing: EmailType.BILLING,
    contact: EmailType.CONTACT,
  };

  return typeMapping[companyEmailType] || EmailType.WORK;
};

/**
 * Mapeia o tipo de endereço da empresa para o tipo do estabelecimento
 */
const mapAddressType = (companyAddressType: string): AddressType => {
  const typeMapping: Record<string, AddressType> = {
    residential: AddressType.RESIDENTIAL,
    commercial: AddressType.COMMERCIAL,
    correspondence: AddressType.CORRESPONDENCE,
    billing: AddressType.BILLING,
    delivery: AddressType.DELIVERY,
  };

  return typeMapping[companyAddressType] || AddressType.COMMERCIAL;
};

/**
 * Verifica se a empresa tem dados suficientes para copiar
 */
export const hasCompanyDataToCopy = (company: CompanyData): boolean => {
  const hasBasicData = company.name && company.tax_id;
  const hasContacts =
    (company.phones && company.phones.length > 0) ||
    (company.emails && company.emails.length > 0) ||
    (company.addresses && company.addresses.length > 0);

  return hasBasicData || hasContacts;
};
