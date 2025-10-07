import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Alert, AlertDescription } from "../ui/alert";
import { RadioGroup, RadioGroupItem } from "../ui/radio-group";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import {
  Loader2,
  CreditCard,
  FileText,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import {
  BillingMethodStatus,
  BillingMethodUpdate,
} from "../../types/pagbank.types";

interface PagBankMethodSelectorProps {
  contractId: number;
  currentStatus?: BillingMethodStatus;
  onMethodChange?: (method: "recurrent" | "manual") => void;
  onStatusUpdate?: (status: BillingMethodStatus) => void;
  loading?: boolean;
  disabled?: boolean;
}

const PagBankMethodSelector: React.FC<PagBankMethodSelectorProps> = ({
  contractId,
  currentStatus,
  onMethodChange,
  onStatusUpdate,
  loading = false,
  disabled = false,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<"recurrent" | "manual">(
    currentStatus?.billing_method || "manual"
  );
  const [autoFallback, setAutoFallback] = useState(
    currentStatus?.auto_fallback_enabled ?? true
  );
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (currentStatus) {
      setSelectedMethod(currentStatus.billing_method);
      setAutoFallback(currentStatus.auto_fallback_enabled);
    }
  }, [currentStatus]);

  const handleMethodChange = (value: string) => {
    const method = value as "recurrent" | "manual";
    setSelectedMethod(method);
    onMethodChange?.(method);
  };

  const getBillingMethodIcon = (method: "recurrent" | "manual") => {
    return method === "recurrent" ? (
      <CreditCard className="h-5 w-5 text-blue-600" />
    ) : (
      <FileText className="h-5 w-5 text-green-600" />
    );
  };

  const getBillingMethodLabel = (method: "recurrent" | "manual") => {
    return method === "recurrent" ? "Cobrança Recorrente" : "Cobrança Manual";
  };

  const getBillingMethodDescription = (method: "recurrent" | "manual") => {
    if (method === "recurrent") {
      return "Pagamento automático via cartão de crédito cadastrado. Cobranças mensais automáticas.";
    }
    return "Pagamento manual via PIX, Boleto ou Cartão. Cliente recebe link de pagamento.";
  };

  const getStatusBadge = () => {
    if (!currentStatus) return null;

    const isActive = currentStatus.is_active;
    const method = currentStatus.billing_method;
    const hasFailures = currentStatus.attempt_count > 0;

    if (!isActive) {
      return (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
          <AlertCircle className="h-4 w-4" />
          Inativo
        </div>
      );
    }

    if (method === "recurrent" && hasFailures) {
      return (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-orange-100 text-orange-700 text-sm">
          <AlertCircle className="h-4 w-4" />
          {currentStatus.attempt_count} tentativa(s) falharam
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm">
        <CheckCircle className="h-4 w-4" />
        Ativo
      </div>
    );
  };

  const getPagBankStatusInfo = () => {
    if (
      !currentStatus?.pagbank_data ||
      currentStatus.billing_method !== "recurrent"
    ) {
      return null;
    }

    const pagbankData = currentStatus.pagbank_data;

    return (
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-medium text-blue-900 mb-2">Status PagBank</h4>
        <div className="space-y-1 text-sm text-blue-700">
          <div>Assinatura: {pagbankData.subscription_id || "N/A"}</div>
          <div>Status: {pagbankData.subscription_status || "N/A"}</div>
          {pagbankData.next_billing_date && (
            <div>
              Próxima cobrança:{" "}
              {new Date(pagbankData.next_billing_date).toLocaleDateString(
                "pt-BR"
              )}
            </div>
          )}
          {pagbankData.status_check_error && (
            <div className="text-red-600">
              Erro: {pagbankData.status_check_error}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
          <span className="ml-2 text-gray-500">
            Carregando método de cobrança...
          </span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Método de Cobrança PagBank</CardTitle>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <RadioGroup
          value={selectedMethod}
          onValueChange={handleMethodChange}
          disabled={disabled || isUpdating}
        >
          <div className="space-y-4">
            {/* Recurrent Billing Option */}
            <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <RadioGroupItem
                value="recurrent"
                id="recurrent"
                className="mt-1"
              />
              <div className="flex-1">
                <Label
                  htmlFor="recurrent"
                  className="flex items-center gap-2 font-medium cursor-pointer"
                >
                  {getBillingMethodIcon("recurrent")}
                  {getBillingMethodLabel("recurrent")}
                </Label>
                <p className="text-sm text-gray-600 mt-1">
                  {getBillingMethodDescription("recurrent")}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  ✓ Pagamento automático &nbsp;&nbsp; ✓ Sem interrupção do
                  serviço &nbsp;&nbsp; ✓ Fallback automático
                </div>
              </div>
            </div>

            {/* Manual Billing Option */}
            <div className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <RadioGroupItem value="manual" id="manual" className="mt-1" />
              <div className="flex-1">
                <Label
                  htmlFor="manual"
                  className="flex items-center gap-2 font-medium cursor-pointer"
                >
                  {getBillingMethodIcon("manual")}
                  {getBillingMethodLabel("manual")}
                </Label>
                <p className="text-sm text-gray-600 mt-1">
                  {getBillingMethodDescription("manual")}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  ✓ PIX, Boleto e Cartão &nbsp;&nbsp; ✓ Flexibilidade de
                  pagamento &nbsp;&nbsp; ✓ Link de checkout seguro
                </div>
              </div>
            </div>
          </div>
        </RadioGroup>

        {/* Auto Fallback Option */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <Label htmlFor="auto-fallback" className="font-medium">
              Fallback Automático
            </Label>
            <p className="text-sm text-gray-600">
              Mudar automaticamente para cobrança manual após 3 falhas
              consecutivas
            </p>
          </div>
          <Switch
            id="auto-fallback"
            checked={autoFallback}
            onCheckedChange={setAutoFallback}
            disabled={disabled || isUpdating}
          />
        </div>

        {/* Current Status Info */}
        {currentStatus && (
          <div className="space-y-3 pt-4 border-t">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Status:</span>
                <span className="ml-2 font-medium">
                  {currentStatus.is_active ? "Ativo" : "Inativo"}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Método atual:</span>
                <span className="ml-2 font-medium">
                  {getBillingMethodLabel(currentStatus.billing_method)}
                </span>
              </div>
              {currentStatus.next_billing_date && (
                <div>
                  <span className="text-gray-500">Próxima cobrança:</span>
                  <span className="ml-2 font-medium">
                    {new Date(
                      currentStatus.next_billing_date
                    ).toLocaleDateString("pt-BR")}
                  </span>
                </div>
              )}
              {currentStatus.attempt_count > 0 && (
                <div>
                  <span className="text-gray-500">Tentativas falharam:</span>
                  <span className="ml-2 font-medium text-orange-600">
                    {currentStatus.attempt_count}
                  </span>
                </div>
              )}
            </div>

            {getPagBankStatusInfo()}
          </div>
        )}

        {/* Warning for method changes */}
        {currentStatus && selectedMethod !== currentStatus.billing_method && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Você está prestes a alterar o método de cobrança. Esta ação pode
              impactar os próximos pagamentos do contrato.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default PagBankMethodSelector;
