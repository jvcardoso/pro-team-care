/**
 * HTTP Cache simples em memória
 * Implementa cache com TTL para otimizar requests frequentes
 */

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number; // Time to live em milliseconds
}

class HttpCache {
  private cache = new Map<string, CacheEntry>();

  // TTL padrão para diferentes tipos de dados (em milliseconds)
  private readonly DEFAULT_TTLS = {
    companies: 5 * 60 * 1000, // 5 minutos - dados de empresas
    addresses: 30 * 60 * 1000, // 30 minutos - dados de endereço (ViaCEP)
    cnpj: 60 * 60 * 1000, // 60 minutos - dados do CNPJ
    health: 2 * 60 * 1000, // 2 minutos - health check
    menus: 5 * 60 * 1000, // 5 minutos - dados de menus (podem ser editados)
    users: 2 * 60 * 1000, // 2 minutos - dados de usuários (podem mudar frequentemente)
    auth: 24 * 60 * 60 * 1000, // 24 horas - dados de auth
    static: 24 * 60 * 60 * 1000, // 24 horas - dados estáticos
  } as const;

  /**
   * Gera chave de cache baseada na URL e parâmetros
   */
  private generateKey(url: string, params?: any): string {
    const paramString = params ? JSON.stringify(params) : "";
    return `${url}${paramString}`;
  }

  /**
   * Determina TTL baseado na URL
   */
  private getTTLForUrl(url: string): number {
    if (url.includes("/companies")) return this.DEFAULT_TTLS.companies;
    if (url.includes("/addresses") || url.includes("viacep"))
      return this.DEFAULT_TTLS.addresses;
    if (url.includes("/cnpj")) return this.DEFAULT_TTLS.cnpj;
    if (url.includes("/health")) return this.DEFAULT_TTLS.health;
    if (url.includes("/menus") || url.includes("/menu"))
      return this.DEFAULT_TTLS.menus;
    if (url.includes("/users")) return this.DEFAULT_TTLS.users;
    if (url.includes("/auth")) return this.DEFAULT_TTLS.auth;
    return this.DEFAULT_TTLS.static;
  }

  /**
   * Verifica se entrada do cache ainda é válida
   */
  private isValid(entry: CacheEntry): boolean {
    const now = Date.now();
    return now - entry.timestamp < entry.ttl;
  }

  /**
   * Busca dados do cache
   */
  get(url: string, params?: any): any | null {
    const key = this.generateKey(url, params);
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    if (!this.isValid(entry)) {
      this.cache.delete(key);
      return null;
    }

    if (process.env.NODE_ENV === "development") {
      console.log("🔄 Cache HIT:", url);
    }

    return entry.data;
  }

  /**
   * Armazena dados no cache
   */
  set(url: string, data: any, params?: any, customTTL?: number): void {
    const key = this.generateKey(url, params);
    const ttl = customTTL || this.getTTLForUrl(url);

    const entry: CacheEntry = {
      data: JSON.parse(JSON.stringify(data)), // Deep clone
      timestamp: Date.now(),
      ttl,
    };

    this.cache.set(key, entry);

    if (process.env.NODE_ENV === "development") {
      console.log("💾 Cache SET:", url, `TTL: ${ttl}ms`);
    }
  }

  /**
   * Remove entrada específica do cache
   */
  delete(url: string, params?: any): boolean {
    const key = this.generateKey(url, params);
    return this.cache.delete(key);
  }

  /**
   * Invalida cache por padrão de URL
   */
  invalidatePattern(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }

    if (process.env.NODE_ENV === "development") {
      console.log("🗑️ Cache invalidated pattern:", pattern);
    }
  }

  /**
   * Limpa todo o cache
   */
  clear(): void {
    this.cache.clear();

    if (process.env.NODE_ENV === "development") {
      console.log("🧹 Cache cleared");
    }
  }

  /**
   * Remove entradas expiradas do cache
   */
  cleanup(): void {
    const now = Date.now();
    let removedCount = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (!this.isValid(entry)) {
        this.cache.delete(key);
        removedCount++;
      }
    }

    if (process.env.NODE_ENV === "development") {
      console.log(`🧹 Cache cleanup: ${removedCount} expired entries removed`);
    }
  }

  /**
   * Estatísticas do cache
   */
  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
}

// Singleton instance
export const httpCache = new HttpCache();

// Auto cleanup a cada 5 minutos
setInterval(() => {
  httpCache.cleanup();
}, 5 * 60 * 1000);

// Cache de dados dinâmicos será invalidado conforme necessário pelas operações CRUD

// 🔄 Interceptor para cache automático em requests GET
export const createCacheInterceptor = (axiosInstance: any) => {
  // Lista de endpoints que NÃO devem ter cache (dados dinâmicos críticos)
  const NO_CACHE_PATTERNS = [
    "/users/count", // Contadores de usuários
    "/users/", // Lista de usuários
    "/users?", // Lista de usuários com parâmetros
    "/establishments/count", // Contadores de estabelecimentos
    "/establishments/", // Lista de estabelecimentos
    "/clients/count", // Contadores de clientes
    "/clients/", // Lista de clientes
    "/auth/", // Dados de autenticação
  ];

  // Função para verificar se URL deve ter cache
  const shouldCache = (url: string): boolean => {
    return !NO_CACHE_PATTERNS.some((pattern) => url.includes(pattern));
  };

  // Request interceptor - verificar cache antes do request
  axiosInstance.interceptors.request.use((config: any) => {
    // Só aplicar cache para requests GET de dados estáticos
    if (config.method === "get" && shouldCache(config.url)) {
      const cached = httpCache.get(config.url, config.params);
      if (cached) {
        // Retornar dados do cache como response
        return Promise.reject({
          cached: true,
          data: cached,
          status: 200,
          statusText: "OK (cached)",
        });
      }
    }
    return config;
  });

  // Response interceptor - armazenar responses GET no cache
  axiosInstance.interceptors.response.use(
    (response: any) => {
      // Cache apenas responses GET bem-sucedidos de dados estáticos
      if (
        response.config.method === "get" &&
        response.status === 200 &&
        shouldCache(response.config.url)
      ) {
        httpCache.set(
          response.config.url,
          response.data,
          response.config.params
        );
      }
      return response;
    },
    (error: any) => {
      // Se é um erro de cache (cached: true), converter para response normal
      if (error.cached) {
        return Promise.resolve({
          data: error.data,
          status: error.status,
          statusText: error.statusText,
          headers: {},
          config: {},
          request: {},
        });
      }
      return Promise.reject(error);
    }
  );
};

export default httpCache;
