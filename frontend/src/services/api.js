import axios from "axios";
import axiosRetry from "axios-retry";
import { createAxiosConfig, RETRY_CONFIG } from "../config/http.ts";
import { createCacheInterceptor, httpCache } from "./httpCache.ts";
import secureSessionService from "./secureSessionService";

// 🔄 Configuração HTTP padronizada
const api = axios.create(createAxiosConfig("main"));

// 🔄 Retry mechanism configurado
axiosRetry(api, RETRY_CONFIG);

// 💾 Cache HTTP configurado para requests GET
createCacheInterceptor(api);

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    // 🔧 DEVELOPMENT: Skip auth header if bypassing authentication
    if (import.meta.env.DEV && !localStorage.getItem("access_token")) {
      console.info("🔧 Development mode: skipping auth header for", config.url);
    } else {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ✅ Mock interceptor removido para permitir requests reais ao backend

// Interceptor para tratar respostas e erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // ✅ Mock response handling removido

    // Log seguro para debug (sem dados sensíveis)
    const isDevelopment =
      import.meta.env?.DEV ||
      window.location.hostname === "localhost" ||
      window.location.port === "3000";

    if (isDevelopment) {
      console.error("API Error:", {
        status: error.response?.status,
        message: error.message,
        method: error.config?.method,
        url: error.config?.url?.replace(/\/\d+/g, "/:id"), // Mascarar IDs
      });
    }

    if (error.response?.status === 401) {
      // Token inválido ou expirado
      localStorage.removeItem("access_token");

      // Evitar loop infinito - só redirecionar se não estiver na página de login
      if (!window.location.pathname.includes("/login")) {
        // Salvar URL atual para redirecionar após login
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem("redirectAfterLogin", currentPath);

        // Usar window.location.replace para evitar problemas de histórico
        window.location.replace("/login");
      }
    }

    return Promise.reject(error);
  }
);

// Serviços da API
export const authService = {
  login: async (email, password) => {
    // Usar URLSearchParams para application/x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post("/api/v1/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post("/api/v1/auth/register", userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get("/api/v1/auth/me");
    return response.data;
  },

  // 🔒 Validação de token JWT
  validateToken: async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        return { valid: false, reason: "no_token" };
      }

      // Verificar se token não expirou (básico)
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const currentTime = Math.floor(Date.now() / 1000);

        if (payload.exp && payload.exp < currentTime) {
          return { valid: false, reason: "expired" };
        }
      } catch (e) {
        return { valid: false, reason: "invalid_format" };
      }

      // Validar com backend
      const response = await api.get("/api/v1/auth/me");
      return {
        valid: true,
        user: response.data,
        token,
      };
    } catch (error) {
      if (error.response?.status === 401) {
        return { valid: false, reason: "unauthorized" };
      }
      return { valid: false, reason: "network_error", error };
    }
  },

  // 🔒 Refresh token se necessário
  refreshToken: async () => {
    try {
      const response = await api.post("/api/v1/auth/refresh");
      if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
        return { success: true, token: response.data.access_token };
      }
      return { success: false, reason: "no_token_returned" };
    } catch (error) {
      return { success: false, reason: "refresh_failed", error };
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  },
};

export const healthService = {
  getHealthStatus: async () => {
    const response = await api.get("/api/v1/health");
    return response.data;
  },

  getDetailedHealth: async () => {
    const response = await api.get("/api/v1/health/detailed");
    return response.data;
  },
};

export const companiesService = {
  // Listar empresas com paginação e filtros
  getCompanies: async (params = {}) => {
    const response = await api.get("/api/v1/companies/", { params });
    return response.data;
  },

  // Contar total de empresas
  getCompaniesCount: async (params = {}) => {
    const response = await api.get("/api/v1/companies/count", { params });
    return response.data;
  },

  // Obter empresa por ID
  getCompany: async (id) => {
    const response = await api.get(`/api/v1/companies/${id}`);
    return response.data;
  },

  // Obter empresa por CNPJ
  getCompanyByCNPJ: async (cnpj) => {
    const response = await api.get(`/api/v1/companies/cnpj/${cnpj}`);
    return response.data;
  },

  // Criar nova empresa
  createCompany: async (companyData) => {
    const response = await api.post("/api/v1/companies/", companyData);
    // Invalidar cache de empresas após criação
    httpCache.invalidatePattern("/api/v1/companies");
    return response.data;
  },

  // Atualizar empresa
  updateCompany: async (id, companyData) => {
    const response = await api.put(`/api/v1/companies/${id}`, companyData);
    // Invalidar cache específico da empresa e listagem geral
    httpCache.invalidatePattern("/api/v1/companies");
    httpCache.delete(`/api/v1/companies/${id}`);
    return response.data;
  },

  // Deletar empresa (soft delete)
  deleteCompany: async (id) => {
    const response = await api.delete(`/api/v1/companies/${id}`);
    // Invalidar cache específico da empresa e listagem geral
    httpCache.invalidatePattern("/api/v1/companies");
    httpCache.delete(`/api/v1/companies/${id}`);
    return response.data;
  },

  // Obter apenas contatos da empresa
  getCompanyContacts: async (id) => {
    const response = await api.get(`/api/v1/companies/${id}/contacts`);
    return response.data;
  },
};

