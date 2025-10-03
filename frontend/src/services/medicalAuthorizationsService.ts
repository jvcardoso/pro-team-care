/**
 * Serviço para gestão de autorizações médicas
 */

import api from "./api";

export interface MedicalAuthorization {
  id: number;
  contract_life_id: number;
  service_id: number;
  doctor_id: number;
  authorization_code: string;
  authorization_date: string;
  valid_from: string;
  valid_until: string;
  sessions_authorized?: number;
  sessions_remaining?: number;
  monthly_limit?: number;
  weekly_limit?: number;
  daily_limit?: number;
  medical_indication: string;
  contraindications?: string;
  special_instructions?: string;
  urgency_level: "URGENT" | "HIGH" | "NORMAL" | "LOW";
  requires_supervision: boolean;
  supervision_notes?: string;
  diagnosis_cid?: string;
  diagnosis_description?: string;
  treatment_goals?: string;
  expected_duration_days?: number;
  renewal_allowed: boolean;
  renewal_conditions?: string;
  status: "active" | "expired" | "cancelled" | "suspended";
  cancellation_reason?: string;
  cancelled_at?: string;
  cancelled_by?: number;
  created_at: string;
  updated_at: string;
  created_by?: number;
  updated_by?: number;
  // Related data
  service_name?: string;
  service_category?: string;
  service_type?: string;
  doctor_name?: string;
  doctor_email?: string;
  patient_name?: string;
  contract_number?: string;
}

export interface MedicalAuthorizationCreate {
  contract_life_id: number;
  service_id: number;
  doctor_id: number;
  authorization_date: string;
  valid_from: string;
  valid_until: string;
  sessions_authorized?: number;
  sessions_remaining?: number;
  monthly_limit?: number;
  weekly_limit?: number;
  daily_limit?: number;
  medical_indication: string;
  contraindications?: string;
  special_instructions?: string;
  urgency_level?: "URGENT" | "HIGH" | "NORMAL" | "LOW";
  requires_supervision?: boolean;
  supervision_notes?: string;
  diagnosis_cid?: string;
  diagnosis_description?: string;
  treatment_goals?: string;
  expected_duration_days?: number;
  renewal_allowed?: boolean;
  renewal_conditions?: string;
}

export interface MedicalAuthorizationUpdate {
  authorization_date?: string;
  valid_from?: string;
  valid_until?: string;
  sessions_authorized?: number;
  sessions_remaining?: number;
  monthly_limit?: number;
  weekly_limit?: number;
  daily_limit?: number;
  medical_indication?: string;
  contraindications?: string;
  special_instructions?: string;
  urgency_level?: "URGENT" | "HIGH" | "NORMAL" | "LOW";
  requires_supervision?: boolean;
  supervision_notes?: string;
  diagnosis_cid?: string;
  diagnosis_description?: string;
  treatment_goals?: string;
  expected_duration_days?: number;
  renewal_allowed?: boolean;
  renewal_conditions?: string;
}

export interface MedicalAuthorizationListParams {
  contract_life_id?: number;
  service_id?: number;
  doctor_id?: number;
  status?: "active" | "expired" | "cancelled" | "suspended";
  urgency_level?: "URGENT" | "HIGH" | "NORMAL" | "LOW";
  valid_from?: string;
  valid_until?: string;
  requires_supervision?: boolean;
  page?: number;
  size?: number;
}

