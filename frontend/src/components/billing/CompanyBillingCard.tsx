import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';
import { notify } from '../../utils/notifications';
import {
  CreditCard,
  Calendar,
  DollarSign,
  FileText,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { B2BBillingService } from '../../services/b2bBillingService';
import type { CompanyBillingCardProps, CompanySubscription, ProTeamCareInvoice } from '../../types/b2b-billing.types';

const CompanyBillingCard: React.FC<CompanyBillingCardProps> = ({
  company,
  subscription: initialSubscription,
  onCreateSubscription,
  onManageSubscription,
  onCreateInvoice,
}) => {
  const [subscription, setSubscription] = useState<CompanySubscription | null>(initialSubscription || null);
  const [recentInvoices, setRecentInvoices] = useState<ProTeamCareInvoice[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!initialSubscription) {
      loadSubscriptionData();
    }
  }, [company.id, initialSubscription]);

  // Recarregar dados quando o componente é re-montado ou company.id muda
  useEffect(() => {
    loadSubscriptionData();
  }, [company.id]);

  useEffect(() => {
    if (subscription) {
      loadRecentInvoices();
    }
  }, [subscription]);

  const loadSubscriptionData = async () => {
    try {
      setLoading(true);
      const subscriptionData = await B2BBillingService.getCompanySubscription(company.id);
      console.log('🔍 CompanyBillingCard - Subscription carregada:', subscriptionData);
      setSubscription(subscriptionData);
    } catch (err: any) {
      notify.error('Erro ao carregar dados da assinatura');
      console.error('Erro ao carregar assinatura:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRecentInvoices = async () => {
    if (!subscription) return;

    try {
      const invoices = await B2BBillingService.getCompanyInvoices(company.id, undefined, 5);
      setRecentInvoices(invoices);
    } catch (err: any) {
      console.error('Erro ao carregar faturas:', err);
    }
  };

  const handleCreateCheckout = async (invoice: ProTeamCareInvoice) => {
    try {
      setLoading(true);
      const checkoutResponse = await B2BBillingService.createCheckoutSession(invoice.id);

      if (checkoutResponse.success && checkoutResponse.checkout_url) {
        // Check if it's a mock URL
        if (checkoutResponse.checkout_url.includes('mock-pagbank.proteamcare.com')) {
          const amount = typeof invoice.amount === 'string' ? parseFloat(invoice.amount) : invoice.amount;
          notify.info(
            `Checkout criado em modo demonstração. Fatura: ${invoice.invoice_number} • Valor: R$ ${amount.toFixed(2)}`,
            { duration: 5000 }
          );
        } else {
          window.open(checkoutResponse.checkout_url, '_blank', 'noopener,noreferrer');
        }
      }
    } catch (err: any) {
      notify.error('Erro ao criar checkout: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getNextBillingDate = (): string => {
    if (!subscription) return 'N/A';
    const nextBilling = B2BBillingService.calculateNextBillingDate(subscription);
    return B2BBillingService.formatDate(nextBilling.toISOString());
  };

  const getOverdueAmount = (): number => {
    return recentInvoices
      .filter(invoice => B2BBillingService.isOverdue(invoice))
      .reduce((total, invoice) => {
        const amount = typeof invoice.amount === 'string' ? parseFloat(invoice.amount) : invoice.amount;
        return total + amount;
      }, 0);
  };

  const getPendingInvoicesCount = (): number => {
    return recentInvoices.filter(invoice => invoice.status === 'pending').length;
  };

  if (loading && !subscription) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Carregando dados de cobrança...</p>
          </div>
        </div>
      </Card>
    );
  }


  // Empresa sem assinatura
  if (!subscription) {
    return (
      <Card className="border-dashed border-2 border-gray-300">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-card-foreground flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-gray-500" />
            {company.name}
          </h3>
        </div>
        <div className="px-6 py-4 text-center space-y-4">
          <div className="text-gray-500">
            <p className="text-lg font-medium">Sem assinatura ativa</p>
            <p className="text-sm">Esta empresa ainda não possui um plano Pro Team Care</p>
          </div>
          <Button onClick={() => onCreateSubscription?.(company.id)} className="w-full">
            <CreditCard className="mr-2 h-4 w-4" />
            Criar Assinatura
          </Button>
        </div>
      </Card>
    );
  }

  const overdueAmount = getOverdueAmount();
  const pendingCount = getPendingInvoicesCount();

  return (
    <Card className="test">
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-card-foreground flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-blue-600" />
              {company.name}
            </h3>
          </div>
          <Badge className={B2BBillingService.getStatusColor(subscription.status)}>
            {B2BBillingService.getStatusLabel(subscription.status)}
          </Badge>
        </div>
      </div>
      <div className="px-6 py-4 space-y-4">
        {/* Informações da Assinatura */}
        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <span className="text-sm text-gray-600">Plano</span>
            <p className="font-medium">{subscription.plan?.name || 'Plano não identificado'}</p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Valor Mensal</span>
            <p className="font-medium text-green-600">
              {subscription.plan ? B2BBillingService.formatCurrency(subscription.plan.monthly_price) : 'N/A'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Próxima Cobrança</span>
            <p className="font-medium flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {getNextBillingDate()}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-600">Método</span>
            <p className="font-medium">
              {subscription.payment_method === 'recurrent' ? 'Automático' : 'Manual'}
            </p>
          </div>
        </div>

        {/* Alertas */}
        {overdueAmount > 0 && (
          <Alert type="error">
            <strong>Atenção:</strong> Existe valor em atraso de{' '}
            <span className="font-bold">{B2BBillingService.formatCurrency(overdueAmount)}</span>
          </Alert>
        )}

        {pendingCount > 0 && overdueAmount === 0 && (
          <Alert type="warning">
            {pendingCount} fatura{pendingCount > 1 ? 's' : ''} pendente{pendingCount > 1 ? 's' : ''} de pagamento
          </Alert>
        )}

        {/* Faturas Recentes */}
        {recentInvoices.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Faturas Recentes
            </h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {recentInvoices.slice(0, 3).map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-2 bg-white rounded border">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{invoice.invoice_number}</span>
                      <Badge size="sm" className={B2BBillingService.getStatusColor(invoice.status)}>
                        {B2BBillingService.getStatusLabel(invoice.status)}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-600">
                      Venc: {B2BBillingService.formatDate(invoice.due_date)} •{' '}
                      {B2BBillingService.formatCurrency(invoice.amount)}
                    </div>
                  </div>
                  {invoice.status === 'pending' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleCreateCheckout(invoice)}
                      disabled={loading}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ações */}
        <div className="flex gap-2 pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              console.log('🔍 CompanyBillingCard - Chamando onManageSubscription com:', subscription);
              onManageSubscription?.(subscription);
            }}
            className="flex-1"
          >
            <Settings className="mr-2 h-4 w-4" />
            Gerenciar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onCreateInvoice?.(company.id, subscription)}
            className="flex-1"
          >
            <DollarSign className="mr-2 h-4 w-4" />
            Nova Fatura
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default CompanyBillingCard;
