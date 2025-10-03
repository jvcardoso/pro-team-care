import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
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
    // Salvar a URL atual para redirecionar após o login
    const redirectUrl = location.pathname + location.search;
    console.log("🔄 ProtectedRoute salvando redirectAfterLogin:", redirectUrl);
    sessionStorage.setItem("redirectAfterLogin", redirectUrl);
    return <Navigate to="/login" replace />;
  }

  // Se está autenticado, mostrar o conteúdo
  return children;
};

export default ProtectedRoute;
