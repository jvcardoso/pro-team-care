import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, Loader2, Eye, EyeOff } from "lucide-react";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import userActivationService from "../services/userActivationService";

const ActivationPage = () => {
  const { token } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [activating, setActivating] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // Validar token ao carregar a página
  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setError("Token de ativação não fornecido");
      setLoading(false);
    }
  }, [token]);

  const validateToken = async () => {
    try {
      setValidating(true);
      const response = await userActivationService.validateActivationToken(
        token
      );

      if (response.valid) {
        setTokenValid(true);
        setUserInfo(response);
        setError("");
      } else {
        setError("Token de ativação inválido ou expirado");
      }
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail || "Erro ao validar token";
      setError(errorMessage);
    } finally {
      setLoading(false);
      setValidating(false);
    }
  };

  const handleActivation = async (e) => {
    e.preventDefault();

    // Validações
    if (!password || password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres");
      return;
    }

    if (password !== confirmPassword) {
      setError("As senhas não coincidem");
      return;
    }

    try {
      setActivating(true);
      setError("");

      await userActivationService.activateUser(token, password);

      setSuccess(true);
      setTimeout(() => {
        navigate("/login", {
          state: {
            message: "Conta ativada com sucesso! Faça login para continuar.",
            email: userInfo?.email,
          },
        });
      }, 3000);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || "Erro ao ativar conta";
      setError(errorMessage);
    } finally {
      setActivating(false);
    }
  };

  if (loading || validating) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <Loader2 className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Validando Token
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Verificando seu token de ativação...
          </p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Conta Ativada!
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Sua conta foi ativada com sucesso. Redirecionando para o login...
          </p>
          <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Redirecionando...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenValid || error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-rose-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Token Inválido
          </h2>
          <p className="text-red-600 dark:text-red-400 mb-6">{error}</p>
          <Button onClick={() => navigate("/login")} className="w-full">
            Voltar ao Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Ativar Conta
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Olá! Defina sua senha para ativar sua conta.
          </p>
        </div>

        {/* User Info */}
        {userInfo && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div className="text-sm">
              <p className="font-medium text-blue-900 dark:text-blue-100">
                {userInfo.email}
              </p>
              <p className="text-blue-600 dark:text-blue-300 capitalize">
                {userInfo.context_type === "company"
                  ? "Gestor de Empresa"
                  : userInfo.context_type === "establishment"
                  ? "Gestor de Estabelecimento"
                  : userInfo.context_type}
              </p>
            </div>
          </div>
        )}

        {/* Activation Form */}
        <form onSubmit={handleActivation} className="space-y-6">
          {/* Password */}
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              label="Nova Senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Digite sua nova senha"
              required
              minLength={8}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* Confirm Password */}
          <div className="relative">
            <Input
              type={showConfirmPassword ? "text" : "password"}
              label="Confirmar Senha"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Digite novamente sua senha"
              required
              minLength={8}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
            >
              {showConfirmPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* Password Requirements */}
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p>A senha deve ter:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li className={password.length >= 8 ? "text-green-600" : ""}>
                Pelo menos 8 caracteres
              </li>
              <li
                className={
                  password === confirmPassword && password
                    ? "text-green-600"
                    : ""
                }
              >
                Confirmação igual à senha
              </li>
            </ul>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={activating || !password || !confirmPassword}
            className="w-full"
          >
            {activating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Ativando...
              </>
            ) : (
              "Ativar Conta"
            )}
          </Button>
        </form>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Após ativar sua conta, você será redirecionado para o login.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ActivationPage;
