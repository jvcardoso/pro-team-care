/**
 * Hook para carregamento dinâmico de menus baseado nas permissões do usuário
 * Consome a API de menus dinâmicos implementada no backend
 */

import { useState, useEffect, useCallback } from "react";
import api from "../services/api";

/**
 * Hook useDynamicMenus
 *
 * Funcionalidades:
 * - Carrega menus dinamicamente da API
 * - Filtra baseado nas permissões do usuário
 * - Atualiza automaticamente quando contexto muda
 * - Fallback para menus estáticos em caso de erro
 * - Cache local para performance
 *
 * @returns {Object} { menus, loading, error, refreshMenus, isRoot, userInfo, context }
 */
export const useDynamicMenus = () => {
  try {
    console.log("🔧 useDynamicMenus hook inicializado");

    const [menus, setMenus] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isRoot, setIsRoot] = useState(false);
    const [userInfo, setUserInfo] = useState(null);
    const [context, setContext] = useState(null);
    const [lastFetch, setLastFetch] = useState(null);

    // Obter dados do usuário do localStorage
    const getUserData = () => {
      try {
        const userData = localStorage.getItem("user");
        return userData ? JSON.parse(userData) : null;
      } catch {
        return null;
      }
    };

    const getCurrentContext = () => {
      // Para o sistema atual, usar contexto padrão
      return {
        type: "establishment",
        id: 1, // ID padrão do estabelecimento
      };
    };

    const [user] = useState(getUserData);
    const [currentContext] = useState(getCurrentContext);

    // Cache TTL: 5 minutos
    const CACHE_TTL = 5 * 60 * 1000;

    /**
     * Busca menus da API
     */
    const fetchMenus = useCallback(
      async (forceFresh = false) => {
        console.log("🔧 DEBUG: fetchMenus() iniciado");
        console.log("🔧 DEBUG: forceFresh:", forceFresh);

        // 2º PORQUÊ: Verificar se há token de acesso
        const token = localStorage.getItem("access_token");
        console.log(
          "🔧 DEBUG: Token no fetchMenus:",
          !!token,
          token ? token.substring(0, 20) + "..." : "null"
        );

        if (!token) {
          console.log("❌ Sem token de acesso - não é possível carregar menus");
          console.log("🔧 DEBUG: Parando loading por falta de token");
          setLoading(false);
          setError("Token de acesso não encontrado");
          return;
        }

        // Verificar cache
        if (!forceFresh && lastFetch && Date.now() - lastFetch < CACHE_TTL) {
          return; // Usar cache
        }

        try {
          console.log("🔧 DEBUG: Entrando no try do fetchMenus");
          setLoading(true);
          setError(null);

          console.log("🔄 Carregando menus dinâmicos...");

          // Obter ID do usuário autenticado
          const userId = user?.id || 2; // Fallback para user ID 2 (admin)
          const contextType = currentContext?.type || "establishment";
          const contextId = currentContext?.id || null;

          // Usar endpoint correto de menus por usuário
          const menuUrl =
            `/api/v1/menus/user/${userId}?context_type=${contextType}` +
            (contextId ? `&context_id=${contextId}` : "");

          console.log("🔧 DEBUG: Tentando endpoint correto:", menuUrl);
          console.log("🔧 DEBUG: User ID:", userId, "Context:", contextType);

          const response = await api.get(menuUrl, {
            timeout: 10000, // 10 segundos timeout
          });
          console.log("🔧 DEBUG: Endpoint funcionou:", response.status);

          const data = response.data;

          // Validar estrutura da resposta da API de menus por usuário
          if (!data || !Array.isArray(data.menus)) {
            throw new Error("Resposta da API inválida: menus não encontrados");
          }

          // Atualizar estados usando a estrutura correta
          setMenus(data.menus);
          setIsRoot(data.user_info?.is_root || false);
          setUserInfo(data.user_info || null);
          setContext(data.context);
          setLastFetch(Date.now());

          console.log("✅ Menus carregados com sucesso", {
            totalMenus: data.total_menus,
            isRoot: data.user_info?.is_root,
            context: data.context?.type,
            includeDevMenus: data.include_dev_menus,
          });
        } catch (err) {
          console.error("❌ Erro ao carregar menus dinâmicos:", err);

          // Definir tipo de erro
          let errorMessage = "Falha ao carregar menus.";

          if (err.response?.status === 401) {
            errorMessage = "Não autenticado. Usando menus básicos.";
            console.log("🔐 Erro 401 - usuário não autenticado");
          } else if (err.response?.status === 403) {
            errorMessage = "Acesso negado. Verifique suas permissões.";
          } else if (err.response?.status === 404) {
            errorMessage = "Usuário não encontrado.";
          } else if (err.response?.status === 500) {
            errorMessage = "Erro interno do servidor.";
          } else if (err.code === "ECONNABORTED") {
            errorMessage = "Timeout: servidor demorou para responder.";
          } else if (err.code === "NETWORK_ERROR") {
            errorMessage = "Erro de rede. Verifique sua conexão.";
          }

          setError(errorMessage);

          // Fallback para menus estáticos baseado no tipo de usuário
          const fallbackMenus = getFallbackMenus(user, currentContext);
          setMenus(fallbackMenus);
          setIsRoot(user?.is_system_admin || false);
        } finally {
          setLoading(false);
        }
      },
      [user?.id, currentContext?.type, currentContext?.id, lastFetch]
    );

    /**
     * Força atualização dos menus (ignora cache)
     */
    const refreshMenus = () => {
      console.log("🔄 Forçando atualização dos menus...");
      setLastFetch(null); // Limpar cache
    };

    /**
     * Carregar menus quando user/context mudar
     */
    useEffect(() => {
      console.log("🔧 DEBUG: useEffect executado");

      // 1º PORQUÊ: Verificar se há token
      const token = localStorage.getItem("access_token");
      console.log("🔧 DEBUG: Token encontrado?", !!token);

      if (token) {
        console.log("🔄 Iniciando carregamento de menus...");
        console.log("🔧 DEBUG: Chamando fetchMenus()");
        fetchMenus();
      } else {
        console.log("❌ Sem token - carregando menus de fallback");
        console.log("🔧 DEBUG: Aplicando fallback imediato");
        setLoading(false);
        const fallbackMenus = getFallbackMenus(user, currentContext);
        console.log("🔧 DEBUG: Fallback menus:", fallbackMenus.length, "itens");
        setMenus(fallbackMenus);
        setError("Não autenticado - usando menus básicos");
      }
    }, [fetchMenus]);

    /**
     * Auto-refresh a cada 10 minutos se a aba estiver ativa
     */
    useEffect(() => {
      const handleVisibilityChange = () => {
        if (
          !document.hidden &&
          lastFetch &&
          Date.now() - lastFetch > CACHE_TTL
        ) {
          console.log("🔄 Auto-refresh: aba voltou a ficar ativa");
          refreshMenus();
        }
      };

      document.addEventListener("visibilitychange", handleVisibilityChange);

      return () => {
        document.removeEventListener(
          "visibilitychange",
          handleVisibilityChange
        );
      };
    }, [refreshMenus, lastFetch]);

    return {
      menus,
      loading,
      error,
      refreshMenus,
      isRoot,
      userInfo,
      context,
      // Informações adicionais para debug
      lastFetch: lastFetch ? new Date(lastFetch).toLocaleTimeString() : null,
      cacheAge: lastFetch ? Math.round((Date.now() - lastFetch) / 1000) : null,
    };
  } catch (hookError) {
    console.error("🔧 DEBUG: Erro crítico no useDynamicMenus hook:", hookError);
    console.error("🔧 DEBUG: Stack trace:", hookError.stack);

    // Fallback de emergência quando o hook falha completamente
    return {
      menus: [
        {
          id: "emergency-1",
          name: "Dashboard (Emergência)",
          slug: "dashboard-emergency",
          url: "/admin",
          children: [],
        },
      ],
      loading: false,
      error: `Erro crítico no hook: ${hookError.message}`,
      refreshMenus: () =>
        console.log("RefreshMenus não disponível - hook falhou"),
      isRoot: false,
      userInfo: { emergency: true },
      context: { emergency: true },
      lastFetch: null,
      cacheAge: null,
    };
  }
};

