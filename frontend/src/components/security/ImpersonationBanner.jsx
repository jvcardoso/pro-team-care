import React, { useState, useEffect } from "react";
import { AlertTriangle, User, LogOut, Info } from "lucide-react";
import secureSessionService from "../../services/secureSessionService";
import { notify } from "../../utils/notifications.jsx";

const ImpersonationBanner = () => {
  const [currentContext, setCurrentContext] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCurrentContext();

    // Listen for context changes
    const handleContextChange = (newContext) => {
      setCurrentContext(newContext);
    };

    secureSessionService.addListener(handleContextChange);

    return () => {
      secureSessionService.removeListener(handleContextChange);
    };
  }, []);

  const loadCurrentContext = async () => {
    try {
      const context = await secureSessionService.getCurrentContext();
      setCurrentContext(context);
    } catch (error) {
      // Silently fail if no secure session
      setCurrentContext(null);
    }
  };

  const handleStopImpersonation = async () => {
    try {
      setLoading(true);
      await secureSessionService.terminateSession();
      notify.success("Personificação encerrada");

      // Reload page to refresh all components
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      notify.error("Erro ao encerrar personificação");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Se não está personificando, não mostrar o banner
  if (!currentContext?.is_impersonating) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3">
          {/* Left side - Warning info */}
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-5 w-5 animate-pulse" />

            <div className="flex items-center space-x-2">
              <span className="font-medium">MODO PERSONIFICAÇÃO ATIVO</span>
              <span className="text-orange-100">•</span>
              <div className="flex items-center space-x-1">
                <User className="h-4 w-4" />
                <span className="text-sm">
                  Você está operando como:{" "}
                  <strong>{currentContext.effective_user_email}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Right side - Controls */}
          <div className="flex items-center space-x-4">
            {/* Real user info */}
            <div className="hidden md:flex items-center space-x-2 text-sm bg-black/20 px-3 py-1 rounded-full">
              <Info className="h-4 w-4" />
              <span>Usuário real: {currentContext.user_email}</span>
            </div>

            {/* Stop impersonation button */}
            <button
              onClick={handleStopImpersonation}
              disabled={loading}
              className={`
                flex items-center space-x-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors text-sm font-medium
                ${loading ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              <LogOut className="h-4 w-4" />
              <span>
                {loading ? "Encerrando..." : "Encerrar Personificação"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile version - stacked layout */}
      <div className="md:hidden border-t border-orange-400/30">
        <div className="px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-1 text-xs bg-black/20 px-2 py-1 rounded">
            <Info className="h-3 w-3" />
            <span>Real: {currentContext.user_email}</span>
          </div>

          <button
            onClick={handleStopImpersonation}
            disabled={loading}
            className={`
              flex items-center space-x-1 text-xs px-3 py-1 bg-white/20 hover:bg-white/30 rounded transition-colors
              ${loading ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            <LogOut className="h-3 w-3" />
            <span>{loading ? "Encerrando..." : "Sair"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImpersonationBanner;
