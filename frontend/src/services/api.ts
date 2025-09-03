/**
 * API Service - Configuração tipada do Axios
 * Migrado para TypeScript com type safety
 */

import axios, {
  AxiosInstance,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";
import { ApiResponse, ApiError, RequestOptions } from "@/types";

// ===============================
// API CONFIGURATION
// ===============================

// Usar proxy do Vite em desenvolvimento, URL absoluta em produção
const API_BASE_URL = import.meta.env.DEV
  ? ""
  : import.meta.env.VITE_API_URL || "http://192.168.11.83:8000";

/**
 * Instância principal do Axios com configuração padrão
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ===============================
// REQUEST INTERCEPTOR
// ===============================

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// ===============================
// RESPONSE INTERCEPTOR
// ===============================

api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }

    // Handle other HTTP errors
    const apiError: ApiError = {
      detail:
        error.response?.data?.detail || error.message || "Erro desconhecido",
      type: error.response?.data?.type || "api_error",
      status_code: error.response?.status || 500,
    };

    return Promise.reject(apiError);
  }
);

// ===============================
// API METHODS WITH TYPES
// ===============================

/**
 * GET request tipado
 */
export const get = async <T>(
  url: string,
  options?: RequestOptions
): Promise<T> => {
  const response: AxiosResponse<T> = await api.get(url, options);
  return response.data;
};

/**
 * POST request tipado
 */
export const post = async <T, D = any>(
  url: string,
  data?: D,
  options?: RequestOptions
): Promise<T> => {
  const response: AxiosResponse<T> = await api.post(url, data, options);
  return response.data;
};

/**
 * PUT request tipado
 */
export const put = async <T, D = any>(
  url: string,
  data?: D,
  options?: RequestOptions
): Promise<T> => {
  const response: AxiosResponse<T> = await api.put(url, data, options);
  return response.data;
};

/**
 * DELETE request tipado
 */
export const del = async <T>(
  url: string,
  options?: RequestOptions
): Promise<T> => {
  const response: AxiosResponse<T> = await api.delete(url, options);
  return response.data;
};

/**
 * PATCH request tipado
 */
export const patch = async <T, D = any>(
  url: string,
  data?: D,
  options?: RequestOptions
): Promise<T> => {
  const response: AxiosResponse<T> = await api.patch(url, data, options);
  return response.data;
};

// ===============================
// SPECIALIZED API METHODS
// ===============================

/**
 * Upload de arquivos
 */
export const uploadFile = async <T>(
  url: string,
  file: File,
  onUploadProgress?: (progress: number) => void
): Promise<T> => {
  const formData = new FormData();
  formData.append("file", file);

  const response: AxiosResponse<T> = await api.post(url, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onUploadProgress(progress);
      }
    },
  });

  return response.data;
};

/**
 * Download de arquivos
 */
export const downloadFile = async (
  url: string,
  filename?: string
): Promise<void> => {
  const response: AxiosResponse<Blob> = await api.get(url, {
    responseType: "blob",
  });

  const blob = new Blob([response.data]);
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename || "download";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
};

// ===============================
// HEALTH CHECK
// ===============================

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

/**
 * Health check da API
 */
export const healthCheck = async (): Promise<HealthCheckResponse> => {
  return get<HealthCheckResponse>("/api/v1/health");
};

// ===============================
// EXPORTS
// ===============================

export default api;
export { API_BASE_URL };
export type { ApiResponse, ApiError, RequestOptions };
