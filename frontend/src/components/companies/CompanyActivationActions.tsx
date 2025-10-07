/**
 * Componente de ações de ativação para empresas
 *
 * Exibe botões de ação baseados no status de ativação da empresa
 */

import React, { useState } from "react";
import { Mail, RefreshCw, Eye, CheckCircle } from "lucide-react";
import Button from "../ui/Button";
import companyActivationService, {
  canSendContractEmail,
  canResendEmail,
} from "../../services/companyActivationService";
import { notify } from "../../utils/notifications";

interface CompanyActivationActionsProps {
  company: {
    id: number;
    name: string;
    access_status?: string;
    activation_sent_to?: string;
  };
  onActionComplete?: () => void;
}

const CompanyActivationActions: React.FC<CompanyActivationActionsProps> = ({
  company,
  onActionComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState(
    company.activation_sent_to || ""
  );
  const [recipientName, setRecipientName] = useState("");

  const status = company.access_status || "pending_contract";

  const handleSendContractEmail = async () => {
    if (!recipientEmail || !recipientName) {
      notify.error("Preencha o email e nome do destinatário");
      return;
    }

    try {
      setLoading(true);
      await companyActivationService.sendContractEmail({
        company_id: company.id,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
      });

      notify.success("Email de ativação enviado com sucesso!");
      setShowEmailModal(false);
      onActionComplete?.();
    } catch (error: any) {
      notify.error(error.response?.data?.detail || "Erro ao enviar email");
    } finally {
      setLoading(false);
    }
  };

  const handleResendEmail = async () => {
    try {
      setLoading(true);
      await companyActivationService.resendContractEmail(company.id);
      notify.success("Email reenviado com sucesso!");
      onActionComplete?.();
    } catch (error: any) {
      notify.error(error.response?.data?.detail || "Erro ao reenviar email");
    } finally {
      setLoading(false);
    }
  };

  const handleViewStatus = () => {
    // Navegar para detalhes da empresa, aba ativação
    window.location.href = `/admin/empresas/${company.id}?tab=ativacao`;
  };

  // Modal de envio de email
  const EmailModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Enviar Email de Ativação
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nome do Destinatário *
            </label>
            <input
              type="text"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Ex: João Silva"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email do Destinatário *
            </label>
            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="gestor@empresa.com.br"
            />
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              📧 O destinatário receberá um email com link para aceitar os
              termos de uso do sistema. O link expira em 7 dias.
            </p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <Button
            onClick={() => setShowEmailModal(false)}
            variant="secondary"
            className="flex-1"
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleSendContractEmail}
            variant="primary"
            className="flex-1"
            disabled={loading}
            loading={loading}
          >
            {loading ? "Enviando..." : "Enviar Email"}
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="flex gap-2 items-center">
        {/* Botão: Enviar Email de Ativação */}
        {canSendContractEmail(status) && (
          <Button
            size="sm"
            variant="primary"
            onClick={() => setShowEmailModal(true)}
            icon={<Mail className="h-4 w-4" />}
            disabled={loading}
          >
            <span className="hidden sm:inline">Enviar Ativação</span>
            <span className="sm:hidden">Enviar</span>
          </Button>
        )}

        {/* Botão: Reenviar Email */}
        {canResendEmail(status) && company.activation_sent_to && (
          <Button
            size="sm"
            variant="secondary"
            onClick={handleResendEmail}
            icon={<RefreshCw className="h-4 w-4" />}
            disabled={loading}
          >
            <span className="hidden sm:inline">Reenviar</span>
          </Button>
        )}

        {/* Botão: Ver Status */}
        <Button
          size="sm"
          variant="secondary"
          outline
          onClick={handleViewStatus}
          icon={<Eye className="h-4 w-4" />}
        >
          <span className="hidden sm:inline">Status</span>
        </Button>
      </div>

      {/* Modal de envio de email */}
      {showEmailModal && <EmailModal />}
    </>
  );
};

export default CompanyActivationActions;
