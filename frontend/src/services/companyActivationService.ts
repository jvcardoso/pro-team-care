/**
 * Serviço de API para processo de ativação de empresas
 *
 * Este serviço centraliza todas as chamadas à API relacionadas ao
 * processo de ativação de empresas no sistema.
 */

import api from "./api";

export interface SendContractEmailRequest {
  company_id: number;
  recipient_email: string;
  recipient_name: string;
}

export interface AcceptContractRequest {
  contract_token: string;
  accepted_by_name: string;
  accepted_by_email: string;
  accepted_by_cpf?: string;
  ip_address: string;
  terms_version?: string;
}

export interface ValidateTokenRequest {
  token: string;
}

export interface CreateManagerUserRequest {
  token: string;
  user_name: string;
  user_email: string;
  password: string;
}

export interface SendEmailResponse {
  success: boolean;
  message: string;
  company_id: number;
  sent_to: string;
  sent_at: string;
}

export interface AcceptContractResponse {
  success: boolean;
  message: string;
  company_id: number;
  access_status: string;
  contract_accepted_at: string;
  next_step: string;
}

export interface ValidateTokenResponse {
  valid: boolean;
  company_id?: number;
  company_name?: string;
  token_type?: string;
  expires_at?: string;
  expired: boolean;
  error_message?: string;
}

export interface CompanyActivationStatus {
  company_id: number;
  company_name: string;
  access_status:
    | "pending_contract"
    | "contract_signed"
    | "pending_user"
    | "active"
    | "suspended";
  contract_sent: boolean;
  contract_sent_at?: string;
  contract_sent_to?: string;
  contract_accepted: boolean;
  contract_accepted_at?: string;
  contract_accepted_by?: string;
  contract_terms_version?: string;
  has_active_user: boolean;
  activated_at?: string;
  activated_by_user_id?: number;
  days_since_creation?: number;
  days_since_contract_sent?: number;
  is_overdue: boolean;
}

export interface PendingCompaniesResponse {
  stats: {
    total: number;
    pending_contract: number;
    contract_signed: number;
    pending_user: number;
    overdue: number;
  };
  companies: CompanyActivationStatus[];
}

/**
 * Envia email de aceite de contrato para empresa
 */
export const sendContractEmail = async (
  data: SendContractEmailRequest
): Promise<SendEmailResponse> => {
  const response = await api.post(
    "/company-activation/send-contract-email",
    data
  );
  return response.data;
};

/**
 * Registra aceite de contrato (endpoint público)
 */
export const acceptContract = async (
  data: AcceptContractRequest
): Promise<AcceptContractResponse> => {
  const response = await api.post(
    "/api/v1/company-activation/accept-contract",
    data
  );
  return response.data;
};

/**
 * Valida token de criação de usuário (endpoint público)
 */
export const validateUserCreationToken = async (
  token: string
): Promise<ValidateTokenResponse> => {
  const response = await api.post(
    "/api/v1/company-activation/validate-user-token",
    {
      token,
    }
  );
  return response.data;
};

/**
 * Cria usuário gestor usando token (endpoint público)
 */
export const createManagerUser = async (
  data: CreateManagerUserRequest
): Promise<any> => {
  const response = await api.post(
    "/api/v1/company-activation/create-manager-user",
    null,
    {
      params: data,
    }
  );
  return response.data;
};

/**
 * Consulta status de ativação da empresa
 */
export const getCompanyActivationStatus = async (
  companyId: number
): Promise<CompanyActivationStatus> => {
  const response = await api.get(
    `/api/v1/company-activation/status/${companyId}`
  );
  return response.data;
};

/**
 * Reenvia email de aceite de contrato
 */
export const resendContractEmail = async (
  companyId: number
): Promise<SendEmailResponse> => {
  const response = await api.post(
    "/api/v1/company-activation/resend-contract-email",
    {
      company_id: companyId,
    }
  );
  return response.data;
};

/**
 * Lista empresas pendentes de ativação
 */
export const getPendingCompanies =
  async (): Promise<PendingCompaniesResponse> => {
    const response = await api.get(
      "/api/v1/company-activation/pending-companies"
    );
    return response.data;
  };

/**
 * Helper: Retorna label do status em português
 */
export const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending_contract: "Aguardando Contrato",
    contract_signed: "Contrato Assinado",
    pending_user: "Aguardando Usuário",
    active: "Ativa",
    suspended: "Suspensa",
  };
  return labels[status] || status;
};

/**
 * Helper: Retorna classes CSS do badge de status
 */
export const getStatusBadgeClasses = (status: string): string => {
  const classes: Record<string, string> = {
    pending_contract:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    contract_signed:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    pending_user:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    active:
      "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    suspended: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };
  return classes[status] || "bg-gray-100 text-gray-800";
};

/**
 * Helper: Retorna ícone do status
 */
export const getStatusIcon = (status: string): string => {
  const icons: Record<string, string> = {
    pending_contract: "⏳",
    contract_signed: "✅",
    pending_user: "👤",
    active: "🟢",
    suspended: "🔴",
  };
  return icons[status] || "❓";
};

/**
 * Helper: Verifica se empresa pode receber email de contrato
 */
export const canSendContractEmail = (status: string): boolean => {
  return status === "pending_contract";
};

/**
 * Helper: Verifica se empresa pode receber reenvio
 */
export const canResendEmail = (status: string): boolean => {
  return status === "pending_contract" || status === "contract_signed";
};

/**
 * Helper: Obtém IP do cliente (para registro de aceite)
 */
export const getClientIpAddress = async (): Promise<string> => {
  try {
    // Tenta obter IP via serviço externo
    const response = await fetch("https://api.ipify.org?format=json");
    const data = await response.json();
    return data.ip;
  } catch (error) {
    // Fallback: retorna localhost
    return "127.0.0.1";
  }
};

export default {
  sendContractEmail,
  acceptContract,
  validateUserCreationToken,
  createManagerUser,
  getCompanyActivationStatus,
  resendContractEmail,
  getPendingCompanies,
  getStatusLabel,
  getStatusBadgeClasses,
  getStatusIcon,
  canSendContractEmail,
  canResendEmail,
  getClientIpAddress,
};
