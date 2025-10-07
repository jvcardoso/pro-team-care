/**
 * Página pública de criação de usuário gestor
 *
 * Permite que o responsável crie seu usuário após aceitar o contrato
 */

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  CheckCircle,
  AlertCircle,
  User,
  Lock,
  Mail,
  Eye,
  EyeOff,
} from "lucide-react";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import companyActivationService from "../services/companyActivationService";
import { notify } from "../utils/notifications";

const CreateManagerPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenExpired, setTokenExpired] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [userCreated, setUserCreated] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Form fields
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Password validation
  const [passwordValidation, setPasswordValidation] = useState({
    minLength: false,
    hasUpperCase: false,
    hasLowerCase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });

  useEffect(() => {
    if (token) {
      validateToken();
    }
  }, [token]);

  useEffect(() => {
    // Validar senha em tempo real
    setPasswordValidation({
      minLength: password.length >= 8,
      hasUpperCase: /[A-Z]/.test(password),
      hasLowerCase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    });
  }, [password]);

  const validateToken = async () => {
    try {
      setLoading(true);
      const response = await companyActivationService.validateUserCreationToken(
        token!
      );

      if (response.valid) {
        setTokenValid(true);
        setCompanyName(response.company_name || "Empresa");
      } else {
        setTokenValid(false);
        setTokenExpired(response.expired);
        setErrorMessage(response.error_message || "Token inválido");
      }
    } catch (error: any) {
      setTokenValid(false);
      setErrorMessage("Erro ao validar token");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    // Validações
    if (!userName || !userEmail || !password || !confirmPassword) {
      notify.error("Preencha todos os campos");
      return;
    }

    if (password !== confirmPassword) {
      notify.error("As senhas não coincidem");
      return;
    }

    const isPasswordValid = Object.values(passwordValidation).every((v) => v);
    if (!isPasswordValid) {
      notify.error("A senha não atende aos requisitos de segurança");
      return;
    }

    try {
      setCreating(true);

      await companyActivationService.createManagerUser({
        token: token!,
        user_name: userName,
        user_email: userEmail,
        password: password,
      });

      setUserCreated(true);
      notify.success("Usuário criado com sucesso!");

      // Redirecionar para login após 3 segundos
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (error: any) {
      notify.error(error.response?.data?.detail || "Erro ao criar usuário");
      setErrorMessage(error.response?.data?.detail || "Erro ao criar usuário");
    } finally {
      setCreating(false);
    }
  };

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Token inválido
  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <div className="text-center py-8">
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {tokenExpired ? "Token Expirado" : "Token Inválido"}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {errorMessage ||
                "O link de criação de usuário é inválido ou expirou (24 horas)."}
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Entre em contato com o suporte para solicitar um novo link.
            </p>
            <Button variant="primary" onClick={() => navigate("/")}>
              Ir para Página Inicial
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Sucesso
  if (userCreated) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="max-w-2xl w-full">
          <div className="text-center py-8">
            <CheckCircle className="h-20 w-20 text-green-500 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              🎉 Conta Criada com Sucesso!
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
              Sua empresa <strong>{companyName}</strong> foi ativada!
            </p>

            <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg mb-6">
              <h3 className="font-semibold text-green-800 dark:text-green-300 mb-3">
                ✅ Tudo Pronto!
              </h3>
              <div className="text-left text-green-700 dark:text-green-400 space-y-2">
                <p>
                  ✓ Usuário gestor criado: <strong>{userName}</strong>
                </p>
                <p>
                  ✓ Email: <strong>{userEmail}</strong>
                </p>
                <p>✓ Empresa totalmente ativada</p>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg mb-6">
              <h3 className="font-semibold text-blue-800 dark:text-blue-300 mb-3">
                🚀 Próximos Passos:
              </h3>
              <ol className="text-left text-blue-700 dark:text-blue-400 space-y-2">
                <li>1. Faça login com seu email e senha</li>
                <li>2. Configure uma assinatura para sua empresa</li>
                <li>3. Cadastre estabelecimentos e clientes</li>
                <li>4. Comece a usar o sistema!</li>
              </ol>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
              Você será redirecionado para a página de login em alguns
              segundos...
            </p>

            <Button variant="primary" onClick={() => navigate("/login")}>
              Ir para Login Agora
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Formulário de criação
  const isPasswordStrong = Object.values(passwordValidation).every((v) => v);
  const passwordsMatch =
    password && confirmPassword && password === confirmPassword;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            ProTeamCare
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Sistema de Gestão para Empresas de Home Care
          </p>
        </div>

        {/* Main Card */}
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <User className="h-8 w-8 text-primary-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Criar Usuário Gestor
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Empresa: <strong>{companyName}</strong>
                </p>
              </div>
            </div>

            {/* Success Banner */}
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg mb-6">
              <p className="text-sm text-green-800 dark:text-green-300">
                ✅ Contrato aceito! Agora crie seu usuário gestor para acessar o
                sistema.
              </p>
            </div>

            {/* Form */}
            <div className="space-y-4">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome Completo *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Ex: João Silva"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="email"
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="seu@email.com"
                  />
                </div>
              </div>

              {/* Senha */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Senha *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>

                {/* Password validation */}
                {password && (
                  <div className="mt-2 space-y-1">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      Requisitos da senha:
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div
                        className={
                          passwordValidation.minLength
                            ? "text-green-600"
                            : "text-gray-400"
                        }
                      >
                        {passwordValidation.minLength ? "✓" : "○"} Mínimo 8
                        caracteres
                      </div>
                      <div
                        className={
                          passwordValidation.hasUpperCase
                            ? "text-green-600"
                            : "text-gray-400"
                        }
                      >
                        {passwordValidation.hasUpperCase ? "✓" : "○"} Letra
                        maiúscula
                      </div>
                      <div
                        className={
                          passwordValidation.hasLowerCase
                            ? "text-green-600"
                            : "text-gray-400"
                        }
                      >
                        {passwordValidation.hasLowerCase ? "✓" : "○"} Letra
                        minúscula
                      </div>
                      <div
                        className={
                          passwordValidation.hasNumber
                            ? "text-green-600"
                            : "text-gray-400"
                        }
                      >
                        {passwordValidation.hasNumber ? "✓" : "○"} Número
                      </div>
                      <div
                        className={
                          passwordValidation.hasSpecialChar
                            ? "text-green-600"
                            : "text-gray-400"
                        }
                      >
                        {passwordValidation.hasSpecialChar ? "✓" : "○"}{" "}
                        Caractere especial
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Confirmar Senha */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Confirmar Senha *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>

                {confirmPassword && (
                  <p
                    className={`mt-1 text-xs ${
                      passwordsMatch ? "text-green-600" : "text-red-600"
                    }`}
                  >
                    {passwordsMatch
                      ? "✓ Senhas conferem"
                      : "✗ As senhas não conferem"}
                  </p>
                )}
              </div>
            </div>

            {/* Botão */}
            <Button
              onClick={handleCreateUser}
              variant="primary"
              className="w-full mt-6"
              size="lg"
              disabled={
                !userName ||
                !userEmail ||
                !password ||
                !confirmPassword ||
                !isPasswordStrong ||
                !passwordsMatch
              }
              loading={creating}
            >
              {creating
                ? "Criando Usuário..."
                : "👤 Criar Usuário e Ativar Empresa"}
            </Button>

            {/* Info */}
            <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                💡 <strong>Dica:</strong> Use uma senha forte e guarde-a em
                local seguro. Você precisará dela para acessar o sistema.
              </p>
            </div>
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-8">
          <p>© 2025 ProTeamCare. Todos os direitos reservados.</p>
        </div>
      </div>
    </div>
  );
};

export default CreateManagerPage;
