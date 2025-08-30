import axios from 'axios';

// Configuração base da API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.11.62:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas e erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido ou expirado
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Serviços da API
export const authService = {
  login: async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/v1/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  }
};

export const healthService = {
  getHealthStatus: async () => {
    const response = await api.get('/api/v1/health');
    return response.data;
  },

  getDetailedHealth: async () => {
    const response = await api.get('/api/v1/health/detailed');
    return response.data;
  }
};

export const companiesService = {
  // Listar empresas com paginação e filtros
  getCompanies: async (params = {}) => {
    const response = await api.get('/api/v1/companies/', { params });
    return response.data;
  },

  // Contar total de empresas
  getCompaniesCount: async (params = {}) => {
    const response = await api.get('/api/v1/companies/count', { params });
    return response.data;
  },

  // Obter empresa por ID
  getCompany: async (id) => {
    const response = await api.get(`/api/v1/companies/${id}`);
    return response.data;
  },

  // Criar nova empresa
  createCompany: async (companyData) => {
    const response = await api.post('/api/v1/companies/', companyData);
    return response.data;
  },

  // Atualizar empresa
  updateCompany: async (id, companyData) => {
    const response = await api.put(`/api/v1/companies/${id}`, companyData);
    return response.data;
  },

  // Deletar empresa (soft delete)
  deleteCompany: async (id) => {
    const response = await api.delete(`/api/v1/companies/${id}`);
    return response.data;
  },

  // Obter apenas contatos da empresa
  getCompanyContacts: async (id) => {
    const response = await api.get(`/api/v1/companies/${id}/contacts`);
    return response.data;
  }
};

export default api;