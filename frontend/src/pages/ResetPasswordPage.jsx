import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Lock, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { notify } from '../utils/notifications';
import api from '../services/api';

const ResetPasswordPage = () => {
  const { token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [validatingToken, setValidatingToken] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [passwordReset, setPasswordReset] = useState(false);

  // Requisitos de senha
  const [passwordStrength, setPasswordStrength] = useState({
    minLength: false,
    hasUpperCase: false,
    hasLowerCase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });

  useEffect(() => {
    validateToken();
  }, [token]);

  useEffect(() => {
    checkPasswordStrength(password);
  }, [password]);

  const validateToken = async () => {
    try {
      setValidatingToken(true);
      await api.post('/api/v1/auth/validate-reset-token', { token });
      setTokenValid(true);
    } catch (error) {
      setTokenValid(false);
      notify.error('Link inválido ou expirado');
    } finally {
      setValidatingToken(false);
    }
  };

  const checkPasswordStrength = (pwd) => {
    setPasswordStrength({
      minLength: pwd.length >= 8,
      hasUpperCase: /[A-Z]/.test(pwd),
      hasLowerCase: /[a-z]/.test(pwd),
      hasNumber: /[0-9]/.test(pwd),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(pwd),
    });
  };

  const isPasswordValid = () => {
    return Object.values(passwordStrength).every((val) => val === true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isPasswordValid()) {
      notify.error('A senha não atende aos requisitos mínimos');
      return;
    }

    if (password !== confirmPassword) {
      notify.error('As senhas não coincidem');
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/api/v1/auth/reset-password', {
        token,
        new_password: password,
      });

      setPasswordReset(true);
      notify.success('Senha redefinida com sucesso!');

      // Redirecionar após 3 segundos
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error) {
      notify.error(error.response?.data?.detail || 'Erro ao redefinir senha');
    } finally {
      setIsLoading(false);
    }
  };

  if (validatingToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <span className="loading-spinner mx-auto mb-4"></span>
          <p className="text-gray-600 dark:text-gray-300">Validando link...</p>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white dark:bg-gray-800 shadow-xl sm:rounded-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center">
              <AlertCircle className="mx-auto h-16 w-16 text-red-500 dark:text-red-400 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Link Inválido
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Este link de recuperação é inválido ou já expirou.
              </p>
              <button
                onClick={() => navigate('/forgot-password')}
                className="btn-primary"
              >
                Solicitar Novo Link
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (passwordReset) {
    return (
      <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white dark:bg-gray-800 shadow-xl sm:rounded-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500 dark:text-green-400 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Senha Redefinida!
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Sua senha foi alterada com sucesso. Você será redirecionado para o login...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-gray-800 shadow-xl sm:rounded-lg border border-gray-200 dark:border-gray-700">
          {/* Cabeçalho */}
          <div className="px-4 py-6 sm:px-10 text-center border-b border-gray-200 dark:border-gray-700">
            <Lock className="mx-auto h-12 w-12 text-blue-600 dark:text-blue-400 mb-3" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Redefinir Senha</h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Digite sua nova senha
            </p>
          </div>

          {/* Formulário */}
          <div className="px-4 py-8 sm:px-10">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Nova Senha */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-900 dark:text-gray-200"
                >
                  Nova Senha
                </label>
                <div className="mt-1 relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white pr-10 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
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
              </div>

              {/* Confirmar Senha */}
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium text-gray-900 dark:text-gray-200"
                >
                  Confirmar Senha
                </label>
                <div className="mt-1 relative">
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white pr-10 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
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
              </div>

              {/* Requisitos de Senha */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-4">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Requisitos da senha:
                </p>
                <ul className="space-y-1 text-sm">
                  <li className={passwordStrength.minLength ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {passwordStrength.minLength ? '✓' : '○'} Mínimo de 8 caracteres
                  </li>
                  <li className={passwordStrength.hasUpperCase ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {passwordStrength.hasUpperCase ? '✓' : '○'} Uma letra maiúscula
                  </li>
                  <li className={passwordStrength.hasLowerCase ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {passwordStrength.hasLowerCase ? '✓' : '○'} Uma letra minúscula
                  </li>
                  <li className={passwordStrength.hasNumber ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {passwordStrength.hasNumber ? '✓' : '○'} Um número
                  </li>
                  <li className={passwordStrength.hasSpecialChar ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                    {passwordStrength.hasSpecialChar ? '✓' : '○'} Um caractere especial (!@#$%^&*...)
                  </li>
                </ul>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading || !isPasswordValid()}
                  className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="loading-spinner mr-2"></span>
                      Redefinindo...
                    </>
                  ) : (
                    'Redefinir Senha'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
