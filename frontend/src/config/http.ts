/**
 * Configurações HTTP centralizadas
 * 🔄 Padronização de timeouts, headers e configurações
 */

// 🌐 Base URLs - usar proxy do Vite em desenvolvimento
export const API_BASE_URL = (() => {
  // Jest environment detection
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return "http://localhost:8000";
  }

  // Vite environment
  if (typeof import.meta !== "undefined" && import.meta.env) {
    return import.meta.env.DEV
      ? ""
      : import.meta.env.VITE_API_URL || "http://192.168.11.83:8000";
  }

  // Fallback
  return "http://192.168.11.83:8000";
})();

// ⏱️ Timeouts padronizados (em milliseconds)
export const HTTP_TIMEOUTS = {
  DEFAULT: 10000, // 10s - Requests normais
  EXTERNAL: 15000, // 15s - APIs externas (ViaCEP, CNPJ)
  UPLOAD: 30000, // 30s - Upload de arquivos
  LONG_RUNNING: 60000, // 60s - Operações longas
} as const;

// 📋 Headers padronizados
export const HTTP_HEADERS = {
  JSON: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  FORM_DATA: {
    "Content-Type": "multipart/form-data",
  },
  FORM_URLENCODED: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
} as const;

// 🔄 Retry configurations
export const RETRY_CONFIG = {
  retries: 3,
  retryDelay: (retryCount: number) => Math.pow(2, retryCount) * 1000, // Exponential backoff
  retryCondition: (error: any) => {
    // Retry on network errors and 5xx status codes
    return (
      !error.response ||
      (error.response.status >= 500 && error.response.status <= 599)
    );
  },
} as const;

// 🏥 Specific service configurations
export const SERVICE_CONFIGS = {
  // Main API service
  main: {
    baseURL: API_BASE_URL,
    timeout: HTTP_TIMEOUTS.DEFAULT,
    headers: HTTP_HEADERS.JSON,
  },

  // CNPJ public service
  cnpj: {
    baseURL: API_BASE_URL,
    timeout: HTTP_TIMEOUTS.EXTERNAL,
    headers: HTTP_HEADERS.JSON,
  },

  // Address enrichment (ViaCEP, etc)
  address: {
    timeout: HTTP_TIMEOUTS.EXTERNAL,
    headers: HTTP_HEADERS.JSON,
  },

  // File upload service
  upload: {
    baseURL: API_BASE_URL,
    timeout: HTTP_TIMEOUTS.UPLOAD,
    headers: HTTP_HEADERS.FORM_DATA,
  },
} as const;

// 🔒 Security headers
export const SECURITY_HEADERS = {
  "X-Requested-With": "XMLHttpRequest",
  "X-Content-Type-Options": "nosniff",
} as const;

// 📊 Common axios configuration factory
export const createAxiosConfig = (
  serviceType: keyof typeof SERVICE_CONFIGS = "main"
) => {
  const config = SERVICE_CONFIGS[serviceType];

  return {
    ...config,
    headers: {
      ...config.headers,
      ...SECURITY_HEADERS,
    },
  };
};

// 🌍 Environment-specific configurations
export const ENV_CONFIG = {
  development: {
    enableLogging: true,
    enableMocks: false,
  },
  production: {
    enableLogging: false,
    enableMocks: false,
  },
} as const;

// 🎯 Get current environment config
export const getCurrentEnvConfig = () => {
  // Jest environment
  if (typeof process !== "undefined" && process.env.NODE_ENV === "test") {
    return ENV_CONFIG.development;
  }

  // Vite environment
  if (typeof import.meta !== "undefined" && import.meta.env) {
    const env = import.meta.env.MODE as keyof typeof ENV_CONFIG;
    return ENV_CONFIG[env] || ENV_CONFIG.development;
  }

  // Fallback
  return ENV_CONFIG.development;
};
