/**
 * Contracts Service - API calls para contratos home care
 * Implementação TypeScript seguindo padrão dos outros serviços
 */

import axios from "axios";
import axiosRetry from "axios-retry";
import { createAxiosConfig, RETRY_CONFIG } from "../config/http.ts";
import { createCacheInterceptor, httpCache } from "./httpCache.ts";
import type {
  ContractLife,
  ContractLifeCreateDTO,
  ContractLifeUpdateDTO,
  ContractLifeMutationResponse,
  ContractLifeStats,
  ContractLifeHistory,
} from "../types/contract-lives.types";

// ===============================
// TYPES
// ===============================

export interface ServicesCatalog {
  id: number;
  service_code: string;
  service_name: string;
  service_category: string;
  service_type: string;
  requires_prescription: boolean;
  home_visit_required: boolean;
  default_unit_value?: number;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Contract {
  id: number;
  client_id: number;
  contract_number: string;
  contract_type: "INDIVIDUAL" | "CORPORATIVO" | "EMPRESARIAL";
  plan_name: string;
  monthly_value: number;
  lives_contracted: number;
  actual_lives_count?: number; // Contagem real de vidas ativas
  lives_minimum?: number;
  lives_maximum?: number;
  allows_substitution: boolean;
  control_period?: "DAILY" | "WEEKLY" | "MONTHLY" | "QUARTERLY";
  start_date: string;
  end_date?: string;
  service_address_type?: "PATIENT" | "CLINIC";
  service_addresses?: any;
  status: "active" | "inactive" | "suspended" | "cancelled" | "expired";
  created_at: string;
  updated_at: string;
  created_by?: number;
  updated_by?: number;
  notes?: string; // Campo para observações do contrato
}

export interface ContractCreate {
  client_id: number;
  contract_type?: "INDIVIDUAL" | "CORPORATIVO" | "EMPRESARIAL";
  plan_name: string;
  monthly_value: number;
  lives_contracted?: number;
  lives_minimum?: number;
  lives_maximum?: number;
  allows_substitution?: boolean;
  control_period?: "DAILY" | "WEEKLY" | "MONTHLY" | "QUARTERLY";
  start_date: string;
  end_date?: string;
  service_address_type?: "PATIENT" | "CLINIC";
  service_addresses?: any;
  status?: "active" | "inactive" | "suspended" | "cancelled" | "expired";
  notes?: string; // Campo para observações do contrato
}

export interface ContractUpdate {
  contract_type?: "INDIVIDUAL" | "CORPORATIVO" | "EMPRESARIAL";
  plan_name?: string;
  monthly_value?: number;
  lives_contracted?: number;
  lives_minimum?: number;
  lives_maximum?: number;
  allows_substitution?: boolean;
  control_period?: "DAILY" | "WEEKLY" | "MONTHLY" | "QUARTERLY";
  end_date?: string;
  service_address_type?: "PATIENT" | "CLINIC";
  service_addresses?: any;
  status?: "active" | "inactive" | "suspended" | "cancelled" | "expired";
  notes?: string; // Campo para observações do contrato
}

export interface ContractListResponse {
  contracts: Contract[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ServicesListResponse {
  services: ServicesCatalog[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ContractListParams {
  client_id?: number;
  status?: string;
  contract_type?: string;
  page?: number;
  size?: number;
}

export interface ServicesListParams {
  category?: string;
  service_type?: string;
  page?: number;
  size?: number;
}

// ===============================
// API SETUP
// ===============================

const api = axios.create(createAxiosConfig("main"));
axiosRetry(api, RETRY_CONFIG);
createCacheInterceptor(api);

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const currentTime = Math.floor(Date.now() / 1000);

        if (payload.exp && payload.exp < currentTime) {
          console.warn(
            "⚠️ Token expirado detectado, removendo do localStorage"
          );
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");

          if (!window.location.pathname.includes("/login")) {
            const currentPath =
              window.location.pathname + window.location.search;
            sessionStorage.setItem("redirectAfterLogin", currentPath);
            window.location.replace("/login");
          }
          return Promise.reject(new Error("Token expirado"));
        }

        config.headers.Authorization = `Bearer ${token}`;
      } catch (error) {
        console.error("❌ Erro ao processar token:", error);
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para tratamento de respostas
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");

      if (!window.location.pathname.includes("/login")) {
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem("redirectAfterLogin", currentPath);
        window.location.replace("/login");
      }
    }
    return Promise.reject(error);
  }
);

// ===============================
// CONTRACT OPERATIONS
// ===============================

class ContractsService {
  /**
   * Listar contratos com filtros e paginação
   */
  async listContracts(
    params: ContractListParams = {}
  ): Promise<ContractListResponse> {
    const queryParams = new URLSearchParams();

    if (params.client_id)
      queryParams.append("client_id", params.client_id.toString());
    if (params.status) queryParams.append("status", params.status);
    if (params.contract_type)
      queryParams.append("contract_type", params.contract_type);
    if (params.page) queryParams.append("page", params.page.toString());
    if (params.size) queryParams.append("size", params.size.toString());

    const response = await api.get(
      `/api/v1/contracts/?${queryParams.toString()}`
    );
    return response.data;
  }

