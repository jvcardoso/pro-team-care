import React, { useState, useEffect, useCallback } from 'react';
import Card from '../ui/Card';
import { CreditCard, Calendar, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { B2BBillingService } from '../../services/b2bBillingService';
import type { CompanySubscription, ProTeamCareInvoice } from '../../types/b2b-billing.types';

interface BillingInfoCardProps {
  companyId: number;
}

const BillingInfoCard: React.FC<BillingInfoCardProps> = ({ companyId }) => {
  const [subscription, setSubscription] = useState<CompanySubscription | null>(null);
  const [lastInvoice, setLastInvoice] = useState<ProTeamCareInvoice | null>(null);
  const [lastPaidInvoice, setLastPaidInvoice] = useState<ProTeamCareInvoice | null>(null);
  const [loading, setLoading] = useState(true);

  const loadBillingData = useCallback(async () => {
    try {
      setLoading(true);

      // Carregar subscription
      const subscriptionData = await B2BBillingService.getCompanySubscription(companyId);
      setSubscription(subscriptionData);

      // Carregar última fatura (qualquer status)
      const allInvoices = await B2BBillingService.getCompanyInvoices(companyId, undefined, 1);
      if (allInvoices.length > 0) {
        setLastInvoice(allInvoices[0]);
      }

      // Carregar última fatura paga
      const paidInvoices = await B2BBillingService.getCompanyInvoices(companyId, 'paid', 1);
      if (paidInvoices.length > 0) {
        setLastPaidInvoice(paidInvoices[0]);
      }
    } catch (err) {
      console.error('Erro ao carregar dados de faturamento:', err);
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    loadBillingData();
  }, [loadBillingData]);

  // Calcular próxima data de faturamento
  const getNextBillingDate = (): string => {
    if (!subscription) return 'N/A';
    const nextDate = B2BBillingService.calculateNextBillingDate(subscription);
    return nextDate.toLocaleDateString("pt-BR");
  };

  // Obter data do último faturamento (paid_at da última fatura paga)
  const getLastBillingDate = (): string => {
    if (lastPaidInvoice?.paid_at) {
      return new Date(lastPaidInvoice.paid_at).toLocaleDateString("pt-BR");
    }
    if (lastInvoice?.created_at) {
      return new Date(lastInvoice.created_at).toLocaleDateString("pt-BR");
    }
    return 'N/A';
  };

  // Status da última fatura
  const getLastInvoiceStatus = () => {
    if (!lastInvoice) return { label: 'N/A', color: 'text-gray-500', icon: Clock };

    const statusMap = {
      paid: { label: 'Pago', color: 'text-green-600', icon: CheckCircle },
      pending: { label: 'Pendente', color: 'text-yellow-600', icon: Clock },
      overdue: { label: 'Vencido', color: 'text-red-600', icon: AlertTriangle },
      cancelled: { label: 'Cancelado', color: 'text-gray-600', icon: Clock },
    };

    return statusMap[lastInvoice.status] || statusMap.pending;
  };

  if (loading) {
    return (
      <Card title="Faturamento">
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  if (!subscription) {
    return (
      <Card title="Faturamento">
        <div className="text-center py-6">
          <CreditCard className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">Sem assinatura ativa</p>
        </div>
      </Card>
    );
  }

  const statusInfo = getLastInvoiceStatus();
  const StatusIcon = statusInfo.icon;

  return (
    <Card title="Faturamento">
      <div className="space-y-4 text-sm">
        {/* Plano Atual */}
        <div>
          <div className="block text-muted-foreground mb-1">Plano Atual</div>
          <p className="text-foreground font-medium">
            {subscription.plan?.name || 'N/A'}
          </p>
        </div>

        {/* Dia do Faturamento */}
        <div>
          <div className="block text-muted-foreground mb-1">Dia do Faturamento</div>
          <p className="text-foreground">Dia {subscription.billing_day}</p>
        </div>

        {/* Data do Último Faturamento */}
        <div>
          <div className="block text-muted-foreground mb-1">Último Faturamento</div>
          <p className="text-foreground flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {getLastBillingDate()}
          </p>
        </div>

        {/* Status do Último Faturamento */}
        <div>
          <div className="block text-muted-foreground mb-1">Status</div>
          <p className={`flex items-center gap-1 font-medium ${statusInfo.color}`}>
            <StatusIcon className="h-4 w-4" />
            {statusInfo.label}
          </p>
        </div>

        {/* Próxima Cobrança */}
        <div>
          <div className="block text-muted-foreground mb-1">Próxima Cobrança</div>
          <p className="text-foreground flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {getNextBillingDate()}
          </p>
        </div>
      </div>
    </Card>
  );
};

export default BillingInfoCard;
