import React, { useState, useEffect } from "react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import Textarea from "../ui/Textarea";
import { notify } from "../../utils/notifications";
import { X, CreditCard, Users, Building, Settings, Info } from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import type { SubscriptionPlan } from "../../types/b2b-billing.types";

interface SubscriptionPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  plan?: SubscriptionPlan | null;
}

const SubscriptionPlanModal: React.FC<SubscriptionPlanModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  plan,
}) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [monthlyPrice, setMonthlyPrice] = useState<number>(0);
  const [maxUsers, setMaxUsers] = useState<number | null>(null);
  const [maxEstablishments, setMaxEstablishments] = useState<number | null>(
    null
  );
  const [isActive, setIsActive] = useState(true);
  const [loading, setLoading] = useState(false);

  // Features
  const [reportsType, setReportsType] = useState("basic");
  const [supportType, setSupportType] = useState("email");
  const [integrationsType, setIntegrationsType] = useState("limited");
  const [hasAnalytics, setHasAnalytics] = useState(false);
  const [hasCustomFeatures, setHasCustomFeatures] = useState(false);

  const isEditing = !!plan;

  useEffect(() => {
    if (isOpen) {
      if (plan) {
        setName(plan.name);
        setDescription(plan.description || "");
        setMonthlyPrice(
          typeof plan.monthly_price === "string"
            ? parseFloat(plan.monthly_price)
            : plan.monthly_price
        );
        setMaxUsers(plan.max_users);
        setMaxEstablishments(plan.max_establishments);
        setIsActive(plan.is_active);

        // Features
        if (plan.features) {
          setReportsType(plan.features.reports || "basic");
          setSupportType(plan.features.support || "email");
          setIntegrationsType(plan.features.integrations || "limited");
          setHasAnalytics(!!plan.features.analytics);
          setHasCustomFeatures(!!plan.features.custom_features);
        }
      } else {
        // Reset form for new plan
        setName("");
        setDescription("");
        setMonthlyPrice(0);
        setMaxUsers(null);
        setMaxEstablishments(null);
        setIsActive(true);
        setReportsType("basic");
        setSupportType("email");
        setIntegrationsType("limited");
        setHasAnalytics(false);
        setHasCustomFeatures(false);
      }
    }
  }, [isOpen, plan]);

  const handleSave = async () => {
    // Validações
    if (!name.trim()) {
      notify.error("Nome do plano é obrigatório");
      return;
    }

    if (monthlyPrice <= 0) {
      notify.error("Preço mensal deve ser maior que zero");
      return;
    }

    if (maxUsers !== null && maxUsers <= 0) {
      notify.error("Número máximo de usuários deve ser maior que zero");
      return;
    }

    if (maxEstablishments !== null && maxEstablishments <= 0) {
      notify.error("Número máximo de estabelecimentos deve ser maior que zero");
      return;
    }

    try {
      setLoading(true);

      const planData = {
        name: name.trim(),
        description: description.trim() || null,
        monthly_price: monthlyPrice,
        max_users: maxUsers,
        max_establishments: maxEstablishments,
        is_active: isActive,
        features: {
          reports: reportsType,
          support: supportType,
          integrations: integrationsType,
          ...(hasAnalytics && { analytics: true }),
          ...(hasCustomFeatures && { custom_features: true }),
        },
      };

      if (isEditing && plan) {
        await B2BBillingService.updateSubscriptionPlan(plan.id, planData);
        notify.success("Plano atualizado com sucesso!");
      } else {
        await B2BBillingService.createSubscriptionPlan(planData);
        notify.success("Plano criado com sucesso!");
      }

      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err: any) {
      notify.error(
        `Erro ao ${isEditing ? "atualizar" : "criar"} plano: ` + err.message
      );
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            {isEditing ? "Editar Plano" : "Novo Plano de Assinatura"}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Informações Básicas */}
          <Card title="Informações Básicas" icon={<Info className="h-5 w-5" />}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Plano *
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: Básico, Premium, Enterprise"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Descreva o plano e seus benefícios"
                  rows={3}
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preço Mensal (R$) *
                </label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={monthlyPrice}
                  onChange={(e) =>
                    setMonthlyPrice(parseFloat(e.target.value) || 0)
                  }
                  placeholder="0.00"
                  disabled={loading}
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="rounded border-gray-300"
                  disabled={loading}
                />
                <label
                  htmlFor="isActive"
                  className="text-sm font-medium text-gray-700"
                >
                  Plano ativo
                </label>
              </div>
            </div>
          </Card>

          {/* Limites */}
          <Card title="Limites de Uso" icon={<Users className="h-5 w-5" />}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Máximo de Usuários
                </label>
                <Input
                  type="number"
                  min="1"
                  value={maxUsers || ""}
                  onChange={(e) =>
                    setMaxUsers(
                      e.target.value ? parseInt(e.target.value) : null
                    )
                  }
                  placeholder="Deixe vazio para ilimitado"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Deixe vazio para permitir usuários ilimitados
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Máximo de Estabelecimentos
                </label>
                <Input
                  type="number"
                  min="1"
                  value={maxEstablishments || ""}
                  onChange={(e) =>
                    setMaxEstablishments(
                      e.target.value ? parseInt(e.target.value) : null
                    )
                  }
                  placeholder="Deixe vazio para ilimitado"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Deixe vazio para permitir estabelecimentos ilimitados
                </p>
              </div>
            </div>
          </Card>

          {/* Features */}
          <Card
            title="Recursos e Funcionalidades"
            icon={<Settings className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Relatórios
                </label>
                <select
                  value={reportsType}
                  onChange={(e) => setReportsType(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                >
                  <option value="basic">Básico</option>
                  <option value="advanced">Avançado</option>
                  <option value="premium">Premium</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Suporte
                </label>
                <select
                  value={supportType}
                  onChange={(e) => setSupportType(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                >
                  <option value="email">Email</option>
                  <option value="priority">Prioritário</option>
                  <option value="dedicated">Dedicado</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Integrações
                </label>
                <select
                  value={integrationsType}
                  onChange={(e) => setIntegrationsType(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                >
                  <option value="limited">Limitadas</option>
                  <option value="full">Completas</option>
                  <option value="unlimited">Ilimitadas</option>
                </select>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="hasAnalytics"
                    checked={hasAnalytics}
                    onChange={(e) => setHasAnalytics(e.target.checked)}
                    className="rounded border-gray-300"
                    disabled={loading}
                  />
                  <label
                    htmlFor="hasAnalytics"
                    className="text-sm font-medium text-gray-700"
                  >
                    Analytics Avançado
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="hasCustomFeatures"
                    checked={hasCustomFeatures}
                    onChange={(e) => setHasCustomFeatures(e.target.checked)}
                    className="rounded border-gray-300"
                    disabled={loading}
                  />
                  <label
                    htmlFor="hasCustomFeatures"
                    className="text-sm font-medium text-gray-700"
                  >
                    Recursos Customizados
                  </label>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? "Salvando..." : isEditing ? "Atualizar" : "Criar Plano"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPlanModal;