export interface MedicalAuthorizationListResponse {
  authorizations: MedicalAuthorization[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface AuthorizationStatistics {
  total_authorizations: number;
  active_authorizations: number;
  expired_authorizations: number;
  cancelled_authorizations: number;
  suspended_authorizations: number;
  urgent_authorizations: number;
  authorizations_requiring_supervision: number;
  sessions_authorized_total: number;
  sessions_remaining_total: number;
  average_duration_days?: number;
  most_common_service?: string;
  most_active_doctor?: string;
}

export interface AuthorizationHistory {
  id: number;
  authorization_id: number;
  action: string;
  field_changed?: string;
  old_value?: string;
  new_value?: string;
  reason?: string;
  performed_by: number;
  performed_at: string;
  ip_address?: string;
  user_agent?: string;
  performed_by_name?: string;
  authorization_code?: string;
}

export interface SessionUpdateRequest {
  sessions_used: number;
  notes?: string;
}

export interface AuthorizationSuspendRequest {
  reason: string;
  suspension_until?: string;
}

export interface AuthorizationRenewRequest {
  new_valid_until: string;
  additional_sessions?: number;
  renewal_reason: string;
  changes_summary?: string;
}

export interface AuthorizationCancelRequest {
  cancellation_reason: string;
}

class MedicalAuthorizationsService {
  private readonly baseUrl = "/api/v1/medical-authorizations";

  /**
   * Listar autorizações médicas
   */
  async listAuthorizations(
    params?: MedicalAuthorizationListParams
  ): Promise<MedicalAuthorizationListResponse> {
    const queryParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const url = queryParams.toString()
      ? `${this.baseUrl}/?${queryParams}`
      : `${this.baseUrl}/`;
    const response = await api.get(url);
    return response.data;
  }

  /**
   * Buscar autorização médica por ID
   */
  async getAuthorization(id: number): Promise<MedicalAuthorization> {
    const response = await api.get(`${this.baseUrl}/${id}`);
    return response.data;
  }

  /**
   * Criar nova autorização médica
   */
  async createAuthorization(
    data: MedicalAuthorizationCreate
  ): Promise<MedicalAuthorization> {
    const response = await api.post(`${this.baseUrl}/`, data);
    return response.data;
  }

  /**
   * Atualizar autorização médica
   */
  async updateAuthorization(
    id: number,
    data: MedicalAuthorizationUpdate
  ): Promise<MedicalAuthorization> {
    const response = await api.put(`${this.baseUrl}/${id}`, data);
    return response.data;
  }

  /**
   * Cancelar autorização médica
   */
  async cancelAuthorization(
    id: number,
    data: AuthorizationCancelRequest
  ): Promise<MedicalAuthorization> {
    const response = await api.post(`${this.baseUrl}/${id}/cancel`, data);
    return response.data;
  }

  /**
   * Suspender autorização médica
   */
  async suspendAuthorization(
    id: number,
    data: AuthorizationSuspendRequest
  ): Promise<MedicalAuthorization> {
    const response = await api.post(`${this.baseUrl}/${id}/suspend`, data);
    return response.data;
  }

  /**
   * Atualizar sessões utilizadas
   */
  async updateSessions(
    id: number,
    data: SessionUpdateRequest
  ): Promise<MedicalAuthorization> {
    const response = await api.post(
      `${this.baseUrl}/${id}/update-sessions`,
      data
    );
    return response.data;
  }

  /**
   * Renovar autorização médica
   */
  async renewAuthorization(
    id: number,
    data: AuthorizationRenewRequest
  ): Promise<{
    message: string;
    new_authorization_id: number;
    new_authorization_code: string;
    renewal_id: number;
  }> {
    const response = await api.post(`${this.baseUrl}/${id}/renew`, data);
    return response.data;
  }

  /**
   * Buscar histórico de uma autorização
   */
  async getAuthorizationHistory(id: number): Promise<AuthorizationHistory[]> {
    const response = await api.get(`${this.baseUrl}/${id}/history`);
    return response.data;
  }

  /**
   * Obter estatísticas de autorizações
   */
  async getStatistics(
    startDate?: string,
    endDate?: string
  ): Promise<AuthorizationStatistics> {
    const queryParams = new URLSearchParams();

    if (startDate) queryParams.append("start_date", startDate);
    if (endDate) queryParams.append("end_date", endDate);

    const url = queryParams.toString()
      ? `${this.baseUrl}/statistics/overview?${queryParams}`
      : `${this.baseUrl}/statistics/overview`;

    const response = await api.get(url);
    return response.data;
  }

  /**
   * Buscar autorizações que vencem em breve
   */
  async getExpiring(days: number = 7): Promise<MedicalAuthorization[]> {
    const response = await api.get(
      `${this.baseUrl}/expiring/soon?days=${days}`
    );
    return response.data;
  }

  // Utility methods

  /**
   * Formatar data para exibição
   */
  static formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("pt-BR");
  }

  /**
   * Formatar data e hora para exibição
   */
  static formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString("pt-BR");
  }

  /**
   * Verificar se autorização está expirada
   */
  static isExpired(validUntil: string): boolean {
    return new Date(validUntil) < new Date();
  }

  /**
   * Verificar se autorização vence em breve
   */
  static isExpiringSoon(validUntil: string, days: number = 7): boolean {
    const today = new Date();
    const expiryDate = new Date(validUntil);
    const diffTime = expiryDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= days && diffDays > 0;
  }

  /**
   * Calcular dias restantes até expiração
   */
  static getDaysUntilExpiry(validUntil: string): number {
    const today = new Date();
    const expiryDate = new Date(validUntil);
    const diffTime = expiryDate.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  /**
   * Obter label do status
   */
  static getStatusLabel(status: string): string {
    const labels = {
      active: "Ativa",
      expired: "Expirada",
      cancelled: "Cancelada",
      suspended: "Suspensa",
    };
    return labels[status as keyof typeof labels] || status;
  }

  /**
   * Obter label da urgência
   */
  static getUrgencyLabel(urgency: string): string {
    const labels = {
      URGENT: "Urgente",
      HIGH: "Alta",
      NORMAL: "Normal",
      LOW: "Baixa",
    };
    return labels[urgency as keyof typeof labels] || urgency;
  }

  /**
   * Obter cor do status
   */
  static getStatusColor(status: string): string {
    const colors = {
      active: "text-green-600 bg-green-100",
      expired: "text-gray-600 bg-gray-100",
      cancelled: "text-red-600 bg-red-100",
      suspended: "text-yellow-600 bg-yellow-100",
    };
    return colors[status as keyof typeof colors] || "text-gray-600 bg-gray-100";
  }

  /**
   * Obter cor da urgência
   */
  static getUrgencyColor(urgency: string): string {
    const colors = {
      URGENT: "text-red-600 bg-red-100",
      HIGH: "text-orange-600 bg-orange-100",
      NORMAL: "text-blue-600 bg-blue-100",
      LOW: "text-gray-600 bg-gray-100",
    };
    return (
      colors[urgency as keyof typeof colors] || "text-gray-600 bg-gray-100"
    );
  }
}

export const medicalAuthorizationsService = new MedicalAuthorizationsService();
