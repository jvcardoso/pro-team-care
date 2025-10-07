import React, { useState, useEffect } from "react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import { Alert } from "../ui/Alert";
import { notify } from "../../utils/notifications";
import {
  Building,
  CreditCard,
  Calendar,
  Settings,
  X,
  CheckCircle,
  AlertTriangle,
  Info,
} from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import { httpCache } from "../../services/httpCache";
import type {
  CompanySubscription,
  SubscriptionPlan,
  CreateSubscriptionRequest,
} from "../../types/b2b-billing.types";

interface SubscriptionManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  company: {
    id: number;
    name: string;
    tax_id?: string;
  };
  subscription?: CompanySubscription | null;
  onSuccess: () => void;
}

const SubscriptionManagementModal: React.FC<
  SubscriptionManagementModalProps
> = ({ isOpen, onClose, company, subscription, onSuccess }) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<number>(
    subscription?.plan_id || 0
  );
  const [billingDay, setBillingDay] = useState<number>(
    subscription?.billing_day || 1
  );
  const [paymentMethod, setPaymentMethod] = useState<"manual" | "recurrent">(
    subscription?.payment_method || "manual"
  );
  const [autoRenew, setAutoRenew] = useState<boolean>(
    subscription?.auto_renew || true
  );
  const [loading, setLoading] = useState(false);

  const isEditing = !!subscription;

  useEffect(() => {
    if (isOpen) {
      loadPlans();
    }
  }, [isOpen]);

  // Reinicializar valores quando subscription mudar
  useEffect(() => {
    console.log("🔍 SubscriptionModal - Subscription recebida:", subscription);
    if (subscription) {
      console.log("🔍 SubscriptionModal - Plan ID:", subscription.plan_id);
      console.log(
        "🔍 SubscriptionModal - Billing Day:",
        subscription.billing_day
      );
      console.log(
        "🔍 SubscriptionModal - Payment Method:",
        subscription.payment_method
      );
      console.log(
        "🔍 SubscriptionModal - Auto Renew:",
        subscription.auto_renew
      );

      setSelectedPlanId(subscription.plan_id || 0);
      setBillingDay(subscription.billing_day || 1);
      setPaymentMethod(subscription.payment_method || "manual");
      setAutoRenew(
        subscription.auto_renew !== undefined ? subscription.auto_renew : true
      );
    }
  }, [subscription]);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const availablePlans = await B2BBillingService.getSubscriptionPlans(true);
      console.log("🔍 SubscriptionModal - Planos carregados:", availablePlans);
      setPlans(availablePlans);

      // Se há subscription, garantir que o plano correto seja selecionado
      if (subscription && subscription.plan_id) {
        console.log(
          "🔍 SubscriptionModal - Definindo selectedPlanId para:",
          subscription.plan_id
        );
        setSelectedPlanId(subscription.plan_id);
      } else if (!selectedPlanId && availablePlans.length > 0) {
        // Se não há plano selecionado e há planos disponíveis, selecionar o primeiro
        console.log(
          "🔍 SubscriptionModal - Selecionando primeiro plano:",
          availablePlans[0].id
        );
        setSelectedPlanId(availablePlans[0].id);
      }
    } catch (err: any) {
      notify.error("Erro ao carregar planos disponíveis: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedPlanId) {
      notify.error("Por favor, selecione um plano");
      return;
    }

    if (billingDay < 1 || billingDay > 31) {
      notify.error("Dia de cobrança deve estar entre 1 e 31");
      return;
    }

    try {
      setLoading(true);

      if (isEditing && subscription) {
        // Atualizar assinatura existente
        const updateData: Partial<CompanySubscription> = {
          plan_id: selectedPlanId,
          billing_day: billingDay,
          payment_method: paymentMethod,
          auto_renew: autoRenew,
        };

        await B2BBillingService.updateCompanySubscription(
          subscription.id,
          updateData
        );

        // Invalidar cache relacionado à subscription
        httpCache.invalidatePattern(
          `/api/v1/b2b-billing/subscriptions/company/${company.id}`
        );
        httpCache.invalidatePattern(
          `/api/v1/b2b-billing/invoices/company/${company.id}`
        );

        notify.success("Assinatura atualizada com sucesso!");
      } else {
        // Criar nova assinatura
        const createData: CreateSubscriptionRequest = {
          company_id: company.id,
          plan_id: selectedPlanId,
          start_date: new Date().toISOString().split("T")[0], // Hoje
          billing_day: billingDay,
          payment_method: paymentMethod,
          auto_renew: autoRenew,
        };

        await B2BBillingService.createCompanySubscription(createData);

        // Invalidar cache relacionado à subscription
        httpCache.invalidatePattern(
          `/api/v1/b2b-billing/subscriptions/company/${company.id}`
        );
        httpCache.invalidatePattern(
          `/api/v1/b2b-billing/invoices/company/${company.id}`
        );

        notify.success("Assinatura criada com sucesso!");
      }

      // Fechar modal após sucesso
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err: any) {
      notify.error(
        `Erro ao ${isEditing ? "atualizar" : "criar"} assinatura: ` +
          err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const selectedPlan = plans.find((plan) => plan.id === selectedPlanId);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <Building className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                {isEditing ? "Gerenciar Assinatura" : "Criar Assinatura"}
              </h2>
              <p className="text-sm text-muted-foreground">{company.name}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={loading}
            icon={<X className="h-4 w-4" />}
          />
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Seleção de Plano */}
          <Card
            title="Plano de Assinatura"
            icon={<CreditCard className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Plano *
                </label>
                <select
                  value={selectedPlanId}
                  onChange={(e) => setSelectedPlanId(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                  disabled={loading}
                >
                  <option value={0}>Selecione um plano</option>
                  {plans.map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} -{" "}
                      {B2BBillingService.formatCurrency(plan.monthly_price)}/mês
                    </option>
                  ))}
                </select>
              </div>

              {/* Detalhes do Plano Selecionado */}
              {selectedPlan && (
                <div className="p-4 bg-muted rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">
                      {selectedPlan.name}
                    </span>
                    <span className="text-lg font-bold text-green-600 dark:text-green-400">
                      {B2BBillingService.formatCurrency(
                        selectedPlan.monthly_price
                      )}
                      /mês
                    </span>
                  </div>
                  {selectedPlan.description && (
                    <p className="text-sm text-muted-foreground">
                      {selectedPlan.description}
                    </p>
                  )}

                  {/* Recursos do Plano */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-foreground">
                      Recursos inclusos:
                    </h4>
                    <ul className="space-y-1">
                      {B2BBillingService.getPlanFeaturesList(selectedPlan).map(
                        (feature, index) => (
                          <li
                            key={index}
                            className="text-sm text-muted-foreground flex items-center gap-2"
                          >
                            <CheckCircle className="h-3 w-3 text-green-500 dark:text-green-400 flex-shrink-0" />
                            {feature}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Configurações de Cobrança */}
          <Card
            title="Configurações de Cobrança"
            icon={<Settings className="h-5 w-5" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Dia de Cobrança *
                </label>
                <Input
                  type="number"
                  min={1}
                  max={31}
                  value={billingDay}
                  onChange={(e) => setBillingDay(Number(e.target.value))}
                  placeholder="1-31"
                  disabled={loading}
                  icon={<Calendar className="h-4 w-4" />}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Dia do mês em que a cobrança será processada
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Método de Pagamento
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) =>
                    setPaymentMethod(e.target.value as "manual" | "recurrent")
                  }
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                  disabled={loading}
                >
                  <option value="manual">Manual</option>
                  <option value="recurrent">Automático</option>
                </select>
                <p className="text-xs text-muted-foreground mt-1">
                  {paymentMethod === "manual"
                    ? "Faturas serão criadas para pagamento manual"
                    : "Cobrança automática via cartão/PIX"}
                </p>
              </div>
            </div>

            <div className="mt-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoRenew}
                  onChange={(e) => setAutoRenew(e.target.checked)}
                  disabled={loading}
                  className="rounded border-border text-primary focus:ring-ring"
                />
                <span className="text-sm text-foreground">
                  Renovação automática
                </span>
              </label>
              <p className="text-xs text-muted-foreground mt-1">
                Assinatura será renovada automaticamente ao final do período
              </p>
            </div>
          </Card>

          {/* Resumo da Próxima Cobrança */}
          {selectedPlan && (
            <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Resumo da Cobrança
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-700 dark:text-blue-300">
                    Plano:
                  </span>
                  <span className="text-blue-900 dark:text-blue-100 font-medium">
                    {selectedPlan.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700 dark:text-blue-300">
                    Valor mensal:
                  </span>
                  <span className="text-blue-900 dark:text-blue-100 font-medium">
                    {B2BBillingService.formatCurrency(
                      selectedPlan.monthly_price
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700 dark:text-blue-300">
                    Próxima cobrança:
                  </span>
                  <span className="text-blue-900 dark:text-blue-100 font-medium">
                    Dia {billingDay} de cada mês
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700 dark:text-blue-300">
                    Método:
                  </span>
                  <span className="text-blue-900 dark:text-blue-100 font-medium">
                    {paymentMethod === "manual" ? "Manual" : "Automático"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-border">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading || !selectedPlanId}
            loading={loading}
          >
            {isEditing ? "Atualizar Assinatura" : "Criar Assinatura"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionManagementModal;
