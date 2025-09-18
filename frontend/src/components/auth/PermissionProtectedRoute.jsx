import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { Shield, AlertTriangle } from "lucide-react";

/**
 * Componente para proteger rotas baseado em permissões específicas
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Componente a ser renderizado se o usuário tiver permissão
 * @param {string} props.requiredPermission - Permissão necessária para acessar a rota (ex: 'system.admin')
 * @param {boolean} props.requireRoot - Se true, apenas ROOT pode acessar (ignora requiredPermission)
 * @param {string} props.fallbackMessage - Mensagem personalizada de acesso negado
 */
const PermissionProtectedRoute = ({
  children,
  requiredPermission = null,
  requireRoot = false,
  fallbackMessage = null,
}) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  // Mostrar loading enquanto verifica autenticação
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            Verificando autenticação...
          </p>
        </div>
      </div>
    );
  }

  // Se não está autenticado, redirecionar para login
  if (!isAuthenticated) {
    sessionStorage.setItem(
      "redirectAfterLogin",
      location.pathname + location.search
    );
    return <Navigate to="/login" replace />;
  }

  // Verificar se é ROOT (quando requireRoot = true)
  if (requireRoot && !user?.is_system_admin) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="mb-4">
            <Shield className="h-16 w-16 text-red-500 mx-auto" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Acesso Restrito
          </h1>
          <p className="text-muted-foreground mb-4">
            {fallbackMessage ||
              "Esta página é acessível apenas para administradores do sistema (ROOT)."}
          </p>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span className="text-red-800 text-sm">
                Permissão necessária:{" "}
                <code className="bg-red-100 px-1 rounded">system.admin</code>
              </span>
            </div>
          </div>
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Voltar
          </button>
        </div>
      </div>
    );
  }

  // TODO: Implementar verificação de permissões específicas no futuro
  // Para agora, apenas verificação ROOT funciona
  if (requiredPermission && !requireRoot) {
    console.warn(
      `PermissionProtectedRoute: Verificação de permissão '${requiredPermission}' não implementada ainda. Usando apenas verificação ROOT.`
    );
  }

  // Se todas as verificações passaram, mostrar o conteúdo
  return children;
};

export default PermissionProtectedRoute;
