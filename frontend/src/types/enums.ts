/**
 * Enums sincronizados com backend FastAPI
 * Baseado em: app/domain/entities/enums.py
 * 🔄 MANTER SINCRONIZADO com backend
 */

// 📱 Phone Types - Sincronizado com PhoneType enum
export enum PhoneType {
  LANDLINE = "landline",
  MOBILE = "mobile",
  WHATSAPP = "whatsapp",
  COMMERCIAL = "commercial",
  EMERGENCY = "emergency",
  FAX = "fax",
}

// 📧 Email Types - Sincronizado com EmailType enum
export enum EmailType {
  PERSONAL = "personal",
  WORK = "work",
  COMMERCIAL = "commercial",
  BILLING = "billing",
  SUPPORT = "support",
  OTHER = "other",
}

// 🏠 Address Types - Sincronizado com AddressType enum
export enum AddressType {
  RESIDENTIAL = "residential",
  COMMERCIAL = "commercial",
  BILLING = "billing",
  SHIPPING = "shipping",
  CORRESPONDENCE = "correspondence",
  OTHER = "other",
}

// 👥 Person Types - Sincronizado com PersonType enum
export enum PersonType {
  PF = "PF", // Pessoa Física
  PJ = "PJ", // Pessoa Jurídica
}

// 🏢 Company Status - Sincronizado com CompanyStatus enum
export enum CompanyStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended",
  CANCELLED = "cancelled",
}

// 👤 Client Status - Sincronizado com ClientStatus enum
export enum ClientStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  ON_HOLD = "on_hold",
  ARCHIVED = "archived",
}

// ⚥ Gender - Sincronizado com Gender enum
export enum Gender {
  MALE = "male",
  FEMALE = "female",
  NON_BINARY = "non_binary",
  NOT_INFORMED = "not_informed",
}

// 💑 Marital Status - Sincronizado com MaritalStatus enum
export enum MaritalStatus {
  SINGLE = "single",
  MARRIED = "married",
  DIVORCED = "divorced",
  WIDOWED = "widowed",
  STABLE_UNION = "stable_union",
  NOT_INFORMED = "not_informed",
}

// 📊 Person Status - Sincronizado com PersonStatus enum
export enum PersonStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PENDING = "pending",
  SUSPENDED = "suspended",
  BLOCKED = "blocked",
}

// 💼 Tax Regime - Sincronizado com TaxRegime enum
export enum TaxRegime {
  SIMPLES_NACIONAL = "simples_nacional",
  LUCRO_PRESUMIDO = "lucro_presumido",
  LUCRO_REAL = "lucro_real",
  MEI = "mei",
}

// 🌍 Countries - Sincronizado com backend
export enum CountryCode {
  BR = "BR",
  US = "US",
  AR = "AR",
  UY = "UY",
  PY = "PY",
}

// 🗺️ Brazilian States - Sincronizado com backend
export enum BrazilianState {
  AC = "AC",
  AM = "AM",
  AP = "AP",
  AL = "AL",
  BA = "BA",
  CE = "CE",
  DF = "DF",
  ES = "ES",
  GO = "GO",
  MA = "MA",
  MT = "MT",
  MS = "MS",
  MG = "MG",
  PA = "PA",
  PB = "PB",
  PR = "PR",
  PE = "PE",
  PI = "PI",
  RJ = "RJ",
  RN = "RN",
  RS = "RS",
  RO = "RO",
  RR = "RR",
  SC = "SC",
  SP = "SP",
  SE = "SE",
  TO = "TO",
}

// 🔧 Utility functions para validação
export const isValidPhoneType = (type: string): type is PhoneType => {
  return Object.values(PhoneType).includes(type as PhoneType);
};

export const isValidEmailType = (type: string): type is EmailType => {
  return Object.values(EmailType).includes(type as EmailType);
};

export const isValidAddressType = (type: string): type is AddressType => {
  return Object.values(AddressType).includes(type as AddressType);
};

export const isValidPersonType = (type: string): type is PersonType => {
  return Object.values(PersonType).includes(type as PersonType);
};

// 🏷️ Labels para display no frontend
export const PhoneTypeLabels: Record<PhoneType, string> = {
  [PhoneType.LANDLINE]: "Fixo",
  [PhoneType.MOBILE]: "Celular",
  [PhoneType.WHATSAPP]: "WhatsApp",
  [PhoneType.COMMERCIAL]: "Comercial",
  [PhoneType.EMERGENCY]: "Emergência",
  [PhoneType.FAX]: "Fax",
};

export const EmailTypeLabels: Record<EmailType, string> = {
  [EmailType.PERSONAL]: "Pessoal",
  [EmailType.WORK]: "Trabalho",
  [EmailType.COMMERCIAL]: "Comercial",
  [EmailType.BILLING]: "Cobrança",
  [EmailType.SUPPORT]: "Suporte",
  [EmailType.OTHER]: "Outro",
};

export const AddressTypeLabels: Record<AddressType, string> = {
  [AddressType.RESIDENTIAL]: "Residencial",
  [AddressType.COMMERCIAL]: "Comercial",
  [AddressType.BILLING]: "Cobrança",
  [AddressType.SHIPPING]: "Entrega",
  [AddressType.CORRESPONDENCE]: "Correspondência",
  [AddressType.OTHER]: "Outro",
};

export const PersonTypeLabels: Record<PersonType, string> = {
  [PersonType.PF]: "Pessoa Física",
  [PersonType.PJ]: "Pessoa Jurídica",
};

export const CompanyStatusLabels: Record<CompanyStatus, string> = {
  [CompanyStatus.ACTIVE]: "Ativa",
  [CompanyStatus.INACTIVE]: "Inativa",
  [CompanyStatus.SUSPENDED]: "Suspensa",
  [CompanyStatus.CANCELLED]: "Cancelada",
};

export const TaxRegimeLabels: Record<TaxRegime, string> = {
  [TaxRegime.SIMPLES_NACIONAL]: "Simples Nacional",
  [TaxRegime.LUCRO_PRESUMIDO]: "Lucro Presumido",
  [TaxRegime.LUCRO_REAL]: "Lucro Real",
  [TaxRegime.MEI]: "Microempreendedor Individual",
};

export const ClientStatusLabels: Record<ClientStatus, string> = {
  [ClientStatus.ACTIVE]: "Ativo",
  [ClientStatus.INACTIVE]: "Inativo",
  [ClientStatus.ON_HOLD]: "Em Espera",
  [ClientStatus.ARCHIVED]: "Arquivado",
};

export const GenderLabels: Record<Gender, string> = {
  [Gender.MALE]: "Masculino",
  [Gender.FEMALE]: "Feminino",
  [Gender.NON_BINARY]: "Não Binário",
  [Gender.NOT_INFORMED]: "Não Informado",
};

export const MaritalStatusLabels: Record<MaritalStatus, string> = {
  [MaritalStatus.SINGLE]: "Solteiro(a)",
  [MaritalStatus.MARRIED]: "Casado(a)",
  [MaritalStatus.DIVORCED]: "Divorciado(a)",
  [MaritalStatus.WIDOWED]: "Viúvo(a)",
  [MaritalStatus.STABLE_UNION]: "União Estável",
  [MaritalStatus.NOT_INFORMED]: "Não Informado",
};

export const PersonStatusLabels: Record<PersonStatus, string> = {
  [PersonStatus.ACTIVE]: "Ativo",
  [PersonStatus.INACTIVE]: "Inativo",
  [PersonStatus.PENDING]: "Pendente",
  [PersonStatus.SUSPENDED]: "Suspenso",
  [PersonStatus.BLOCKED]: "Bloqueado",
};
