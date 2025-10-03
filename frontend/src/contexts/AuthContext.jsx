import React, { createContext, useContext, useEffect, useState } from "react";
import { authService } from "../services/api";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  // Verificar se token está expirado
  const isTokenExpired = (token) => {
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp && payload.exp < currentTime;
    } catch (e) {
      return true; // Se não conseguir decodificar, considerar expirado
    }
  };

  // Inicializar dados do localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem("access_token");
        const storedUser = localStorage.getItem("user");

        // Verificar se o token existe e não está expirado
        if (storedToken && !isTokenExpired(storedToken)) {
          if (storedUser) {
            const userData = JSON.parse(storedUser);
            setToken(storedToken);
            setUser(userData);
            console.log(
              "✅ Dados de autenticação carregados do localStorage:",
              userData
            );
          } else {
            // Se tem token válido mas não tem usuário, limpar token inválido
            console.warn(
              "⚠️ Token sem dados de usuário, limpando localStorage"
            );
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            setUser(null);
            setToken(null);
          }
        } else {
          // Token expirado ou inexistente
          if (storedToken) {
            console.warn(
              "⚠️ Token expirado encontrado no localStorage, limpando dados"
            );
          }
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          setUser(null);
          setToken(null);
        }
      } catch (error) {
        console.warn("⚠️ Erro ao inicializar autenticação:", error);
        // Limpar dados inválidos
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email, password) => {
    try {
      setLoading(true);

      // Preservar dados antes de limpar
      const savedRedirectUrl = sessionStorage.getItem('redirectAfterLogin');
      const savedTheme = localStorage.getItem('pro-team-care-theme');
      console.log("🔄 Preservando redirectAfterLogin:", savedRedirectUrl);
      console.log("🔄 Preservando tema:", savedTheme);

      // Limpar completamente qualquer sessão anterior
      localStorage.clear();
      sessionStorage.clear();
      setUser(null);
      setToken(null);

      // Restaurar dados preservados
      if (savedRedirectUrl) {
        sessionStorage.setItem('redirectAfterLogin', savedRedirectUrl);
        console.log("✅ redirectAfterLogin restaurado:", savedRedirectUrl);
      } else {
        console.log("⚠️ Nenhum redirectAfterLogin para restaurar");
      }

      if (savedTheme) {
        localStorage.setItem('pro-team-care-theme', savedTheme);
        console.log("✅ Tema restaurado:", savedTheme);
      }

      console.log("🧹 Dados anteriores limpos, iniciando novo login");

      // Fazer login
      const response = await authService.login(email, password);
      const newToken = response.access_token;

      // Salvar token
      localStorage.setItem("access_token", newToken);
      setToken(newToken);

      // Buscar dados do usuário
      console.log("🔄 Buscando dados do usuário...");
      const userData = await authService.getCurrentUser();

      // Para administradores do sistema, forçar contexto 'system'
      if (userData.is_system_admin) {
        userData.context_type = "system";
      }

      // Salvar dados do usuário
      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);

      // Para administradores do sistema, forçar mudança de contexto para 'system'
      if (userData.is_system_admin) {
        try {
          const secureSessionService = (
            await import("../services/secureSessionService")
          ).default;
          await secureSessionService.switchContext(
            "system",
            null,
            "Contexto do sistema para administrador"
          );
          console.log("🔄 Contexto alterado para 'system' para admin");
        } catch (error) {
          console.warn("⚠️ Erro ao alterar contexto para system:", error);
        }
      }

      console.log("✅ Login realizado com sucesso:", userData);
      console.log("📊 Dados da empresa:", {
        company_name: userData.company_name,
        establishment_name: userData.establishment_name,
        establishments: userData.establishments,
        context_type: userData.context_type,
      });

      // Pequeno delay para garantir que o estado seja atualizado
      // antes de outros componentes começarem a fazer requisições
      await new Promise((resolve) => setTimeout(resolve, 100));

      return { success: true, user: userData };
    } catch (error) {
      console.error("❌ Erro no login:", error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Limpar localStorage completo
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("userProfile");

    // Limpar sessionStorage também
    sessionStorage.clear();

    // Resetar estados
    setUser(null);
    setToken(null);

    console.log("✅ Logout realizado - todos os dados limpos");
  };

  const refreshUser = async () => {
    if (!token) return null;

    try {
      const userData = await authService.getCurrentUser();

      // Para administradores do sistema, forçar contexto 'system'
      if (userData.is_system_admin) {
        userData.context_type = "system";
      }

      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);
      return userData;
    } catch (error) {
      console.error("❌ Erro ao atualizar dados do usuário:", error);
      logout();
      throw error;
    }
  };

  const isAuthenticated = () => {
    return !!(token && user && user.id);
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    refreshUser,
    isAuthenticated: isAuthenticated(),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
