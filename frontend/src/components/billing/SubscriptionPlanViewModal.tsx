import React from "react";
import Card from "../ui/Card";
import {
  X,
  CreditCard,
  Users,
  Building,
  Settings,
  Info,
  Calendar,
  DollarSign,
  Check,
  X as XIcon,
} from "lucide-react";
import type { SubscriptionPlan } from "../../types/b2b-billing.types";

interface SubscriptionPlanViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: SubscriptionPlan | null;
}

const SubscriptionPlanViewModal: React.FC<SubscriptionPlanViewModalProps> = ({
  isOpen,
  onClose,
  plan,
}) => {
  if (!isOpen || !plan) return null;

  const formatCurrency = (value: number | string): string => {
    const numValue = typeof value === "string" ? parseFloat(value) : value;
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(numValue);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const getFeatureLabel = (key: string, value: unknown): string => {
    const labels: Record<string, string> = {
      reports: "Relatórios",
      support: "Suporte",
      integrations: "Integrações",
      analytics: "Analytics Avançado",
      custom_features: "Recursos Customizados",
    };

    if (key === "reports") {
      const reportLabels: Record<string, string> = {
        basic: "Básico",
        advanced: "Avançado",
        premium: "Premium",
      };
      return `${labels[key]}: ${reportLabels[value] || value}`;
    }

    if (key === "support") {
      const supportLabels: Record<string, string> = {
        email: "Email",
        priority: "Prioritário",
        dedicated: "Dedicado",
      };
      return `${labels[key]}: ${supportLabels[value] || value}`;
    }

    if (key === "integrations") {
      const integrationLabels: Record<string, string> = {
        limited: "Limitadas",
        full: "Completas",
        unlimited: "Ilimitadas",
      };
      return `${labels[key]}: ${integrationLabels[value] || value}`;
    }

    if (typeof value === "boolean" && value) {
      return labels[key] || key;
    }

    return `${labels[key] || key}: ${value}`;
  };

  const featuresList = plan.features
    ? Object.entries(plan.features).filter(([, value]) => value)
    : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Detalhes do Plano: {plan.name}
          </h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Status */}
          <div className="flex items-center justify-between">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                plan.is_active
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {plan.is_active ? (
                <>
                  <Check className="w-4 h-4 mr-1" />
                  Ativo
                </>
              ) : (
                <>
                  <XIcon className="w-4 h-4 mr-1" />
                  Inativo
                </>
              )}
            </span>
            <div className="text-sm text-gray-500 flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              Criado em {formatDate(plan.created_at)}
            </div>
          </div>

          {/* Informações Básicas */}
          <Card title="Informações Básicas" icon={<Info className="h-5 w-5" />}>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Nome do Plano
                  </div>
                  <p className="text-sm text-foreground bg-muted px-3 py-2 rounded-md">
                    {plan.name}
                  </p>
                </div>

                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Preço Mensal
                  </div>
                  <p className="text-sm text-foreground bg-muted px-3 py-2 rounded-md flex items-center gap-1">
                    <DollarSign className="w-4 h-4 text-green-600 dark:text-green-400" />
                    {formatCurrency(plan.monthly_price)}
                  </p>
                </div>
              </div>

              {plan.description && (
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Descrição
                  </div>
                  <p className="text-sm text-foreground bg-muted px-3 py-2 rounded-md whitespace-pre-wrap">
                    {plan.description}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Limites */}
          <Card title="Limites de Uso" icon={<Users className="h-5 w-5" />}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="block text-sm font-medium text-muted-foreground mb-1">
                  Máximo de Usuários
                </div>
                <p className="text-sm text-foreground bg-muted px-3 py-2 rounded-md flex items-center gap-1">
                  <Users className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  {plan.max_users ? plan.max_users : "Ilimitado"}
                </p>
              </div>

              <div>
                <div className="block text-sm font-medium text-muted-foreground mb-1">
                  Máximo de Estabelecimentos
                </div>
                <p className="text-sm text-foreground bg-muted px-3 py-2 rounded-md flex items-center gap-1">
                  <Building className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  {plan.max_establishments
                    ? plan.max_establishments
                    : "Ilimitado"}
                </p>
              </div>
            </div>
          </Card>

          {/* Features */}
          <Card
            title="Recursos e Funcionalidades"
            icon={<Settings className="h-5 w-5" />}
          >
            {featuresList.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {featuresList.map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                    <span className="text-foreground">
                      {getFeatureLabel(key, value)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">
                Nenhum recurso específico configurado
              </p>
            )}
          </Card>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors font-medium"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPlanViewModal;
