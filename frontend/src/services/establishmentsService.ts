/**
 * Service para gerenciamento de estabelecimentos
 */

import { api, httpCache } from "./api.js";

export interface Establishment {
  id: number;
  code: string;
  type: "matriz" | "filial";
  name: string;
  cnpj?: string;
  is_active: boolean;
  company_id: number;
  created_at: string;
  updated_at: string;
}

export interface EstablishmentCreateData {
  code: string;
  type: "matriz" | "filial";
  name: string;
  cnpj?: string;
  company_id: number;
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
    const response = await api.post(`${this.baseUrl}/`, data);

    // Invalidar cache após criação
    httpCache.invalidatePattern(`${this.baseUrl}/`);

    return response.data;
  }

  async updateEstablishment(
    id: number,
    data: EstablishmentUpdateData
  ): Promise<Establishment> {
    const response = await api.put(`${this.baseUrl}/${id}`, data);

    // Invalidar cache após atualização
    httpCache.invalidatePattern(`${this.baseUrl}/`);

    return response.data;
  }

  async toggleEstablishmentStatus(
    id: number,
    isActive: boolean
  ): Promise<Establishment> {
    const response = await api.patch(`${this.baseUrl}/${id}/toggle-status`, {
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