export const usersService = {
  // Listar usuários com paginação e filtros
  getUsers: async (params = {}) => {
    const response = await api.get("/api/v1/users/", { params });
    return response.data;
  },

  // Contar total de usuários
  getUsersCount: async (params = {}) => {
    const response = await api.get("/api/v1/users/count", { params });
    return response.data;
  },

  // Obter usuário por ID
  getUser: async (id) => {
    const response = await api.get(`/api/v1/users/${id}`);
    return response.data;
  },

  // Obter usuário por email
  getUserByEmail: async (email) => {
    const response = await api.get(`/api/v1/users/email/${email}`);
    return response.data;
  },

  // Criar novo usuário
  createUser: async (userData) => {
    const response = await api.post("/api/v1/users/", userData);
    // Invalidar cache de usuários após criação
    httpCache.invalidatePattern("/api/v1/users");
    return response.data;
  },

  // Atualizar usuário
  updateUser: async (id, userData) => {
    const response = await api.put(`/api/v1/users/${id}`, userData);
    // Invalidar cache específico do usuário e listagem geral
    httpCache.invalidatePattern("/api/v1/users");
    httpCache.delete(`/api/v1/users/${id}`);
    return response.data;
  },

  // Deletar usuário (soft delete) - DEPRECATED: usar toggleUserStatus
  deleteUser: async (id) => {
    const response = await api.delete(`/api/v1/users/${id}`);
    // Invalidar cache específico do usuário e listagem geral
    httpCache.invalidatePattern("/api/v1/users");
    httpCache.delete(`/api/v1/users/${id}`);
    return response.data;
  },

  // Ativar/Inativar usuário
  toggleUserStatus: async (id, isActive) => {
    const response = await api.patch(`/api/v1/users/${id}/status`, { 
      is_active: isActive 
    });
    // Invalidar cache específico do usuário e listagem geral
    httpCache.invalidatePattern("/api/v1/users");
    httpCache.delete(`/api/v1/users/${id}`);
    return response.data;
  },

  // Alterar senha do usuário
  changePassword: async (id, passwordData) => {
    const response = await api.patch(`/api/v1/users/${id}/password`, passwordData);
    return response.data;
  },

  // Obter roles do usuário
  getUserRoles: async (id) => {
    const response = await api.get(`/api/v1/users/${id}/roles`);
    return response.data;
  },

  // Atualizar roles do usuário
  updateUserRoles: async (id, roles) => {
    const response = await api.put(`/api/v1/users/${id}/roles`, { roles });
    httpCache.invalidatePattern("/api/v1/users");
    return response.data;
  },
};

export const establishmentsService = {
  // Listar estabelecimentos com paginação e filtros
  getEstablishments: async (params = {}) => {
    const response = await api.get("/api/v1/establishments/", { params });
    return response.data;
  },

  // Obter estabelecimento por ID
  getEstablishment: async (id) => {
    const response = await api.get(`/api/v1/establishments/${id}`);
    return response.data;
  },

  // Listar estabelecimentos por empresa
  getEstablishmentsByCompany: async (companyId, params = {}) => {
    const response = await api.get(`/api/v1/establishments/company/${companyId}`, { params });
    return response.data;
  },

  // Criar estabelecimento
  createEstablishment: async (data) => {
    const response = await api.post("/api/v1/establishments/", data);
    httpCache.invalidatePattern("/api/v1/establishments");
    return response.data;
  },

  // Atualizar estabelecimento
  updateEstablishment: async (id, data) => {
    const response = await api.put(`/api/v1/establishments/${id}`, data);
    httpCache.invalidatePattern("/api/v1/establishments");
    return response.data;
  },

  // Alterar status do estabelecimento (ativar/desativar)
  toggleEstablishmentStatus: async (id, isActive) => {
    const response = await api.patch(`/api/v1/establishments/${id}/status`, { 
      is_active: isActive 
    });
    httpCache.invalidatePattern("/api/v1/establishments");
    return response.data;
  },

  // Excluir estabelecimento (soft delete)
  deleteEstablishment: async (id) => {
    const response = await api.delete(`/api/v1/establishments/${id}`);
    httpCache.invalidatePattern("/api/v1/establishments");
    return response.data;
  },

  // Reordenar estabelecimentos
  reorderEstablishments: async (companyId, establishmentOrders) => {
    const response = await api.post("/api/v1/establishments/reorder", {
      company_id: companyId,
      establishment_orders: establishmentOrders
    });
    httpCache.invalidatePattern("/api/v1/establishments");
    return response.data;
  },

  // Validar criação de estabelecimento
  validateEstablishmentCreation: async (companyId, code, isPrincipal = false) => {
    const response = await api.post("/api/v1/establishments/validate", null, {
      params: {
        company_id: companyId,
        code: code,
        is_principal: isPrincipal
      }
    });
    return response.data;
  },

  // Contar estabelecimentos (usado para paginação)
  countEstablishments: async (params = {}) => {
    const establishmentsResponse = await api.get("/api/v1/establishments/", { 
      params: { ...params, page: 1, size: 1 } 
    });
    return { total: establishmentsResponse.data.total || 0 };
  },
};

export { api, secureSessionService };
export default api;
