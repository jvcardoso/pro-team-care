/**
 * Company Billing Table Configuration
 * Defines all settings for the company billing data table
 */

import React from "react";
import { Eye } from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { CompanyBillingData } from "../../hooks/useCompanyBillingData";
import { formatCNPJ } from "../../utils/validators";

export const createCompanyBillingConfig = (
  onViewCompany?: (company: CompanyBillingData) => void
): DataTableConfig<CompanyBillingData> => ({
  // Basic Info
  entity: "company-billing",
  title: "🏢 Empresa X Planos",
  description: "Gestão de empresas e seus planos de assinatura",

  // Data Structure - Optimized for NO horizontal scroll
  columns: [
    {
      key: "name",
      label: "Empresa",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div className="min-w-0 max-w-[200px]">
          <div className="font-semibold text-sm truncate" title={value}>
            {value}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
            {item.cnpj ? formatCNPJ(item.cnpj) : "CNPJ não informado"}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      type: "badge",
      render: (value) => getStatusBadge(value),
    },
    {
      key: "active_plan",
      label: "Plano",
      type: "custom",
      render: (plan, item) => (
        <div className="text-sm min-w-0 max-w-[140px]">
          {plan ? (
            <div>
              <div className="font-medium truncate" title={plan.name}>
                {plan.name}
              </div>
              <div className="text-green-600 dark:text-green-400 font-semibold text-xs truncate">
                {formatCurrency(item.monthly_value || 0)}
              </div>
            </div>
          ) : (
            <span className="text-gray-500 italic text-xs">Sem plano</span>
          )}
        </div>
      ),
    },
    {
      key: "payment_method",
      label: "Método",
      type: "text",
      render: (value) => (
        <div
          className="text-xs truncate max-w-[90px]"
          title={value || "Não informado"}
        >
          {getPaymentMethodLabel(value)}
        </div>
      ),
    },
  ],

  searchFields: ["name", "status"],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics - Disabled as requested (only tables and filters needed)
  metrics: {
    primary: [],
    detailed: undefined,
  },

  // Filters
  filters: [
    {
      key: "status",
      label: "Status",
      type: "select",
      options: [
        { value: "all", label: "📋 Todos os status" },
        { value: "Ativo", label: "✅ Ativo" },
        { value: "Sem plano", label: "⏸️ Sem plano" },
      ],
    },
    {
      key: "monthly_value",
      label: "Faixa de Valor",
      type: "range",
      min: 0,
      max: 10000,
      step: 50,
    },
    {
      key: "active_plan",
      label: "Plano Ativo",
      type: "select",
      options: [
        { value: "all", label: "📋 Todos os planos" },
        { value: "with_plan", label: "✅ Com plano" },
        { value: "without_plan", label: "⏸️ Sem plano" },
      ],
    },
  ],

  // Actions
  actions: [
    {
      id: "view",
      label: "Ver Empresa",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick: (company) => {
        if (onViewCompany) {
          onViewCompany(company);
        }
      },
    },
  ],

  // Export
  export: {
    filename: "empresas-cobranca",
    formats: ["csv", "json", "print"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization - Compact table for better responsiveness
  className: "company-billing-table",
  theme: "default",

  // Table styling overrides - More compact for better responsiveness
  tableStyles: {
    compact: true,
    cellPadding: "px-2 py-2",
    fontSize: "text-sm",
  },
});

// Helper functions

function formatDate(dateString: string): string {
  try {
    return new Date(dateString).toLocaleDateString("pt-BR");
  } catch {
    return dateString;
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function getPaymentMethodLabel(method: string | undefined): string {
  if (!method) return "N/I";

  const labels: Record<string, string> = {
    manual: "Manual",
    recurrent: "Recorrente",
    credit_card: "Cartão",
    boleto: "Boleto",
    pix: "PIX",
  };

  return labels[method.toLowerCase()] || method.substring(0, 8);
}

function getStatusBadge(status: string): JSX.Element {
  const statusConfig: Record<
    string,
    { bg: string; text: string; label: string }
  > = {
    Ativo: {
      bg: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
      text: "✅ Ativo",
      label: "Ativo",
    },
    "Sem plano": {
      bg: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
      text: "⏸️ Sem plano",
      label: "Sem plano",
    },
  };

  const config = statusConfig[status] || statusConfig["Sem plano"];

  return (
    <span
      className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap ${config.bg}`}
    >
      {config.label}
    </span>
  );
}

export default createCompanyBillingConfig;