  /**
   * Buscar contrato por ID
   */
  async getContract(contractId: number): Promise<Contract> {
    const response = await api.get(`/api/v1/contracts/${contractId}`);
    console.log(
      "🔍 DEBUG - Resposta completa da API getContract:",
      response.data
    );
    return response.data;
  }

  /**
   * Alias para getContract (compatibilidade)
   */
  async getById(contractId: number): Promise<Contract> {
    return this.getContract(contractId);
  }

  /**
   * Criar novo contrato
   */
  async createContract(contractData: ContractCreate): Promise<Contract> {
    const response = await api.post("/api/v1/contracts/", contractData);
    return response.data;
  }

  /**
   * Atualizar contrato
   */
  async updateContract(
    contractId: number,
    contractData: ContractUpdate
  ): Promise<Contract> {
    const response = await api.put(
      `/api/v1/contracts/${contractId}`,
      contractData
    );
    return response.data;
  }

  /**
   * Deletar contrato (soft delete)
   */
  async deleteContract(contractId: number): Promise<void> {
    await api.delete(`/api/v1/contracts/${contractId}`);
  }

  /**
   * Alias para deleteContract (compatibilidade)
   */
  async delete(contractId: number): Promise<void> {
    return this.deleteContract(contractId);
  }

  /**
   * Contar contratos com filtros
   */
  async countContracts(
    params: ContractListParams = {}
  ): Promise<{ count: number }> {
    const queryParams = new URLSearchParams();

    if (params.client_id)
      queryParams.append("client_id", params.client_id.toString());
    if (params.status) queryParams.append("status", params.status);
    if (params.contract_type)
      queryParams.append("contract_type", params.contract_type);

    const response = await api.get(
      `/api/v1/contracts/count/?${queryParams.toString()}`
    );
    return response.data;
  }

  // ===============================
  // SERVICES CATALOG OPERATIONS
  // ===============================

  /**
   * Listar catálogo de serviços
   */
  async listServices(
    params: ServicesListParams = {}
  ): Promise<ServicesListResponse> {
    const queryParams = new URLSearchParams();

    if (params.category) queryParams.append("category", params.category);
    if (params.service_type)
      queryParams.append("service_type", params.service_type);
    if (params.page) queryParams.append("page", params.page.toString());
    if (params.size) queryParams.append("size", params.size.toString());

    const response = await api.get(
      `/api/v1/services/?${queryParams.toString()}`
    );
    return response.data;
  }

  /**
   * Buscar serviço por ID
   */
  async getService(serviceId: number): Promise<ServicesCatalog> {
    const response = await api.get(`/api/v1/services/${serviceId}`);
    return response.data;
  }

  // ===============================
  // UTILITY METHODS
  // ===============================

  /**
   * Limpar cache de contratos
   */
  clearContractsCache(): void {
    httpCache.invalidatePattern("/api/v1/contracts");
    httpCache.invalidatePattern("/api/v1/services");
  }

  /**
   * Obter opções de tipos de contrato
   */
  getContractTypes(): Array<{ value: string; label: string }> {
    return [
      { value: "INDIVIDUAL", label: "Individual" },
      { value: "CORPORATIVO", label: "Corporativo" },
      { value: "EMPRESARIAL", label: "Empresarial" },
    ];
  }