/**
 * Menus de fallback quando a API falha
 */
const getFallbackMenus = (user, context) => {
  const isRoot = user?.is_system_admin || false;

  // Menus básicos para usuário normal
  const basicMenus = [
    {
      id: 999,
      name: "Dashboard (Offline)",
      slug: "dashboard-offline",
      url: "/admin/dashboard",
      icon: "LayoutDashboard",
      level: 0,
      sort_order: 1,
      children: [],
    },
  ];

  // Menus estendidos para ROOT
  if (isRoot) {
    return [
      ...basicMenus,
      {
        id: 998,
        name: "Administração (Offline)",
        slug: "admin-offline",
        url: null,
        icon: "Settings",
        level: 0,
        sort_order: 10,
        children: [
          {
            id: 997,
            name: "Usuários",
            slug: "users-offline",
            url: "/admin/usuarios",
            icon: "Users",
            level: 1,
            sort_order: 1,
            children: [],
          },
          {
            id: 996,
            name: "Configurações",
            slug: "settings-offline",
            url: "/admin/settings",
            icon: "Settings",
            level: 1,
            sort_order: 2,
            children: [],
          },
        ],
      },
    ];
  }

  return basicMenus;
};

/**
 * Hook para informações do usuário (mock se não existir)
 */
const useUser = () => {
  // TODO: Integrar com sistema de autenticação real
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch {
        return null;
      }
    }

    // Mock users para desenvolvimento (baseado em dados reais)
    // Alternar entre usuário normal e ROOT para teste
    const testAsRoot = localStorage.getItem("testAsRoot") === "true";

    if (testAsRoot) {
      // Usuário ROOT para testes
      return {
        id: 2,
        email: "superadmin@teste.com",
        name: "Super Admin Teste",
        is_system_admin: true,
        person_type: "PF",
      };
    } else {
      // Usuário normal para testes
      return {
        id: 1,
        email: "admin@teste.com",
        name: "Admin Teste",
        is_system_admin: false,
        person_type: "PF",
      };
    }
  });

  return { user, setUser };
};

/**
 * Hook para contexto do usuário (mock se não existir)
 */
const useUserContext = () => {
  // TODO: Integrar com sistema de contexto real
  const [currentContext, setCurrentContext] = useState(() => {
    const storedContext = localStorage.getItem("currentContext");
    if (storedContext) {
      try {
        return JSON.parse(storedContext);
      } catch {
        return null;
      }
    }

    // Mock context para desenvolvimento
    return {
      type: "establishment",
      id: 1,
      name: "Estabelecimento Teste",
    };
  });

  return { currentContext, setCurrentContext };
};

export default useDynamicMenus;
