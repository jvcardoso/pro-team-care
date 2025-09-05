/**
 * Hook para carregamento dinâmico de menus baseado nas permissões do usuário
 * Consome a API de menus dinâmicos implementada no backend
 */

import { useState, useEffect, useCallback } from 'react';
// import { useUser } from './useUser';  // TODO: Implementar hook real
// import { useUserContext } from './useUserContext';  // TODO: Implementar hook real
import api from '../services/api';

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
    const [menus, setMenus] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isRoot, setIsRoot] = useState(false);
    const [userInfo, setUserInfo] = useState(null);
    const [context, setContext] = useState(null);
    const [lastFetch, setLastFetch] = useState(null);
    
    const { user } = useUser();
    const { currentContext } = useUserContext();
    
    // Cache TTL: 5 minutos
    const CACHE_TTL = 5 * 60 * 1000;
    
    /**
     * Busca menus da API
     */
    const fetchMenus = useCallback(async (forceFresh = false) => {
        if (!user?.id || !currentContext) {
            setLoading(false);
            return;
        }
        
        // Verificar cache
        if (!forceFresh && lastFetch && (Date.now() - lastFetch) < CACHE_TTL) {
            return; // Usar cache
        }
        
        try {
            setLoading(true);
            setError(null);
            
            console.log('🔄 Carregando menus dinâmicos...', {
                userId: user.id,
                contextType: currentContext.type,
                contextId: currentContext.id
            });
            
            const response = await api.get(`/api/v1/menus/user/${user.id}`, {
                params: {
                    context_type: currentContext.type || 'establishment',
                    context_id: currentContext.id || null,
                    include_dev_menus: currentContext.type === 'system' ? true : null
                },
                timeout: 10000 // 10 segundos timeout
            });
            
            const data = response.data;
            
            // Validar estrutura da resposta
            if (!data || !Array.isArray(data.menus)) {
                throw new Error('Resposta da API inválida: menus não é um array');
            }
            
            // Atualizar estados
            setMenus(data.menus);
            setIsRoot(data.user_info?.is_root || false);
            setUserInfo(data.user_info);
            setContext(data.context);
            setLastFetch(Date.now());
            
            console.log('✅ Menus carregados com sucesso', {
                totalMenus: data.total_menus,
                isRoot: data.user_info?.is_root,
                context: data.context?.type,
                includeDevMenus: data.include_dev_menus
            });
            
        } catch (err) {
            console.error('❌ Erro ao carregar menus dinâmicos:', err);
            
            // Definir tipo de erro
            let errorMessage = 'Falha ao carregar menus.';
            
            if (err.response?.status === 403) {
                errorMessage = 'Acesso negado. Verifique suas permissões.';
            } else if (err.response?.status === 404) {
                errorMessage = 'Usuário não encontrado.';
            } else if (err.response?.status === 500) {
                errorMessage = 'Erro interno do servidor.';
            } else if (err.code === 'ECONNABORTED') {
                errorMessage = 'Timeout: servidor demorou para responder.';
            } else if (err.code === 'NETWORK_ERROR') {
                errorMessage = 'Erro de rede. Verifique sua conexão.';
            }
            
            setError(errorMessage);
            
            // Fallback para menus estáticos baseado no tipo de usuário
            const fallbackMenus = getFallbackMenus(user, currentContext);
            setMenus(fallbackMenus);
            setIsRoot(user?.is_system_admin || false);
            
        } finally {
            setLoading(false);
        }
    }, [user?.id, currentContext?.type, currentContext?.id, lastFetch]);
    
    /**
     * Força atualização dos menus (ignora cache)
     */
    const refreshMenus = () => {
        console.log('🔄 Forçando atualização dos menus...');
        setLastFetch(null); // Limpar cache
    };
    
    /**
     * Carregar menus quando user/context mudar
     */
    useEffect(() => {
        if (user?.id && currentContext) {
            fetchMenus();
        }
    }, [user?.id, currentContext?.type, currentContext?.id, fetchMenus]);
    
    /**
     * Auto-refresh a cada 10 minutos se a aba estiver ativa
     */
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (!document.hidden && lastFetch && (Date.now() - lastFetch) > CACHE_TTL) {
                console.log('🔄 Auto-refresh: aba voltou a ficar ativa');
                refreshMenus();
            }
        };
        
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
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
        cacheAge: lastFetch ? Math.round((Date.now() - lastFetch) / 1000) : null
    };
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
            name: 'Dashboard (Offline)',
            slug: 'dashboard-offline',
            url: '/admin/dashboard',
            icon: 'LayoutDashboard',
            level: 0,
            sort_order: 1,
            children: []
        }
    ];
    
    // Menus estendidos para ROOT
    if (isRoot) {
        return [
            ...basicMenus,
            {
                id: 998,
                name: 'Administração (Offline)',
                slug: 'admin-offline',
                url: null,
                icon: 'Settings',
                level: 0,
                sort_order: 10,
                children: [
                    {
                        id: 997,
                        name: 'Usuários',
                        slug: 'users-offline',
                        url: '/admin/users',
                        icon: 'Users',
                        level: 1,
                        sort_order: 1,
                        children: []
                    },
                    {
                        id: 996,
                        name: 'Configurações',
                        slug: 'settings-offline',
                        url: '/admin/settings',
                        icon: 'Settings',
                        level: 1,
                        sort_order: 2,
                        children: []
                    }
                ]
            }
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
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                return JSON.parse(storedUser);
            } catch {
                return null;
            }
        }
        
        // Mock users para desenvolvimento (baseado em dados reais)
        // Alternar entre usuário normal e ROOT para teste
        const testAsRoot = localStorage.getItem('testAsRoot') === 'true';
        
        if (testAsRoot) {
            // Usuário ROOT para testes
            return {
                id: 2,
                email: 'superadmin@teste.com',
                name: 'Super Admin Teste',
                is_system_admin: true,
                person_type: 'PF'
            };
        } else {
            // Usuário normal para testes
            return {
                id: 1,
                email: 'admin@teste.com',
                name: 'Admin Teste',
                is_system_admin: false,
                person_type: 'PF'
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
        const storedContext = localStorage.getItem('currentContext');
        if (storedContext) {
            try {
                return JSON.parse(storedContext);
            } catch {
                return null;
            }
        }
        
        // Mock context para desenvolvimento
        return {
            type: 'establishment',
            id: 1,
            name: 'Estabelecimento Teste'
        };
    });
    
    return { currentContext, setCurrentContext };
};

export default useDynamicMenus;