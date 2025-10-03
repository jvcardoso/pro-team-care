/**
 * Service para gerenciamento de estabelecimentos
 */

import { api, httpCache } from "./api.js";

export interface Establishment {
  id: number;
  code: string;
  type: string;
  category: string;
  is_active: boolean;
  is_principal: boolean;
  company_id: number;
  display_order: number;
  settings: Record<string, any>;
  metadata: Record<string, any>;
  operating_hours: Record<string, any>;
  service_areas: Record<string, any>;
  created_at: string;
  updated_at: string;
  person?: {
    id: number;
    name: string;
    tax_id: string;
    person_type: string;
    status: string;
    description?: string;
  };
  phones?: Array<{
    id?: number;
    country_code: string;
    number: string;
    type: string;
    is_principal: boolean;
    is_whatsapp: boolean;
  }>;
  emails?: Array<{
    id?: number;
    email_address: string;
    type: string;
    is_principal: boolean;
  }>;
  addresses?: Array<{
    id?: number;
    street: string;
    number: string;
    details?: string;
    neighborhood: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
    type: string;
    is_principal: boolean;
  }>;
}

export interface EstablishmentCreateData {
  company_id: number;
  code: string;
  type: string;
  category: string;
  is_active: boolean;
  is_principal: boolean;
  settings?: Record<string, any>;
  metadata?: Record<string, any>;
  operating_hours?: Record<string, any>;
  service_areas?: Record<string, any>;
  person: {
    name: string;
    tax_id: string;
    person_type: string;
    status: string;
    description?: string;
  };
  existing_person_id?: number; // Para reutilizar pessoa existente
}

export interface EstablishmentUpdateData
  extends Partial<EstablishmentCreateData> {
  is_active?: boolean;
}

export interface EstablishmentsResponse {
  establishments: Establishment[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface EstablishmentsParams {
  page?: number;
  size?: number;
  search?: string;
  company_id?: number;
  type?: "matriz" | "filial";
  is_active?: boolean;
}

class EstablishmentsService {
  private readonly baseUrl = "/api/v1/establishments";

  async getEstablishments(
    params?: EstablishmentsParams
  ): Promise<EstablishmentsResponse> {
    const response = await api.get(`${this.baseUrl}/`, { params });
    return response.data;
  }

  async getEstablishment(id: number): Promise<Establishment> {
    const response = await api.get(`${this.baseUrl}/${id}`);
    return response.data;
  }

  async getEstablishmentsByCompany(
    companyId: number,
    params?: Omit<EstablishmentsParams, "company_id">
  ): Promise<EstablishmentsResponse> {
    const response = await api.get(`${this.baseUrl}/`, {
      params: { ...params, company_id: companyId },
    });
    return response.data;
  }

  async createEstablishment(
    data: EstablishmentCreateData
  ): Promise<Establishment> {
    console.log("🚀 Enviando dados para criação de estabelecimento:", data);

    const response = await api.post(`${this.baseUrl}/`, data);

    // Invalidar cache após criação
    httpCache.invalidatePattern(`${this.baseUrl}/`);

    console.log("✅ Estabelecimento criado com sucesso:", response.data);
    return response.data;
  }

  async updateEstablishment(
    id: number,
    data: EstablishmentUpdateData
  ): Promise<Establishment> {
    console.log(
      `🚀 Enviando dados para atualização do estabelecimento ${id}:`,
      data
    );

    const response = await api.put(`${this.baseUrl}/${id}`, data);

    // Invalidar cache após atualização
    httpCache.invalidatePattern(`${this.baseUrl}/`);

    console.log("✅ Estabelecimento atualizado com sucesso:", response.data);
    return response.data;
  }

  async toggleEstablishmentStatus(
    id: number,
    isActive: boolean
  ): Promise<Establishment> {
    const response = await api.patch(`${this.baseUrl}/${id}/status`, {
      is_active: isActive,
    });

    // Invalidar cache após mudança de status
    httpCache.invalidatePattern(`${this.baseUrl}/`);

    return response.data;
  }

  async deleteEstablishment(id: number): Promise<void> {
    await api.delete(`${this.baseUrl}/${id}`);

    // Invalidar cache após exclusão
    httpCache.invalidatePattern(`${this.baseUrl}/`);
  }

  async reorderEstablishments(establishmentIds: number[]): Promise<void> {
    await api.post(`${this.baseUrl}/reorder`, {
      establishment_ids: establishmentIds,
    });

    // Invalidar cache após reordenação
    httpCache.invalidatePattern(`${this.baseUrl}/`);
  }

  async validateEstablishmentCreation(
    data: EstablishmentCreateData
  ): Promise<{ valid: boolean; message?: string }> {
    try {
      const response = await api.post(`${this.baseUrl}/validate`, data);
      return response.data;
    } catch (error: any) {
      return {
        valid: false,
        message: error.response?.data?.message || "Erro na validação",
      };
    }
  }

  async countEstablishments(
    params?: Omit<EstablishmentsParams, "page" | "size">
  ): Promise<number> {
    const response = await api.get(`${this.baseUrl}/count`, { params });
    return response.data.count || 0;
  }
}

export const establishmentsService = new EstablishmentsService();
export default establishmentsService;
