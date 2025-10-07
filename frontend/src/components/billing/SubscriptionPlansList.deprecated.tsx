import React, { useState, useEffect } from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { Badge } from "../ui/Badge";
import { notify } from "../../utils/notifications";
import {
  CreditCard,
  Settings,
  Plus,
  Edit,
  Trash2,
  Users,
  Building,
  Check,
  X,
} from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import type { SubscriptionPlan } from "../../types/b2b-billing.types";

interface SubscriptionPlansListProps {
  onCreatePlan: () => void;
  onEditPlan: (plan: SubscriptionPlan) => void;
  refreshTrigger?: number;
}

const SubscriptionPlansList: React.FC<SubscriptionPlansListProps> = ({
  onCreatePlan,
  onEditPlan,
  refreshTrigger = 0,
}) => {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [showInactive, setShowInactive] = useState(false);

  useEffect(() => {
    loadPlans();
  }, [showInactive, refreshTrigger]);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const plansData = await B2BBillingService.getSubscriptionPlans(
        !showInactive
      );
      setPlans(plansData);
    } catch (err: any) {
      notify.error("Erro ao carregar planos: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePlan = async (plan: SubscriptionPlan) => {
    if (!confirm(`Tem certeza que deseja desativar o plano "${plan.name}"?`)) {
      return;
    }

    try {
      await B2BBillingService.deleteSubscriptionPlan(plan.id);
      notify.success("Plano desativado com sucesso!");
      loadPlans();
    } catch (err: any) {
      notify.error("Erro ao desativar plano: " + err.message);
    }
  };

  const formatCurrency = (amount: number | string): string => {
    const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(numAmount);
  };

  const getFeaturesList = (plan: SubscriptionPlan): string[] => {
    const features: string[] = [];

    if (plan.max_users) {
      features.push(`Até ${plan.max_users} usuários`);
    } else {
      features.push("Usuários ilimitados");
    }

    if (plan.max_establishments) {
      features.push(`Até ${plan.max_establishments} estabelecimentos`);
    } else {
      features.push("Estabelecimentos ilimitados");
    }

    if (plan.features?.reports) {
      features.push(`Relatórios ${plan.features.reports}`);
    }

    if (plan.features?.support) {
      features.push(`Suporte ${plan.features.support}`);
    }

    if (plan.features?.analytics) {
      features.push("Analytics avançado");
    }

    if (plan.features?.integrations) {
      features.push(`Integrações ${plan.features.integrations}`);
    }

    if (plan.features?.custom_features) {
      features.push("Recursos customizados");
    }

    return features;
  };

  if (loading && plans.length === 0) {
    return (
      <Card>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-500">Carregando planos...</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CreditCard className="h-6 w-6 text-blue-600" />
            Planos de Assinatura
          </h2>
          <p className="text-gray-600 mt-1">
            Gerencie os planos disponíveis para as empresas
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded border-gray-300"
            />
            Mostrar inativos
          </label>
          <Button onClick={onCreatePlan} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Novo Plano
          </Button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            className={`relative ${
              !plan.is_active
                ? "opacity-60 border-gray-300"
                : "border-gray-200 hover:border-blue-300"
            } transition-all duration-200`}
          >
            {/* Status Badge */}
            <div className="absolute top-4 right-4">
              <Badge variant={plan.is_active ? "success" : "secondary"}>
                {plan.is_active ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Ativo
                  </>
                ) : (
                  <>
                    <X className="h-3 w-3 mr-1" />
                    Inativo
                  </>
                )}
              </Badge>
            </div>

            <div className="p-6">
              {/* Plan Header */}
              <div className="mb-4">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {plan.name}
                </h3>
                <p className="text-gray-600 text-sm mb-3">{plan.description}</p>
                <div className="text-3xl font-bold text-blue-600">
                  {formatCurrency(plan.monthly_price)}
                  <span className="text-sm font-normal text-gray-500">
                    /mês
                  </span>
                </div>
              </div>

              {/* Limits */}
              <div className="mb-4 space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Users className="h-4 w-4" />
                  {plan.max_users
                    ? `${plan.max_users} usuários`
                    : "Usuários ilimitados"}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Building className="h-4 w-4" />
                  {plan.max_establishments
                    ? `${plan.max_establishments} estabelecimentos`
                    : "Estabelecimentos ilimitados"}
                </div>
              </div>

              {/* Features */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Recursos:
                </h4>
                <ul className="space-y-1">
                  {getFeaturesList(plan)
                    .slice(0, 4)
                    .map((feature, index) => (
                      <li
                        key={index}
                        className="flex items-center gap-2 text-sm text-gray-600"
                      >
                        <Check className="h-3 w-3 text-green-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  {getFeaturesList(plan).length > 4 && (
                    <li className="text-sm text-gray-500">
                      +{getFeaturesList(plan).length - 4} outros recursos
                    </li>
                  )}
                </ul>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEditPlan(plan)}
                  className="flex items-center gap-2 flex-1"
                >
                  <Edit className="h-4 w-4" />
                  Editar
                </Button>
                {plan.is_active && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeletePlan(plan)}
                    className="flex items-center gap-2 text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {plans.length === 0 && !loading && (
        <Card>
          <div className="text-center py-12">
            <CreditCard className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Nenhum plano encontrado
            </h3>
            <p className="text-gray-500 mb-4">
              {showInactive
                ? "Não há planos inativos cadastrados."
                : "Não há planos ativos cadastrados. Crie o primeiro plano para começar."}
            </p>
            {!showInactive && (
              <Button
                onClick={onCreatePlan}
                className="flex items-center gap-2 mx-auto"
              >
                <Plus className="h-4 w-4" />
                Criar Primeiro Plano
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default SubscriptionPlansList;
