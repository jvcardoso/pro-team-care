import React, { useState, useEffect, useRef } from "react";
import {
  Users,
  Shield,
  Building2,
  Store,
  ChevronDown,
  AlertCircle,
  UserCheck,
  LogOut,
} from "lucide-react";
import secureSessionService from "../../services/secureSessionService";
import { notify } from "../../utils/notifications.jsx";

const ProfileSwitcher = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [profiles, setProfiles] = useState([]);
  const [currentContext, setCurrentContext] = useState(null);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    loadData();

    // Listen for context changes
    const handleContextChange = (newContext) => {
      setCurrentContext(newContext);
    };

    secureSessionService.addListener(handleContextChange);

    return () => {
      secureSessionService.removeListener(handleContextChange);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await secureSessionService.initialize();

      const [profilesData, contextData] = await Promise.all([
        secureSessionService.getAvailableProfiles(),
        secureSessionService.getCurrentContext(),
      ]);

      setProfiles(profilesData.profiles || []);
      setCurrentContext(contextData);
    } catch (error) {
      console.error("Erro ao carregar dados do profile switcher:", error);
      // Se não conseguir carregar, pode ser que não há sessão segura ainda
      setProfiles([]);
      setCurrentContext(null);
    } finally {
      setLoading(false);
    }
  };

  const handleImpersonation = async (profile) => {
    try {
      setLoading(true);

      const reason = prompt("Motivo da personificação (obrigatório):");
      if (!reason) {
        notify.warning("Motivo é obrigatório para personificação");
        return;
      }

      await secureSessionService.impersonateUser(
        profile.target_user_id,
        reason
      );

      notify.success(`Personificando: ${profile.target_user_email}`);
      setIsOpen(false);

      // Reload page to refresh all components
      window.location.reload();
    } catch (error) {
      notify.error("Erro ao personificar usuário");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleContextSwitch = async (profile) => {
    try {
      setLoading(true);

      await secureSessionService.switchContext(
        profile.context_type,
        profile.context_id,
        `Troca para ${profile.context_name}`
      );

      notify.success(`Contexto alterado: ${profile.context_name}`);
      setIsOpen(false);

      // Reload to refresh components
      window.location.reload();
    } catch (error) {
      notify.error("Erro ao trocar contexto");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopImpersonation = async () => {
    try {
      setLoading(true);
      await secureSessionService.terminateSession();
      notify.success("Personificação encerrada");
      setIsOpen(false);
      window.location.reload();
    } catch (error) {
      notify.error("Erro ao encerrar personificação");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getContextIcon = (contextType) => {
    switch (contextType) {
      case "system":
        return <Shield className="h-4 w-4" />;
      case "company":
        return <Building2 className="h-4 w-4" />;
      case "establishment":
        return <Store className="h-4 w-4" />;
      default:
        return <Users className="h-4 w-4" />;
    }
  };

  const isImpersonating = currentContext?.is_impersonating;
  const isRoot = currentContext?.is_root;

  // Sempre mostrar para ROOT, mesmo sem perfis disponíveis
  // Só esconder se não for ROOT E não tiver perfis E não estiver personificando
  if (!isRoot && !profiles.length && !isImpersonating) {
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Current Context Indicator */}
      {isImpersonating && (
        <div className="mb-2 px-3 py-2 bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">
            Personificando:{" "}
            <strong>{currentContext.effective_user_email}</strong>
          </span>
        </div>
      )}

      {/* Profile Switcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className={`
          flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors
          ${
            isImpersonating
              ? "bg-orange-100 text-orange-800 hover:bg-orange-200 dark:bg-orange-900 dark:text-orange-200 dark:hover:bg-orange-800"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          }
          ${loading ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        {isRoot ? (
          <Shield className="h-4 w-4" />
        ) : (
          <Users className="h-4 w-4" />
        )}
        <span>{isImpersonating ? "Personificando" : "Trocar Perfil"}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-y-auto">
          {/* Current Status */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Perfis Disponíveis
              </h3>
              {isRoot && (
                <span className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs rounded-full">
                  ROOT
                </span>
              )}
            </div>

            {isImpersonating && (
              <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-orange-800 dark:text-orange-200">
                    Usuário Real: {currentContext.user_email}
                  </span>
                  <button
                    onClick={handleStopImpersonation}
                    disabled={loading}
                    className="flex items-center space-x-1 text-orange-600 hover:text-orange-800 dark:text-orange-400 dark:hover:text-orange-200"
                  >
                    <LogOut className="h-3 w-3" />
                    <span>Sair</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Available Profiles */}
          <div className="py-2">
            {profiles.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 text-center">
                Nenhum perfil disponível
              </div>
            ) : (
              profiles.map((profile, index) => (
                <button
                  key={index}
                  onClick={() => {
                    if (profile.is_impersonation) {
                      handleImpersonation(profile);
                    } else {
                      handleContextSwitch(profile);
                    }
                  }}
                  disabled={loading}
                  className={`
                    w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 flex items-start space-x-3 transition-colors
                    ${loading ? "opacity-50 cursor-not-allowed" : ""}
                  `}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {profile.is_impersonation ? (
                      <UserCheck className="h-4 w-4 text-blue-500" />
                    ) : (
                      getContextIcon(profile.context_type)
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {profile.role_display_name}
                      </p>
                      {profile.is_impersonation && (
                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                          Personificar
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {profile.context_name}
                    </p>

                    {profile.is_impersonation && (
                      <p className="text-xs text-gray-600 dark:text-gray-300 mt-1 font-mono">
                        👤 {profile.target_user_email}
                      </p>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileSwitcher;
