import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { notify } from "../utils/notifications.jsx";

// Hook para detectar tipo de dispositivo e orientação
const useDeviceType = () => {
  const [deviceType, setDeviceType] = useState("desktop"); // 'desktop', 'mobile-vertical', 'mobile-horizontal'

  useEffect(() => {
    const checkDeviceType = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const isMobile = width <= 768;
      const isPortrait = height > width;

      if (!isMobile) {
        setDeviceType("desktop");
      } else if (isPortrait) {
        setDeviceType("mobile-vertical");
      } else {
        setDeviceType("mobile-horizontal");
      }
    };

    // Verificar inicialmente
    checkDeviceType();

    // Adicionar listener para mudanças de tamanho/orientação
    window.addEventListener("resize", checkDeviceType);
    window.addEventListener("orientationchange", checkDeviceType);

    return () => {
      window.removeEventListener("resize", checkDeviceType);
      window.removeEventListener("orientationchange", checkDeviceType);
    };
  }, []);

  return deviceType;
};

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading } = useAuth();
  const deviceType = useDeviceType();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);

  // Mapear tipo de dispositivo para imagem de fundo
  const getBackgroundImage = () => {
    switch (deviceType) {
      case "mobile-vertical":
        return 'url("/login-bg-mobile-vertical.png")';
      case "mobile-horizontal":
        return 'url("/login-bg-mobile-horizontal.png")';
      default:
        return 'url("/login-bg.png")';
    }
  };

  useEffect(() => {
    // Se não está carregando e já está autenticado, redirecionar
    if (!loading && isAuthenticated) {
      const redirectUrl = sessionStorage.getItem("redirectAfterLogin");
      if (redirectUrl) {
        sessionStorage.removeItem("redirectAfterLogin");
        navigate(redirectUrl, { replace: true });
      } else {
        navigate("/admin", { replace: true });
      }
    }
  }, [navigate, loading, isAuthenticated]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Validação básica
      if (!formData.email || !formData.password) {
        throw new Error("Preencha email e senha");
      }

      console.log("Tentando login com:", formData.email, formData.password);

      // Usar o contexto de autenticação
      const result = await login(formData.email, formData.password);

      if (result.success) {
        notify.success("Login realizado com sucesso!");

        // Verificar se há uma URL para redirecionar
        const redirectUrl = sessionStorage.getItem("redirectAfterLogin");
        if (redirectUrl) {
          sessionStorage.removeItem("redirectAfterLogin");
          navigate(redirectUrl, { replace: true });
        } else {
          navigate("/admin", { replace: true });
        }
      }
    } catch (error) {
      console.error("Erro no login:", error);

      // Error handling específico
      if (error.response?.status === 401) {
        notify.error("Email ou senha incorretos");
      } else if (error.response?.status === 429) {
        notify.error("Muitas tentativas. Tente novamente em alguns minutos.");
      } else if (error.code === "NETWORK_ERROR") {
        notify.error("Erro de conexão. Verifique sua internet.");
      } else {
        notify.error(error.message || "Erro no login. Tente novamente.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative">
      {/* Fundo com imagem adaptada ao dispositivo */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-30"
        style={{ backgroundImage: getBackgroundImage() }}
      ></div>
      {/* Overlay adicional para melhorar legibilidade */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/20 to-black/40"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="bg-white shadow-2xl sm:rounded-lg border border-gray-200">
          {/* Cabeçalho do painel */}
          <div className="px-4 py-6 sm:px-10 text-center border-b border-gray-200">
            <h2 className="text-3xl font-bold text-gray-900">Pro Team Care</h2>
            <p className="mt-2 text-sm text-gray-600">
              Faça login em sua conta
            </p>
          </div>

          {/* Formulário */}
          <div className="px-4 py-8 sm:px-10">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-900"
                >
                  Email
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="seu@email.com"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-900"
                >
                  Senha
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="loading-spinner mr-2"></span>
                      Entrando...
                    </>
                  ) : (
                    "Entrar"
                  )}
                </button>
              </div>
            </form>

            <div className="mt-6 border-t border-gray-200 pt-6">
              <div className="text-center">
                <span className="text-sm text-gray-800">
                  Sistema de Gestão Profissional v1.0.0
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
