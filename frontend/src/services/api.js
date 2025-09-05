import axios from "axios";
import axiosRetry from "axios-retry";
import { createAxiosConfig, RETRY_CONFIG } from "../config/http.ts";
import { createCacheInterceptor, httpCache } from "./httpCache.ts";

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

// 🔧 DEVELOPMENT: Mock interceptor for menus API
api.interceptors.request.use(
  (config) => {
    // Mock menus response for development
    if (import.meta.env.DEV && config.url?.includes('/api/v1/menus/user/')) {
      console.info("🔧 Development mode: mocking menus API response");

      // Simulate network delay
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ...config,
            mockResponse: {
              data: {
                menus: [
                  {
                    id: 1,
                    parent_id: null,
                    name: "Dashboard",
                    slug: "dashboard",
                    url: "/admin/dashboard",
                    icon: "LayoutDashboard",
                    sort_order: 1,
                    is_visible: true,
                    permission_name: "view_dashboard",
                    children: []
                  },
                  {
                    id: 2,
                    parent_id: null,
                    name: "Pacientes",
                    slug: "pacientes",
                    url: "/admin/pacientes",
                    icon: "Users",
                    sort_order: 2,
                    is_visible: true,
                    permission_name: "view_patients",
                    children: []
                  },
                  {
                    id: 3,
                    parent_id: null,
                    name: "Profissionais",
                    slug: "profissionais",
                    url: "/admin/profissionais",
                    icon: "UserCheck",
                    sort_order: 3,
                    is_visible: true,
                    permission_name: "view_professionals",
                    children: []
                  },
                  {
                    id: 4,
                    parent_id: null,
                    name: "Consultas",
                    slug: "consultas",
                    url: "/admin/consultas",
                    icon: "Calendar",
                    sort_order: 4,
                    is_visible: true,
                    permission_name: "view_appointments",
                    children: []
                  },
                  {
                    id: 5,
                    parent_id: null,
                    name: "Empresas",
                    slug: "empresas",
                    url: "/admin/empresas",
                    icon: "Building",
                    sort_order: 5,
                    is_visible: true,
                    permission_name: "view_companies",
                    children: []
                  },
                  {
                    id: 6,
                    parent_id: null,
                    name: "Sistema",
                    slug: "sistema",
                    url: null,
                    icon: "Settings",
                    sort_order: 6,
                    is_visible: true,
                    permission_name: "system_admin",
                    children: [
                      {
                        id: 7,
                        parent_id: 6,
                        name: "Menus",
                        slug: "menus",
                        url: "/admin/menus",
                        icon: "Menu",
                        sort_order: 1,
                        is_visible: true,
                        permission_name: "manage_menus",
                        children: []
                      }
                    ]
                  }
                ]
              },
              status: 200,
              statusText: "OK",
              headers: {},
              config
            }
          });
        }, 500); // 500ms delay
      });
    }

    return config;
  }
);

// Interceptor para tratar respostas e erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle mock responses
    if (error.config?.mockResponse) {
      return Promise.resolve(error.config.mockResponse);
    }

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

export { api };
export default api;
