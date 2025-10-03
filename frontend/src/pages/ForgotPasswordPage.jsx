import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import { notify } from '../utils/notifications';
import api from '../services/api';

const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email) {
      notify.error('Digite seu email');
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/api/v1/auth/forgot-password', { email });

      // Sempre mostrar mensagem genérica (segurança)
      setEmailSent(true);
    } catch (error) {
      // Não revelar se email existe ou não
      setEmailSent(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white dark:bg-gray-800 shadow-xl sm:rounded-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500 dark:text-green-400 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Email Enviado!
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                Se existe uma conta associada ao email <strong className="text-gray-900 dark:text-white">{email}</strong>,
                você receberá um link para redefinir sua senha.
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                O link expira em 1 hora. Verifique sua caixa de spam se não receber o email.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="btn-secondary inline-flex items-center"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar para Login
              </button>
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
            <Mail className="mx-auto h-12 w-12 text-blue-600 dark:text-blue-400 mb-3" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Recuperar Senha</h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Digite seu email para receber o link de recuperação
            </p>
          </div>

          {/* Formulário */}
          <div className="px-4 py-8 sm:px-10">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-900 dark:text-gray-200"
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
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                    placeholder="seu@email.com"
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
                      Enviando...
                    </>
                  ) : (
                    'Enviar Link de Recuperação'
                  )}
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 inline-flex items-center"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Voltar para Login
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
