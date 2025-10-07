/**
 * BillingSettingsForm Component
 * Form for configuring billing settings for a contract
 */

import React, { useState, useEffect } from "react";
import { Contract } from "../../services/contractsService";
import { BillingCycle } from "../../types/billing.types";

interface BillingSettingsFormProps {
  contract: Contract;
  onSave: (settings: BillingSettings) => void;
  loading?: boolean;
  className?: string;
}

export interface BillingSettings {
  is_billing_enabled: boolean;
  billing_cycle: BillingCycle;
  billing_day: number;
  next_billing_date: string;
  amount_per_cycle: number;
  grace_period_days: number;
  auto_generate_invoices: boolean;
  send_email_notifications: boolean;
  late_fee_percentage?: number;
  notes?: string;
}

const BillingSettingsForm: React.FC<BillingSettingsFormProps> = ({
  contract,
  onSave,
  loading = false,
  className = "",
}) => {
  const [settings, setSettings] = useState<BillingSettings>({
    is_billing_enabled: true,
    billing_cycle: BillingCycle.MONTHLY,
    billing_day: 1,
    next_billing_date: getNextMonthFirstDay(),
    amount_per_cycle: parseFloat(contract.monthly_value?.toString() || "0"),
    grace_period_days: 5,
    auto_generate_invoices: true,
    send_email_notifications: true,
    late_fee_percentage: 2,
    notes: "",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  function getNextMonthFirstDay(): string {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return nextMonth.toISOString().split("T")[0];
  }

  const billingCycleOptions = [
    {
      value: BillingCycle.MONTHLY,
      label: "Mensal",
      description: "Cobrança todo mês",
    },
    {
      value: BillingCycle.QUARTERLY,
      label: "Trimestral",
      description: "Cobrança a cada 3 meses",
    },
    {
      value: BillingCycle.SEMI_ANNUAL,
      label: "Semestral",
      description: "Cobrança a cada 6 meses",
    },
    {
      value: BillingCycle.ANNUAL,
      label: "Anual",
      description: "Cobrança uma vez por ano",
    },
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (settings.amount_per_cycle <= 0) {
      newErrors.amount_per_cycle = "Valor deve ser maior que zero";
    }

    if (settings.billing_day < 1 || settings.billing_day > 31) {
      newErrors.billing_day = "Dia deve estar entre 1 e 31";
    }

    if (settings.grace_period_days < 0 || settings.grace_period_days > 90) {
      newErrors.grace_period_days =
        "Período de carência deve estar entre 0 e 90 dias";
    }

    if (
      settings.late_fee_percentage &&
      (settings.late_fee_percentage < 0 || settings.late_fee_percentage > 20)
    ) {
      newErrors.late_fee_percentage = "Taxa de multa deve estar entre 0% e 20%";
    }

    if (!settings.next_billing_date) {
      newErrors.next_billing_date = "Data do próximo faturamento é obrigatória";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const updateSetting = <K extends keyof BillingSettings>(
    key: K,
    value: BillingSettings[K]
  ) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));

    // Clear error when user starts typing
    if (errors[key]) {
      setErrors((prev) => ({
        ...prev,
        [key]: "",
      }));
    }
  };

  const calculateNextBillingDate = (
    cycle: BillingCycle,
    day: number
  ): string => {
    const now = new Date();
    let nextDate: Date;

    switch (cycle) {
      case BillingCycle.MONTHLY:
        nextDate = new Date(now.getFullYear(), now.getMonth() + 1, day);
        break;
      case BillingCycle.QUARTERLY:
        nextDate = new Date(now.getFullYear(), now.getMonth() + 3, day);
        break;
      case BillingCycle.SEMI_ANNUAL:
        nextDate = new Date(now.getFullYear(), now.getMonth() + 6, day);
        break;
      case BillingCycle.ANNUAL:
        nextDate = new Date(now.getFullYear() + 1, now.getMonth(), day);
        break;
      default:
        nextDate = new Date(now.getFullYear(), now.getMonth() + 1, day);
    }

    return nextDate.toISOString().split("T")[0];
  };

  // Update next billing date when cycle or day changes
  useEffect(() => {
    const nextDate = calculateNextBillingDate(
      settings.billing_cycle,
      settings.billing_day
    );
    updateSetting("next_billing_date", nextDate);
  }, [settings.billing_cycle, settings.billing_day]);

  return (
    <div className={`bg-white rounded-lg border ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          ⚙️ Configurações de Faturamento
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Configure como e quando as faturas serão geradas para este contrato.
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Enable Billing */}
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="is_billing_enabled"
            checked={settings.is_billing_enabled}
            onChange={(e) =>
              updateSetting("is_billing_enabled", e.target.checked)
            }
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <div>
            <label
              htmlFor="is_billing_enabled"
              className="text-sm font-medium text-gray-900"
            >
              Ativar Faturamento Automático
            </label>
            <p className="text-xs text-gray-500">
              Gerar faturas automaticamente baseado na configuração abaixo
            </p>
          </div>
        </div>

        {settings.is_billing_enabled && (
          <>
            {/* Billing Cycle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ciclo de Faturamento
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {billingCycleOptions.map((option) => (
                  <label
                    key={option.value}
                    className={`relative flex cursor-pointer rounded-lg border p-4 focus:outline-none ${
                      settings.billing_cycle === option.value
                        ? "border-blue-600 ring-2 ring-blue-600"
                        : "border-gray-300"
                    }`}
                  >
                    <input
                      type="radio"
                      name="billing_cycle"
                      value={option.value}
                      checked={settings.billing_cycle === option.value}
                      onChange={(e) =>
                        updateSetting(
                          "billing_cycle",
                          e.target.value as BillingCycle
                        )
                      }
                      className="sr-only"
                    />
                    <div className="flex">
                      <div className="text-sm">
                        <div className="font-medium text-gray-900">
                          {option.label}
                        </div>
                        <div className="text-gray-500">
                          {option.description}
                        </div>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Billing Day and Amount */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dia do Faturamento
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={settings.billing_day}
                  onChange={(e) =>
                    updateSetting("billing_day", parseInt(e.target.value) || 1)
                  }
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.billing_day ? "border-red-300" : "border-gray-300"
                  }`}
                />
                {errors.billing_day && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.billing_day}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Dia do mês para gerar a fatura (1-31)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor por Ciclo *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">
                    R$
                  </span>
                  <input
                    type="text"
                    inputMode="decimal"
                    defaultValue={
                      settings.amount_per_cycle
                        ? settings.amount_per_cycle.toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })
                        : ""
                    }
                    onBlur={(e) => {
                      const value = e.target.value;
                      if (!value || value === "") {
                        updateSetting("amount_per_cycle", null);
                        return;
                      }

                      // Converter formato BR para número
                      const cleanValue = value.replace(/[^\d.,]/g, "");
                      let numericValue;

                      if (cleanValue.includes(",")) {
                        const parts = cleanValue.split(",");
                        const integerPart = parts[0].replace(/\./g, "");
                        const decimalPart = parts[1]
                          ? parts[1].substring(0, 2)
                          : "";
                        numericValue = parseFloat(
                          `${integerPart}.${decimalPart}`
                        );
                      } else {
                        numericValue = parseFloat(
                          cleanValue.replace(/\./g, "")
                        );
                      }

                      if (!isNaN(numericValue)) {
                        updateSetting("amount_per_cycle", numericValue);
                        // Formatar o valor no campo
                        e.target.value = numericValue.toLocaleString("pt-BR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        });
                      }
                    }}
                    onKeyDown={(e) => {
                      if (
                        [
                          "Backspace",
                          "Delete",
                          "Tab",
                          "Escape",
                          "Enter",
                          "Home",
                          "End",
                          "ArrowLeft",
                          "ArrowRight",
                          "ArrowUp",
                          "ArrowDown",
                        ].includes(e.key)
                      ) {
                        return;
                      }
                      if (e.ctrlKey || e.metaKey) {
                        return;
                      }
                      if (!/[0-9.,]/.test(e.key)) {
                        e.preventDefault();
                      }
                    }}
                    placeholder="Ex: 1999,50 ou 1.999,50"
                    className={`w-full pl-8 pr-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                      errors.amount_per_cycle
                        ? "border-red-300"
                        : "border-gray-300"
                    }`}
                  />
                </div>
                {errors.amount_per_cycle && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.amount_per_cycle}
                  </p>
                )}
              </div>
            </div>

            {/* Next Billing Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Próximo Faturamento
              </label>
              <input
                type="date"
                value={settings.next_billing_date}
                onChange={(e) =>
                  updateSetting("next_billing_date", e.target.value)
                }
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                  errors.next_billing_date
                    ? "border-red-300"
                    : "border-gray-300"
                }`}
              />
              {errors.next_billing_date && (
                <p className="mt-1 text-xs text-red-600">
                  {errors.next_billing_date}
                </p>
              )}
            </div>

            {/* Additional Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Período de Carência (dias)
                </label>
                <input
                  type="number"
                  min="0"
                  max="90"
                  value={settings.grace_period_days}
                  onChange={(e) =>
                    updateSetting(
                      "grace_period_days",
                      parseInt(e.target.value) || 0
                    )
                  }
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.grace_period_days
                      ? "border-red-300"
                      : "border-gray-300"
                  }`}
                />
                {errors.grace_period_days && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.grace_period_days}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Dias após vencimento antes de considerar em atraso
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Taxa de Multa (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="20"
                  value={settings.late_fee_percentage || ""}
                  onChange={(e) =>
                    updateSetting(
                      "late_fee_percentage",
                      parseFloat(e.target.value) || undefined
                    )
                  }
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${
                    errors.late_fee_percentage
                      ? "border-red-300"
                      : "border-gray-300"
                  }`}
                />
                {errors.late_fee_percentage && (
                  <p className="mt-1 text-xs text-red-600">
                    {errors.late_fee_percentage}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Porcentagem de multa para pagamentos em atraso
                </p>
              </div>
            </div>

            {/* Additional Options */}
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="auto_generate_invoices"
                  checked={settings.auto_generate_invoices}
                  onChange={(e) =>
                    updateSetting("auto_generate_invoices", e.target.checked)
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="auto_generate_invoices"
                  className="text-sm text-gray-900"
                >
                  Gerar faturas automaticamente
                </label>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="send_email_notifications"
                  checked={settings.send_email_notifications}
                  onChange={(e) =>
                    updateSetting("send_email_notifications", e.target.checked)
                  }
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="send_email_notifications"
                  className="text-sm text-gray-900"
                >
                  Enviar notificações por email
                </label>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Observações
              </label>
              <textarea
                rows={3}
                value={settings.notes || ""}
                onChange={(e) => updateSetting("notes", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Observações sobre a configuração de faturamento..."
              />
            </div>
          </>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => {
              if (validateForm()) {
                onSave(settings);
              }
            }}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Salvando..." : "Salvar Configurações"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BillingSettingsForm;
