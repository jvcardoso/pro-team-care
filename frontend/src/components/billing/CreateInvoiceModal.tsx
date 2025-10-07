import React, { useState, useEffect } from "react";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Input from "../ui/Input";
import Textarea from "../ui/Textarea";
import { Alert } from "../ui/Alert";
import { notify } from "../../utils/notifications";
import {
  Building,
  FileText,
  Calendar,
  DollarSign,
  X,
  CheckCircle,
  AlertTriangle,
  Calculator,
  Info,
} from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import type {
  CompanySubscription,
  CreateInvoiceRequest,
} from "../../types/b2b-billing.types";

interface CreateInvoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  companyId: number;
  companyName: string;
  subscription: CompanySubscription;
  onSuccess: () => void;
}

const CreateInvoiceModal: React.FC<CreateInvoiceModalProps> = ({
  isOpen,
  onClose,
  companyId,
  companyName,
  subscription,
  onSuccess,
}) => {
  const [billingPeriodStart, setBillingPeriodStart] = useState<string>("");
  const [billingPeriodEnd, setBillingPeriodEnd] = useState<string>("");
  const [dueDate, setDueDate] = useState<string>("");
  const [amount, setAmount] = useState<number>(
    subscription?.plan?.monthly_price || 0
  );
  const [notes, setNotes] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && subscription) {
      // Configurar período de cobrança padrão (mês atual)
      const today = new Date();
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
      const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

      setBillingPeriodStart(firstDay.toISOString().split("T")[0]);
      setBillingPeriodEnd(lastDay.toISOString().split("T")[0]);

      // Data de vencimento: 30 dias a partir de hoje
      const dueDateDefault = new Date(today);
      dueDateDefault.setDate(today.getDate() + 30);
      setDueDate(dueDateDefault.toISOString().split("T")[0]);

      // Valor padrão do plano
      setAmount(subscription.plan?.monthly_price || 0);
    }
  }, [isOpen, subscription]);

  const handleSave = async () => {
    // Validações
    if (!billingPeriodStart || !billingPeriodEnd || !dueDate || !amount) {
      notify.error("Todos os campos obrigatórios devem ser preenchidos");
      return;
    }

    if (new Date(billingPeriodStart) >= new Date(billingPeriodEnd)) {
      notify.error(
        "A data de início deve ser anterior à data de fim do período"
      );
      return;
    }

    if (new Date(dueDate) <= new Date()) {
      notify.error("A data de vencimento deve ser futura");
      return;
    }

    if (amount <= 0) {
      notify.error("O valor deve ser maior que zero");
      return;
    }

    try {
      setLoading(true);

      const createData: CreateInvoiceRequest = {
        company_id: companyId,
        subscription_id: subscription.id,
        billing_period_start: billingPeriodStart,
        billing_period_end: billingPeriodEnd,
        due_date: dueDate,
        amount: amount,
        notes: notes.trim() || undefined,
      };

      await B2BBillingService.createManualInvoice(createData);
      notify.success("Fatura criada com sucesso!");

      // Fechar modal após sucesso
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err: any) {
      notify.error("Erro ao criar fatura: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculatePeriodDays = (): number => {
    if (!billingPeriodStart || !billingPeriodEnd) return 0;
    const start = new Date(billingPeriodStart);
    const end = new Date(billingPeriodEnd);
    const diffTime = end.getTime() - start.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  const suggestMonthlyAmount = () => {
    if (subscription?.plan?.monthly_price) {
      setAmount(subscription.plan.monthly_price);
    }
  };

  const suggestCurrentMonth = () => {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    setBillingPeriodStart(firstDay.toISOString().split("T")[0]);
    setBillingPeriodEnd(lastDay.toISOString().split("T")[0]);
  };

  const suggestNextMonth = () => {
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth() + 1, 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 2, 0);

    setBillingPeriodStart(firstDay.toISOString().split("T")[0]);
    setBillingPeriodEnd(lastDay.toISOString().split("T")[0]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                Criar Nova Fatura
              </h2>
              <p className="text-sm text-muted-foreground">{companyName}</p>
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
          {/* Informações da Assinatura */}
          <Card
            title="Informações da Assinatura"
            icon={<Building className="h-5 w-5" />}
          >
            <div className="grid grid-cols-2 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <span className="text-sm text-muted-foreground">Plano</span>
                <p className="font-medium">
                  {subscription?.plan?.name || "N/A"}
                </p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">
                  Valor Mensal
                </span>
                <p className="font-medium text-green-600 dark:text-green-400">
                  {subscription?.plan
                    ? B2BBillingService.formatCurrency(
                        subscription.plan.monthly_price
                      )
                    : "N/A"}
                </p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Status</span>
                <p className="font-medium">
                  {B2BBillingService.getStatusLabel(
                    subscription?.status || "active"
                  )}
                </p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">
                  Método de Pagamento
                </span>
                <p className="font-medium">
                  {subscription?.payment_method === "recurrent"
                    ? "Automático"
                    : "Manual"}
                </p>
              </div>
            </div>
          </Card>

          {/* Período de Cobrança */}
          <Card
            title="Período de Cobrança"
            icon={<Calendar className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Data de Início *
                  </label>
                  <Input
                    type="date"
                    value={billingPeriodStart}
                    onChange={(e) => setBillingPeriodStart(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Data de Fim *
                  </label>
                  <Input
                    type="date"
                    value={billingPeriodEnd}
                    onChange={(e) => setBillingPeriodEnd(e.target.value)}
                    disabled={loading}
                  />
                </div>
              </div>

              {/* Sugestões de Período */}
              <div className="flex gap-2 flex-wrap">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={suggestCurrentMonth}
                  disabled={loading}
                >
                  Mês Atual
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={suggestNextMonth}
                  disabled={loading}
                >
                  Próximo Mês
                </Button>
              </div>

              {billingPeriodStart && billingPeriodEnd && (
                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                      Período selecionado
                    </span>
                  </div>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                    {calculatePeriodDays()} dias (
                    {B2BBillingService.formatDate(billingPeriodStart)} até{" "}
                    {B2BBillingService.formatDate(billingPeriodEnd)})
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Valor e Vencimento */}
          <Card
            title="Valor e Vencimento"
            icon={<DollarSign className="h-5 w-5" />}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Valor da Fatura * (R$)
                </label>
                <div className="space-y-2">
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    placeholder="0.00"
                    disabled={loading}
                    icon={<DollarSign className="h-4 w-4" />}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={suggestMonthlyAmount}
                    disabled={loading || !subscription?.plan?.monthly_price}
                    icon={<Calculator className="h-3 w-3" />}
                  >
                    Usar valor do plano
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Data de Vencimento *
                </label>
                <Input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  disabled={loading}
                  icon={<Calendar className="h-4 w-4" />}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  A fatura vencerá nesta data
                </p>
              </div>
            </div>
          </Card>

          {/* Observações */}
          <Card
            title="Observações (Opcional)"
            icon={<FileText className="h-5 w-5" />}
          >
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Digite observações adicionais para esta fatura..."
              rows={3}
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Estas observações aparecerão na fatura para referência
            </p>
          </Card>

          {/* Resumo */}
          {amount > 0 && dueDate && (
            <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-medium text-green-900 dark:text-green-100">
                  Resumo da Fatura
                </span>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-green-700 dark:text-green-300">
                    Valor:
                  </span>
                  <span className="text-green-900 dark:text-green-100 font-bold text-lg">
                    {B2BBillingService.formatCurrency(amount)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700 dark:text-green-300">
                    Vencimento:
                  </span>
                  <span className="text-green-900 dark:text-green-100 font-medium">
                    {B2BBillingService.formatDate(dueDate)}
                  </span>
                </div>
                {billingPeriodStart && billingPeriodEnd && (
                  <div className="flex justify-between">
                    <span className="text-green-700 dark:text-green-300">
                      Período:
                    </span>
                    <span className="text-green-900 dark:text-green-100 font-medium">
                      {calculatePeriodDays()} dias
                    </span>
                  </div>
                )}
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
            disabled={
              loading ||
              !billingPeriodStart ||
              !billingPeriodEnd ||
              !dueDate ||
              !amount
            }
            loading={loading}
          >
            Criar Fatura
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CreateInvoiceModal;
