/**
 * Aba de Ativação nos detalhes da empresa
 *
 * Exibe timeline completa do processo de ativação
 */

import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, XCircle, Mail, User, Building } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import CompanyActivationBadge from '../ui/CompanyActivationBadge';
import companyActivationService, {
  CompanyActivationStatus,
} from '../../services/companyActivationService';
import { notify } from '../../utils/notifications';

interface CompanyActivationTabProps {
  companyId: number;
  companyName: string;
}

const CompanyActivationTab: React.FC<CompanyActivationTabProps> = ({
  companyId,
  companyName,
}) => {
  const [status, setStatus] = useState<CompanyActivationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, [companyId]);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const data = await companyActivationService.getCompanyActivationStatus(companyId);
      setStatus(data);
    } catch (error: any) {
      notify.error('Erro ao carregar status de ativação');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleResendEmail = async () => {
    try {
      setActionLoading(true);
      await companyActivationService.resendContractEmail(companyId);
      notify.success('Email reenviado com sucesso!');
      loadStatus();
    } catch (error: any) {
      notify.error(error.response?.data?.detail || 'Erro ao reenviar email');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-3 text-muted-foreground">Carregando status...</span>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Não foi possível carregar o status de ativação</p>
      </div>
    );
  }

  // Timeline steps
  const timelineSteps = [
    {
      id: 'created',
      title: 'Empresa Cadastrada',
      description: `Cadastrada em ${status.days_since_creation || 0} dia(s) atrás`,
      status: 'completed',
      icon: Building,
    },
    {
      id: 'contract_sent',
      title: 'Email de Contrato Enviado',
      description: status.contract_sent
        ? `Enviado para ${status.contract_sent_to} há ${status.days_since_contract_sent || 0} dia(s)`
        : 'Aguardando envio',
      status: status.contract_sent ? 'completed' : 'pending',
      icon: Mail,
    },
    {
      id: 'contract_accepted',
      title: 'Contrato Aceito',
      description: status.contract_accepted
        ? `Aceito por ${status.contract_accepted_by} em ${new Date(status.contract_accepted_at!).toLocaleString('pt-BR')}`
        : 'Aguardando aceite do cliente',
      status: status.contract_accepted ? 'completed' : 'pending',
      icon: CheckCircle,
    },
    {
      id: 'user_created',
      title: 'Usuário Gestor Criado',
      description: status.has_active_user
        ? `Criado em ${status.activated_at ? new Date(status.activated_at).toLocaleString('pt-BR') : 'N/A'}`
        : 'Aguardando criação do usuário',
      status: status.has_active_user ? 'completed' : 'pending',
      icon: User,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Status Atual */}
      <Card title="Status Atual">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground mb-2">
              Status do Processo de Ativação
            </p>
            <CompanyActivationBadge status={status.access_status} size="lg" />
          </div>

          {status.is_overdue && (
            <div className="bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
              <p className="text-sm font-medium text-red-600 dark:text-red-400">
                ⚠️ Processo atrasado ({status.days_since_contract_sent} dias)
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Timeline */}
      <Card title="Timeline de Ativação">
        <div className="space-y-6">
          {timelineSteps.map((step, index) => {
            const Icon = step.icon;
            const isLast = index === timelineSteps.length - 1;

            return (
              <div key={step.id} className="flex gap-4">
                {/* Ícone e linha */}
                <div className="flex flex-col items-center">
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      ${
                        step.status === 'completed'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-400'
                      }
                    `}
                  >
                    {step.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <Clock className="h-5 w-5" />
                    )}
                  </div>
                  {!isLast && (
                    <div
                      className={`
                        w-0.5 h-12 my-1
                        ${step.status === 'completed' ? 'bg-green-200 dark:bg-green-800' : 'bg-gray-200 dark:bg-gray-700'}
                      `}
                    />
                  )}
                </div>

                {/* Conteúdo */}
                <div className="flex-1 pb-6">
                  <h4
                    className={`
                      font-medium
                      ${step.status === 'completed' ? 'text-foreground' : 'text-muted-foreground'}
                    `}
                  >
                    {step.title}
                  </h4>
                  <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Ações */}
      <Card title="Ações">
        <div className="space-y-4">
          {status.access_status === 'pending_contract' && !status.contract_sent && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
              <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
                📧 Empresa aguardando envio de email de ativação
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  window.location.href = `/admin/empresas`;
                }}
              >
                Ir para Lista e Enviar Email
              </Button>
            </div>
          )}

          {status.access_status === 'pending_contract' && status.contract_sent && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-300 mb-3">
                ⏳ Aguardando cliente aceitar o contrato
              </p>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleResendEmail}
                disabled={actionLoading}
                loading={actionLoading}
              >
                Reenviar Email de Contrato
              </Button>
            </div>
          )}

          {status.access_status === 'contract_signed' && (
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <p className="text-sm text-green-800 dark:text-green-300">
                ✅ Contrato aceito! Email de criação de usuário já foi enviado automaticamente.
              </p>
            </div>
          )}

          {status.access_status === 'pending_user' && (
            <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
              <p className="text-sm text-orange-800 dark:text-orange-300">
                👤 Aguardando cliente criar usuário gestor
              </p>
            </div>
          )}

          {status.access_status === 'active' && (
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <p className="text-sm text-green-800 dark:text-green-300">
                🎉 Empresa totalmente ativada e funcional!
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Informações de Compliance */}
      {status.contract_accepted && (
        <Card title="Registro de Aceite (Compliance)">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Aceito por:</p>
              <p className="font-medium">{status.contract_accepted_by}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Data/Hora:</p>
              <p className="font-medium">
                {new Date(status.contract_accepted_at!).toLocaleString('pt-BR')}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Versão dos Termos:</p>
              <p className="font-medium">{status.contract_terms_version || 'N/A'}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default CompanyActivationTab;
