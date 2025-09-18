/**
 * Clients Service - API calls tipadas para clientes
 * Implementação TypeScript com type safety completo
 */

import axios from "axios";
import axiosRetry from "axios-retry";
import { createAxiosConfig, RETRY_CONFIG } from "../config/http.ts";
import { createCacheInterceptor, httpCache } from "./httpCache.ts";
import {
  ClientDetailed,
  ClientCreate,
  ClientUpdate,
  ClientListResponse,
  ClientValidationResponse,
  PaginatedResponse,
  PersonType,
  ClientStatus,
} from "../types";

// ===============================
// API SETUP (seguindo padrão do api.js)
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
      } catch (e) {
        console.warn(
          "⚠️ Token com formato inválido, removendo do localStorage"
        );
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");

        if (!window.location.pathname.includes("/login")) {
          const currentPath = window.location.pathname + window.location.search;
          sessionStorage.setItem("redirectAfterLogin", currentPath);
          window.location.replace("/login");
        }
        return Promise.reject(new Error("Token inválido"));
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ===============================
// CLIENTS API SERVICE
// ===============================

class ClientsService {
  private readonly basePath = "/api/v1/clients";

  /**
   * Listar clientes com filtros e paginação
   */
  async getAll(params?: {
    establishment_id?: number;
    status?: ClientStatus;
    person_type?: PersonType;
    search?: string;
    page?: number;
    size?: number;
  }): Promise<ClientListResponse> {
    const queryParams = new URLSearchParams();

    if (params?.establishment_id)
      queryParams.append(
        "establishment_id",
        params.establishment_id.toString()
      );
    if (params?.status) queryParams.append("status", params.status);
    if (params?.person_type)
      queryParams.append("person_type", params.person_type);
    if (params?.search) queryParams.append("search", params.search);
    if (params?.page) queryParams.append("page", params.page.toString());
    if (params?.size) queryParams.append("size", params.size.toString());

    const url = `${this.basePath}/?${queryParams.toString()}`;
    const response = await api.get<ClientListResponse>(url);
    return response.data;
  }

  /**
   * Obter cliente por ID
   */
  async getById(clientId: number): Promise<ClientDetailed> {
    const url = `${this.basePath}/${clientId}`;
    const response = await api.get<ClientDetailed>(url);
    return response.data;
  }

  /**
   * Criar novo cliente
   */
  async create(clientData: ClientCreate): Promise<ClientDetailed> {
    const url = `${this.basePath}/create`;
    const response = await api.post<ClientDetailed>(url, clientData);

    // Invalidar cache relacionado
    httpCache.invalidatePattern("/api/v1/clients");

    return response.data;
  }

  /**
   * Atualizar cliente existente
   */
  async update(
    clientId: number,
    clientData: ClientUpdate
  ): Promise<ClientDetailed> {
    const url = `${this.basePath}/${clientId}`;
    const response = await api.put<ClientDetailed>(url, clientData);

    // Invalidar cache
    httpCache.invalidatePattern("/api/v1/clients");
    httpCache.delete(url);

    return response.data;
  }

  /**
   * Alterar status do cliente
   */
  async updateStatus(
    clientId: number,
    status: ClientStatus
  ): Promise<ClientDetailed> {
    const url = `${this.basePath}/${clientId}/status?status=${status}`;
    const response = await api.put<ClientDetailed>(url, {});

    // Invalidar cache
    httpCache.invalidatePattern("/api/v1/clients");

    return response.data;
  }

  /**
   * Excluir cliente (soft delete)
   */
  async delete(clientId: number): Promise<void> {
    const url = `${this.basePath}/${clientId}`;
    await api.delete(url);

    // Invalidar cache
    httpCache.invalidatePattern("/api/v1/clients");
  }

  /**
   * Validar criação de cliente
   */
  async validateCreation(params: {
    establishment_id: number;
    tax_id: string;
    client_code?: string;
  }): Promise<ClientValidationResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append("establishment_id", params.establishment_id.toString());
    queryParams.append("tax_id", params.tax_id);
    if (params.client_code)
      queryParams.append("client_code", params.client_code);

    const url = `${this.basePath}/validate?${queryParams.toString()}`;
    const response = await api.post<ClientValidationResponse>(url, {});
    return response.data;
  }

  /**
   * Listar clientes por estabelecimento
   */
  async getByEstablishment(
    establishmentId: number,
    status?: ClientStatus
  ): Promise<ClientDetailed[]> {
    const queryParams = new URLSearchParams();
    queryParams.append("establishment_id", establishmentId.toString());
    if (status) queryParams.append("status", status);
    queryParams.append("page", "1");
    queryParams.append("size", "100");

    const url = `${this.basePath}/?${queryParams.toString()}`;
    const response = await api.get<ClientListResponse>(url);
    return response.data.clients;
  }

  /**
   * Buscar clientes por CPF/CNPJ
   * Retorna todos os clientes registrados com este documento fiscal
   */
  async getByTaxId(taxId: string): Promise<ClientDetailed[]> {
    const cleanTaxId = taxId.replace(/\D/g, "");
    const url = `${this.basePath}/search/by-tax-id?tax_id=${cleanTaxId}`;
    const response = await api.get<ClientDetailed[]>(url);
    return response.data;
  }

  /**
   * Verificar se cliente já existe no estabelecimento específico
   * Implementa a lógica dos 4 cenários de verificação
   */
  async checkExistingInEstablishment(
    establishmentId: number,
    taxId: string
  ): Promise<{
    exists_in_establishment: boolean;
    existing_client: ClientDetailed | null;
    person_exists_globally: boolean;
    existing_person: any | null;
    person_type: "PF" | "PJ";
    other_establishments: Array<{
      establishment_id: number;
      establishment_name: string;
      client_code: string;
      status: string;
    }>;
  }> {
    const cleanTaxId = taxId.replace(/\D/g, "");
    const url = `${this.basePath}/check-existing-in-establishment?establishment_id=${establishmentId}&tax_id=${cleanTaxId}`;

    try {
      const response = await api.get(url);
      console.log("🔍 Duplication check successful (200):", response.data);
      return response.data;
    } catch (error: any) {
      console.log(
        "🔍 Duplication check error response:",
        error.response?.status,
        error.response?.data
      );

      // Handle 422 errors which may contain valid duplication data
      if (error.response?.status === 422) {
        const responseData = error.response.data;
        console.log("🔍 Checking 422 response data structure:", responseData);

        // Check if it has the expected duplication data structure
        if (
          responseData &&
          typeof responseData.exists_in_establishment === "boolean" &&
          typeof responseData.person_exists_globally === "boolean" &&
          typeof responseData.person_type === "string"
        ) {
          console.log(
            "🔍 Valid duplication data found in 422 response:",
            responseData
          );
          return responseData;
        }

        // Check if it's nested in a detail object
        if (
          responseData?.detail &&
          typeof responseData.detail.exists_in_establishment === "boolean"
        ) {
          console.log(
            "🔍 Valid duplication data found in 422 response detail:",
            responseData.detail
          );
          return responseData.detail;
        }
      }

      console.log(
        "🔍 No valid duplication data in error response, re-throwing error"
      );
      throw error;
    }
  }

  /**
   * Obter estatísticas de clientes por estabelecimento
   */
  async getStats(establishmentId: number): Promise<{
    total: number;
    status_active: number;
    status_inactive: number;
    status_on_hold: number;
    status_archived: number;
    person_type_PF: number;
    person_type_PJ: number;
  }> {
    const url = `${this.basePath}/stats/by-establishment/${establishmentId}`;
    const response = await api.get<any>(url);
    return response.data;
  }

  // ===============================
  // UTILITY METHODS
  // ===============================

  /**
   * Formatar CPF/CNPJ para exibição
   */
  formatTaxId(taxId: string): string {
    const clean = taxId.replace(/\D/g, "");

    if (clean.length === 11) {
      // CPF: 000.000.000-00
      return clean.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    } else if (clean.length === 14) {
      // CNPJ: 00.000.000/0000-00
      return clean.replace(
        /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
        "$1.$2.$3/$4-$5"
      );
    }

    return taxId;
  }

  /**
   * Validar formato de CPF/CNPJ
   */
  isValidTaxId(taxId: string): boolean {
    const clean = taxId.replace(/\D/g, "");
    return clean.length === 11 || clean.length === 14;
  }

  /**
   * Limpar CPF/CNPJ (apenas números)
   */
  cleanTaxId(taxId: string): string {
    return taxId.replace(/\D/g, "");
  }

  /**
   * Determinar tipo de pessoa baseado no CPF/CNPJ
   */
  getPersonTypeFromTaxId(taxId: string): PersonType {
    const clean = this.cleanTaxId(taxId);
    return clean.length === 11 ? "PF" : "PJ";
  }

  /**
   * Obter label do status do cliente
   */
  getStatusLabel(status: ClientStatus): string {
    const labels = {
      active: "Ativo",
      inactive: "Inativo",
      on_hold: "Em Espera",
      archived: "Arquivado",
    };

    return labels[status] || status;
  }

  /**
   * Obter cor do status do cliente
   */
  getStatusColor(status: ClientStatus): string {
    const colors = {
      active: "green",
      inactive: "gray",
      on_hold: "yellow",
      archived: "red",
    };

    return colors[status] || "gray";
  }
}

// Instância singleton
export const clientsService = new ClientsService();
export default clientsService;
