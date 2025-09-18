import React, { useState, useEffect } from "react";
import { Building2, Store, Shield, ChevronDown, Check } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import secureSessionService from "../../services/secureSessionService";
import { notify } from "../../utils/notifications.jsx";

const ContextSwitcher = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [contexts, setContexts] = useState([]);
  const [currentContext, setCurrentContext] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Só carregar contextos se usuário estiver autenticado
    if (!authLoading && isAuthenticated && user?.id) {
      // Adicionar delay para evitar conflito com outros componentes
      const timer = setTimeout(() => {
        loadContexts();
      }, 600);

      return () => clearTimeout(timer);
    }
  }, [authLoading, isAuthenticated, user?.id]);

  useEffect(() => {
    if (isAuthenticated && user?.id) {
      // Listen for context changes
      const handleContextChange = (newContext) => {
        setCurrentContext(newContext);
      };

      secureSessionService.addListener(handleContextChange);

      return () => {
        secureSessionService.removeListener(handleContextChange);
      };
    }
  }, [isAuthenticated, user?.id]);

  const loadContexts = async () => {
    // Verificar se ainda está autenticado antes de carregar
    if (!isAuthenticated || !user?.id) {
      console.log("⏳ ContextSwitcher: Aguardando autenticação...");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      console.log("⚠️ ContextSwitcher: Token não encontrado");
      return;
    }

    try {
      const [profilesData, contextData] = await Promise.all([
        secureSessionService.getAvailableProfiles(),
        secureSessionService.getCurrentContext(),
      ]);

      // Filter only context-related profiles (not impersonation)
      const contextProfiles =
        profilesData.profiles?.filter((p) => !p.is_impersonation) || [];
      setContexts(contextProfiles);
      setCurrentContext(contextData);
    } catch (error) {
      console.error("Erro ao carregar contextos:", error);
      setContexts([]);
      setCurrentContext(null);
    }
  };

  const handleContextSwitch = async (context) => {
    try {
      setLoading(true);

      await secureSessionService.switchContext(
        context.context_type,
        context.context_id,
        `Mudança de contexto para ${context.context_name}`
      );

      notify.success(`Contexto alterado: ${context.context_name}`);
      setIsOpen(false);

      // Reload page to refresh all data
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      notify.error("Erro ao trocar contexto");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getContextIcon = (contextType) => {
    switch (contextType) {
      case "system":
        return <Shield className="h-4 w-4 text-blue-500" />;
      case "company":
        return <Building2 className="h-4 w-4 text-green-500" />;
      case "establishment":
        return <Store className="h-4 w-4 text-orange-500" />;
      default:
        return <Shield className="h-4 w-4 text-gray-500" />;
    }
  };

  const getCurrentContextName = () => {
    if (!currentContext) return "Sistema";

    const activeContext = currentContext.active_context;
    if (!activeContext?.type) return "Sistema";

    // Find current context in available contexts
    const current = contexts.find(
      (c) =>
        c.context_type === activeContext.type &&
        c.context_id === activeContext.id
    );

    return current?.context_name || "Contexto Ativo";
  };

  const getCurrentContextType = () => {
    return currentContext?.active_context?.type || "system";
  };

  // Don't show if no contexts available
  if (contexts.length <= 1) {
    return null;
  }

  return (
    <div className="relative">
      {/* Context Switcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className={`
          flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors min-w-48 justify-between
          bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
          hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100
          ${loading ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <div className="flex items-center space-x-2">
          {getContextIcon(getCurrentContextType())}
          <span className="truncate">{getCurrentContextName()}</span>
        </div>
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-y-auto">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Selecionar Contexto
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Escolha o contexto de trabalho
            </p>
          </div>

          {/* Available Contexts */}
          <div className="py-2">
            {contexts.map((context, index) => {
              const isActive =
                currentContext?.active_context?.type === context.context_type &&
                currentContext?.active_context?.id === context.context_id;

              return (
                <button
                  key={index}
                  onClick={() => handleContextSwitch(context)}
                  disabled={loading || isActive}
                  className={`
                    w-full px-4 py-3 text-left flex items-center space-x-3 transition-colors
                    ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100"
                        : "hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
                    }
                    ${loading ? "opacity-50 cursor-not-allowed" : ""}
                  `}
                >
                  <div className="flex-shrink-0">
                    {getContextIcon(context.context_type)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium truncate">
                        {context.context_name}
                      </p>
                      {isActive && (
                        <Check className="h-4 w-4 text-blue-500 flex-shrink-0" />
                      )}
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {context.role_display_name}
                    </p>

                    <div className="flex items-center mt-1 space-x-2">
                      <span
                        className={`
                        px-2 py-0.5 text-xs rounded-full
                        ${
                          context.context_type === "system"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                            : context.context_type === "company"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200"
                        }
                      `}
                      >
                        {context.context_type === "system"
                          ? "Sistema"
                          : context.context_type === "company"
                          ? "Empresa"
                          : "Estabelecimento"}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContextSwitcher;
