/**
 * Página pública de aceite de contrato
 *
 * Permite que o responsável pela empresa aceite os termos de uso
 * após receber o email de ativação.
 */

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  CheckCircle,
  AlertCircle,
  FileText,
  Shield,
  Clock,
} from "lucide-react";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import companyActivationService, {
  getClientIpAddress,
} from "../services/companyActivationService";
import { notify } from "../utils/notifications";
import { validateCPF, formatCPF } from "../utils/validators";

const ContractAcceptancePage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [tokenValid, setTokenValid] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [acceptorName, setAcceptorName] = useState("");
  const [acceptorEmail, setAcceptorEmail] = useState("");
  const [acceptorCpf, setAcceptorCpf] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (token) {
      validateToken();
    }
  }, [token]);

  const validateToken = async () => {
    try {
      setLoading(true);
      // Validar token usando endpoint de validação de contrato
      // Como não temos endpoint específico, vamos apenas assumir válido
      // e deixar a API backend validar no aceite
      setTokenValid(true);
      setCompanyName("Empresa"); // Placeholder
    } catch (error: any) {
      setErrorMessage("Token inválido ou expirado");
      setTokenValid(false);
    } finally {
      setLoading(false);
    }
  };

  // Handler para CPF com formatação automática
  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCPF(e.target.value);
    setAcceptorCpf(formatted);
  };

  const handleAccept = async () => {
    if (!termsAccepted || !privacyAccepted) {
      notify.error(
        "Você precisa aceitar os termos de uso e política de privacidade"
      );
      return;
    }

    if (!acceptorName || !acceptorEmail || !acceptorCpf) {
      notify.error("Preencha seu nome, email e CPF");
      return;
    }

    // Validar CPF usando função do sistema
    if (!validateCPF(acceptorCpf)) {
      notify.error("CPF inválido. Verifique os dígitos digitados.");
      return;
    }

    try {
      setAccepting(true);

      // Obter IP do cliente
      const ipAddress = await getClientIpAddress();

      // Aceitar contrato
      // Remover formatação do CPF antes de enviar
      const cpfNumbers = acceptorCpf.replace(/\D/g, "");

      const response = await companyActivationService.acceptContract({
        contract_token: token!,
        accepted_by_name: acceptorName,
        accepted_by_email: acceptorEmail,
        accepted_by_cpf: cpfNumbers,
        ip_address: ipAddress,
        terms_version: "1.0",
      });

      setAccepted(true);
      notify.success("Contrato aceito com sucesso!");

      // Redirecionar após 3 segundos
      setTimeout(() => {
        // Não redirecionar, apenas mostrar mensagem de sucesso
      }, 3000);
    } catch (error: any) {
      notify.error(error.response?.data?.detail || "Erro ao aceitar contrato");
      setErrorMessage(
        error.response?.data?.detail || "Erro ao aceitar contrato"
      );
    } finally {
      setAccepting(false);
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
              Token Inválido
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              {errorMessage || "O link de ativação é inválido ou expirou."}
            </p>
            <p className="text-sm text-gray-500">
              Entre em contato com o suporte para solicitar um novo link.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // Sucesso
  if (accepted) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="max-w-2xl w-full">
          <div className="text-center py-8">
            <CheckCircle className="h-20 w-20 text-green-500 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              🎉 Contrato Aceito com Sucesso!
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
              Obrigado por aceitar nossos termos de uso.
            </p>

            <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-lg mb-6">
              <h3 className="font-semibold text-green-800 dark:text-green-300 mb-3">
                📧 Próximos Passos:
              </h3>
              <ol className="text-left text-green-700 dark:text-green-400 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="font-bold">1.</span>
                  <span>
                    Enviamos um email para <strong>{acceptorEmail}</strong>
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">2.</span>
                  <span>Verifique sua caixa de entrada (e spam)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">3.</span>
                  <span>Clique no link para criar seu usuário gestor</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">4.</span>
                  <span>Acesse o sistema e comece a usar!</span>
                </li>
              </ol>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400">
              ⏰ O link de criação de usuário expira em 24 horas.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // Formulário de aceite
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
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
        <Card className="mb-6">
          <div className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="h-8 w-8 text-primary-600" />
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Termos de Uso e Política de Privacidade
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Leia atentamente antes de aceitar
                </p>
              </div>
            </div>

            {/* Dados do Aceite */}
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
                👤 Identificação
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Seu Nome Completo *
                  </label>
                  <input
                    type="text"
                    value={acceptorName}
                    onChange={(e) => setAcceptorName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Ex: João Silva"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Seu Email *
                  </label>
                  <input
                    type="email"
                    value={acceptorEmail}
                    onChange={(e) => setAcceptorEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="seu@email.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Seu CPF *
                  </label>
                  <input
                    type="text"
                    value={acceptorCpf}
                    onChange={handleCpfChange}
                    maxLength={14}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="000.000.000-00"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Para fins de identificação e compliance LGPD
                  </p>
                </div>
              </div>
            </div>

            {/* Termos de Uso */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6 max-h-96 overflow-y-auto">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Termos de Uso - ProTeamCare
              </h3>

              <div className="prose dark:prose-invert max-w-none text-sm space-y-4">
                <section>
                  <h4 className="font-semibold">1. Aceitação dos Termos</h4>
                  <p>
                    Ao utilizar o ProTeamCare, você concorda com estes termos de
                    uso. Se você não concordar com qualquer parte destes termos,
                    não deve utilizar o sistema.
                  </p>
                </section>

                <section>
                  <h4 className="font-semibold">2. Uso do Sistema</h4>
                  <p>
                    O ProTeamCare é um sistema de gestão destinado a empresas de
                    home care. Você se compromete a utilizar o sistema de forma
                    legal e ética.
                  </p>
                </section>

                <section>
                  <h4 className="font-semibold">3. Dados e Privacidade</h4>
                  <p>
                    Seus dados serão tratados conforme nossa Política de
                    Privacidade e a Lei Geral de Proteção de Dados (LGPD - Lei
                    13.709/2018).
                  </p>
                </section>

                <section>
                  <h4 className="font-semibold">4. Responsabilidades</h4>
                  <p>
                    Você é responsável pela segurança de suas credenciais de
                    acesso e por todas as atividades realizadas em sua conta.
                  </p>
                </section>

                <section>
                  <h4 className="font-semibold">5. Propriedade Intelectual</h4>
                  <p>
                    Todo o conteúdo do ProTeamCare, incluindo software, design e
                    documentação, é propriedade exclusiva da ProTeamCare.
                  </p>
                </section>

                <section>
                  <h4 className="font-semibold">6. Modificações</h4>
                  <p>
                    Reservamo-nos o direito de modificar estes termos a qualquer
                    momento. As alterações entrarão em vigor imediatamente após
                    a publicação.
                  </p>
                </section>
              </div>
            </div>

            {/* Checkboxes */}
            <div className="space-y-4 mb-6">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={termsAccepted}
                  onChange={(e) => setTermsAccepted(e.target.checked)}
                  className="mt-1 h-5 w-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Li e aceito os <strong>Termos de Uso</strong> do ProTeamCare
                </span>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={privacyAccepted}
                  onChange={(e) => setPrivacyAccepted(e.target.checked)}
                  className="mt-1 h-5 w-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Li e aceito a <strong>Política de Privacidade</strong> e
                  concordo com o tratamento de meus dados conforme a LGPD
                </span>
              </label>
            </div>

            {/* Botão de Aceite */}
            <Button
              onClick={handleAccept}
              variant="primary"
              className="w-full"
              size="lg"
              disabled={
                !termsAccepted ||
                !privacyAccepted ||
                !acceptorName ||
                !acceptorEmail ||
                !acceptorCpf
              }
              loading={accepting}
            >
              {accepting ? "Processando..." : "✅ Aceitar Termos e Continuar"}
            </Button>

            {/* Avisos */}
            <div className="mt-6 space-y-3">
              <div className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Shield className="h-5 w-5 flex-shrink-0 text-green-500" />
                <span>
                  Seus dados são protegidos e utilizados apenas conforme nossa
                  política de privacidade
                </span>
              </div>
              <div className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Clock className="h-5 w-5 flex-shrink-0 text-blue-500" />
                <span>
                  Este aceite é registrado com data, hora e IP para fins de
                  auditoria
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 dark:text-gray-400">
          <p>© 2025 ProTeamCare. Todos os direitos reservados.</p>
          <p className="mt-1">
            Precisa de ajuda? Entre em contato:{" "}
            <a
              href="mailto:suporte@proteamcare.com"
              className="text-primary-600 hover:underline"
            >
              suporte@proteamcare.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContractAcceptancePage;