  /**
   * Obter opções de status de contrato
   */
  getContractStatuses(): Array<{ value: string; label: string }> {
    return [
      { value: "active", label: "Ativo" },
      { value: "inactive", label: "Inativo" },
      { value: "suspended", label: "Suspenso" },
      { value: "terminated", label: "Terminado" },
      { value: "draft", label: "Rascunho" },
    ];
  }

  /**
   * Obter opções de período de controle
   */
  getControlPeriods(): Array<{ value: string; label: string }> {
    return [
      { value: "DAILY", label: "Diário" },
      { value: "WEEKLY", label: "Semanal" },
      { value: "MONTHLY", label: "Mensal" },
      { value: "QUARTERLY", label: "Trimestral" },
    ];
  }

  /**
   * Formatar valor monetário
   */
  formatCurrency(value: number): string {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  }

  /**
   * Formatar data
   */
  formatDate(date: string): string {
    return new Intl.DateTimeFormat("pt-BR").format(new Date(date));
  }

  /**
   * Obter label do tipo de contrato
   */
  getContractTypeLabel(type: string): string {
    const types = this.getContractTypes();
    return types.find((t) => t.value === type)?.label || type;
  }

  /**
   * Obter label do status
   */
  getStatusLabel(status: string): string {
    const statuses = this.getContractStatuses();
    return statuses.find((s) => s.value === status)?.label || status;
  }

  // ===============================
  // CONTRACT LIVES OPERATIONS
  // ===============================

  /**
   * Listar vidas de um contrato
   */
  async listContractLives(contractId: number): Promise<ContractLife[]> {
    const response = await api.get<ContractLife[]>(
      `/api/v1/contracts/${contractId}/lives`
    );
    return response.data;
  }

  /**
   * Adicionar vida ao contrato
   *
   * @param contractId - ID do contrato
   * @param lifeData - Dados da vida a ser criada
   * @returns Response com ID da vida criada
   */
  async addContractLife(
    contractId: number,
    lifeData: ContractLifeCreateDTO
  ): Promise<ContractLifeMutationResponse> {
    const response = await api.post<ContractLifeMutationResponse>(
      `/api/v1/contracts/${contractId}/lives`,
      lifeData
    );
    return response.data;
  }

  /**
   * Atualizar vida do contrato
   *
   * @param contractId - ID do contrato
   * @param lifeId - ID da vida
   * @param lifeData - Dados a serem atualizados (apenas campos fornecidos)
   * @returns Response com confirmação
   */
  async updateContractLife(
    contractId: number,
    lifeId: number,
    lifeData: ContractLifeUpdateDTO
  ): Promise<ContractLifeMutationResponse> {
    const response = await api.put<ContractLifeMutationResponse>(
      `/api/v1/contracts/${contractId}/lives/${lifeId}`,
      lifeData
    );
    return response.data;
  }

  /**
   * Remover vida do contrato (soft delete)
   *
   * Define status='cancelled' e end_date=hoje
   * NÃO deleta o registro fisicamente
   *
   * @param contractId - ID do contrato
   * @param lifeId - ID da vida
   */
  async removeContractLife(contractId: number, lifeId: number): Promise<void> {
    await api.delete(`/api/v1/contracts/${contractId}/lives/${lifeId}`);
  }

  /**
   * Buscar estatísticas de vidas de um contrato
   *
   * @param contractId - ID do contrato
   * @returns Estatísticas consolidadas
   */
  async getContractLivesStats(contractId: number): Promise<ContractLifeStats> {
    const response = await api.get<ContractLifeStats>(
      `/api/v1/contracts/${contractId}/lives/stats`
    );
    return response.data;
  }

  /**
   * Buscar histórico de uma vida (auditoria)
   *
   * @param contractId - ID do contrato
   * @param lifeId - ID da vida
   * @returns Histórico completo de eventos
   */
  async getContractLifeHistory(
    contractId: number,
    lifeId: number
  ): Promise<ContractLifeHistory> {
    const response = await api.get<ContractLifeHistory>(
      `/api/v1/contracts/${contractId}/lives/${lifeId}/history`
    );
    return response.data;
  }
}

// Instância singleton
export const contractsService = new ContractsService();

// Export para compatibilidade com CommonJS
export default contractsService;
