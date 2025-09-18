/**
 * Hook para carregamento dinâmico de menus baseado nas permissões do usuário
 * Consome a API de menus dinâmicos implementada no backend
 */

import { useState, useEffect, useCallback } from "react";
import { menusService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

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
    const { user, isAuthenticated, loading: authLoading } = useAuth();

    const [menus, setMenus] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isRoot, setIsRoot] = useState(false);
    const [userInfo, setUserInfo] = useState(null);
    const [context, setContext] = useState(null);
    const [lastFetch, setLastFetch] = useState(null);

    const getCurrentContext = () => {
      // Determinar contexto baseado no usuário
      if (!user) {
        return { type: "establishment", id: null };
      }

      // Se o usuário tem company_id, usar contexto de empresa
      if (user.company_id) {
        return {
          type: "company",
          id: user.company_id,
        };
      }

      // Se o usuário tem establishment_id, usar contexto de estabelecimento
      if (user.establishment_id) {
        return {
          type: "establishment",
          id: user.establishment_id,
        };
      }

      // ROOT ou usuários sem contexto específico
      if (user.is_system_admin) {
        return { type: "system", id: null };
      }

      // Fallback padrão
      return { type: "establishment", id: null };
    };

    // Contexto dinâmico que atualiza quando user muda
    const currentContext = getCurrentContext();

    // Cache TTL: 5 minutos
    const CACHE_TTL = 5 * 60 * 1000;

    /**
     * Busca menus da API
     */
    const fetchMenus = useCallback(
      async (forceFresh = false) => {
        // Só tentar carregar menus se o usuário estiver autenticado
        if (authLoading) {
          return; // Aguardar autenticação
        }

        if (!isAuthenticated || !user?.id) {
          setLoading(false);
          setError("Usuário não autenticado");
          return;
        }

        // Verificação adicional do token
        const token = localStorage.getItem("access_token");
        if (!token) {
          console.log("⚠️ Token não encontrado, não carregando menus");
          setLoading(false);
          return;
        }

        // Verificar cache
        if (!forceFresh && lastFetch && Date.now() - lastFetch < CACHE_TTL) {
          return; // Usar cache
        }

        try {
          setLoading(true);
          setError(null);

          const userId = user.id;
          const contextType = currentContext?.type || "establishment";
          const contextId = currentContext?.id || null;

          console.log("🔄 Carregando menus para usuário:", userId);
          console.log("📋 Contexto:", { type: contextType, id: contextId });
          console.log("👤 User data:", {
            company_id: user.company_id,
            establishment_id: user.establishment_id,
            is_system_admin: user.is_system_admin,
          });

          // Usar serviço de menus
          const response = await menusService.getUserMenus(
            userId,
            contextType,
            contextId
          );

          // Validar estrutura da resposta da API simplificada
          if (
            !response ||
            !response.success ||
            !Array.isArray(response.menus)
          ) {
            throw new Error("Resposta da API inválida: menus não encontrados");
          }

          // Atualizar estados usando a estrutura simplificada
          setMenus(response.menus);
          setIsRoot(response.user_info?.is_root || user?.is_system_admin);
          setUserInfo(
            response.user_info || {
              id: userId,
              is_admin: user?.is_system_admin,
            }
          );
          setContext(response.context || { type: contextType, id: contextId });
          setLastFetch(Date.now());
        } catch (err) {
          console.error("❌ Erro ao carregar menus dinâmicos:", err);
          setMenus([]);
          setError(err.message || "Erro ao carregar menus");
        } finally {
          setLoading(false);
        }
      },
      [
        user?.id,
        user?.company_id,
        user?.establishment_id,
        user?.is_system_admin,
        currentContext?.type,
        currentContext?.id,
        lastFetch,
        authLoading,
        isAuthenticated,
      ]
    );

    /**
     * Força atualização dos menus (ignora cache)
     */
    const refreshMenus = () => {
      setLastFetch(null); // Limpar cache
      fetchMenus(true); // Força nova busca
    };

    /**
     * Carregar menus quando user/context mudar
     */
    useEffect(() => {
      if (!authLoading && isAuthenticated && user?.id) {
        // Delay maior para evitar conflito com outros componentes
        const timer = setTimeout(() => {
          fetchMenus();
        }, 800);

        return () => clearTimeout(timer);
      }
    }, [fetchMenus, authLoading, isAuthenticated, user?.id]);

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
    console.error("Erro crítico no useDynamicMenus hook:", hookError);
    return {
      menus: [],
      loading: false,
      error: `Erro crítico no hook: ${hookError.message}`,
      refreshMenus: () => {},
      isRoot: false,
      userInfo: null,
      context: null,
      lastFetch: null,
      cacheAge: null,
    };
  }
};

export default useDynamicMenus;
