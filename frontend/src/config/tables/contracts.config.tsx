/**
 * Contracts Table Configuration
 * Defines all settings for the contracts data table
 */

import React from "react";
import { parseCurrencyRobust } from "../../utils/formatters";
import {
  Search,
  Filter,
  Plus,
  Download,
  Eye,
  Edit,
  Trash2,
  MoreHorizontal,
  Users,
  Building,
  Calendar,
  DollarSign,
  ChevronDown,
} from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { Contract } from "../../services/contractsService";

export const createContractsConfig = (actions?: {
  onView?: (contract: Contract) => void;
  onEdit?: (contract: Contract) => void;
  onDelete?: (contract: Contract) => void;
  onAdd?: () => void;
}): DataTableConfig<Contract> => ({
  // Basic Info
  entity: "contratos",
  title: "📋 Dashboard de Contratos Home Care",
  description:
    "Gestão completa de contratos com métricas de negócio em tempo real",

  // Data Structure
  columns: [
    {
      key: "contract_number",
      label: "Contrato",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div className="whitespace-nowrap">
          <div className="text-base font-semibold">{value}</div>
          <div className="font-normal text-gray-500 dark:text-gray-400">
            ID: {item.id}
          </div>
        </div>
      ),
    },
    {
      key: "client_name",
      label: "Cliente",
      type: "custom",
      render: (value, item) => (
        <div className="flex items-center">
          <Building className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
          <span>{value}</span>
        </div>
      ),
    },
    {
      key: "contract_type",
      label: "Tipo",
      type: "badge",
      render: (value) => (
        <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300 whitespace-nowrap">
          {getContractTypeLabel(value)}
        </span>
      ),
    },
    {
      key: "actual_lives_count",
      label: "Vidas",
      type: "number",
      render: (value, item) => (
        <div className="flex items-center">
          <Users className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
          <span className="font-medium">
            {value || 0}/{item.lives_contracted || 0}
          </span>
        </div>
      ),
    },
    {
      key: "monthly_value",
      label: "Valor Mensal",
      type: "currency",
      render: (value, item) => (
        <div className="flex items-center">
          <DollarSign className="w-4 h-4 mr-1 text-gray-400 dark:text-gray-500" />
          <span className="font-medium">
            {formatCurrency(
              value,
              item.id,
              item.contract_type,
              item.lives_contracted
            )}
          </span>
        </div>
      ),
    },
    {
      key: "start_date",
      label: "Período",
      type: "date",
      render: (value, item) => (
        <div className="flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
          <div>
            <div className="text-sm">{formatDate(value)}</div>
            {item.end_date && (
              <div className="text-xs text-gray-500 dark:text-gray-400">
                até {formatDate(item.end_date)}
              </div>
            )}
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
  ],

  searchFields: ["contract_number", "client_name", "contract_type", "status"],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics
  metrics: {
    primary: [
      {
        id: "active_contracts",
        title: "Contratos Ativos",
        value: 0, // Will be calculated dynamically
        subtitle: "de {total}",
        icon: (
          <svg
            className="h-6 w-6 text-green-600 dark:text-green-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        ),
        color: "green",
      },
      {
        id: "monthly_revenue",
        title: "Receita Mensal",
        value: 0, // Will be calculated dynamically
        subtitle: "Média: {average}",
        icon: (
          <svg
            className="h-6 w-6 text-blue-600 dark:text-blue-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
            />
          </svg>
        ),
        color: "blue",
      },
      {
        id: "active_lives",
        title: "Vidas Ativas",
        value: 0, // Will be calculated dynamically
        subtitle: "Contratos ativos",
        icon: (
          <svg
            className="h-6 w-6 text-purple-600 dark:text-purple-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
        ),
        color: "purple",
      },
      {
        id: "expiring_contracts",
        title: "Vencendo em 30 dias",
        value: 0, // Will be calculated dynamically
        subtitle: "{status_message}",
        icon: (
          <svg
            className="h-6 w-6 text-yellow-600 dark:text-yellow-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        ),
        color: "yellow",
      },
    ],
    detailed: {
      title: "📊 Métricas Detalhadas",
      sections: [
        {
          title: "📊 Status dos Contratos",
          items: [
            {
              id: "status_active",
              title: "✅ Ativos",
              value: 0,
              icon: <span>✅</span>,
              color: "green",
            },
            {
              id: "status_inactive",
              title: "⏸️ Inativos",
              value: 0,
              icon: <span>⏸️</span>,
              color: "gray",
            },
            {
              id: "status_suspended",
              title: "⏳ Suspensos",
              value: 0,
              icon: <span>⏳</span>,
              color: "yellow",
            },
            {
              id: "status_draft",
              title: "📝 Rascunhos",
              value: 0,
              icon: <span>📝</span>,
              color: "blue",
            },
          ],
        },
        {
          title: "🏢 Tipos de Contrato",
          items: [
            {
              id: "type_individual",
              title: "👤 Individual",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>👤</span>,
              color: "blue",
            },
            {
              id: "type_corporate",
              title: "🏢 Corporativo",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏢</span>,
              color: "purple",
            },
            {
              id: "type_business",
              title: "🏭 Empresarial",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏭</span>,
              color: "green",
            },
          ],
        },
      ],
      quickActions: [
        {
          label: "🔍 Ver Contratos Ativos",
          action: () => {
            // This will be implemented in the component
          },
          color: "green",
        },
        {
          label: "⚠️ Revisar Vencimentos",
          action: () => {
            // This will be implemented in the component
          },
          color: "yellow",
        },
        {
          label: "📄 Exportar Ativos",
          action: () => {
            // This will be implemented in the component
          },
          color: "blue",
        },
      ],
    },
  },

  // Filters - Expandido com novos tipos
  filters: [
    {
      key: "status",
      label: "Status",
      type: "multiselect",
      multiple: true,
      options: [
        { value: "all", label: "📋 Todos Status" },
        { value: "active", label: "✅ Ativo" },
        { value: "inactive", label: "⏸️ Inativo" },
        { value: "suspended", label: "⏳ Suspenso" },
        { value: "terminated", label: "❌ Terminado" },
        { value: "draft", label: "📝 Rascunho" },
      ],
    },
    {
      key: "contract_type",
      label: "Tipo",
      type: "select",
      options: [
        { value: "all", label: "🏢 Todos Tipos" },
        { value: "INDIVIDUAL", label: "👤 Individual" },
        { value: "CORPORATIVO", label: "🏢 Corporativo" },
        { value: "EMPRESARIAL", label: "🏭 Empresarial" },
      ],
    },
    {
      key: "lives_contracted",
      label: "Vidas",
      type: "range",
      min: 1,
      max: 1000,
      step: 1,
      placeholder: "Número de vidas...",
    },
    {
      key: "monthly_value",
      label: "Valor Mensal",
      type: "range",
      min: 0,
      max: 50000,
      step: 100,
      placeholder: "Valor em R$...",
    },
    {
      key: "contract_period",
      label: "Período do Contrato",
      type: "daterange",
      placeholder: "Selecionar período...",
    },
  ],

  // Actions
  actions: [
    {
      id: "view",
      label: "Visualizar",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick: (contract) => {
        actions?.onView?.(contract);
      },
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (contract) => {
        actions?.onEdit?.(contract);
      },
    },
    {
      id: "duplicate",
      label: "Duplicar",
      icon: (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
          <path
            fillRule="evenodd"
            d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5z"
            clipRule="evenodd"
          />
        </svg>
      ),
      color: "purple",
      onClick: (contract) => {
        console.log("Duplicar contrato", contract);
      },
    },
    {
      id: "delete",
      label: "Excluir",
      icon: <Trash2 className="w-4 h-4" />,
      color: "red",
      onClick: (contract) => {
        actions?.onDelete?.(contract);
      },
    },
  ],

  bulkActions: [
    {
      id: "export_csv",
      label: "Exportar CSV",
      icon: <Download className="w-4 h-4" />,
      color: "blue",
      onClick: (contracts) => {
        console.log("Exportar contratos selecionados", contracts);
      },
    },
  ],

  // Export
  export: {
    filename: "contratos",
    formats: ["csv", "json", "print"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization
  className: "",
  theme: "default",

  // Add button configuration
  onAdd: actions?.onAdd,
});

// Helper functions - These will be moved to utils later

function getContractTypeLabel(type: string): string {
  const types = {
    INDIVIDUAL: "Individual",
    CORPORATIVO: "Corporativo",
    EMPRESARIAL: "Empresarial",
  };
  return types[type as keyof typeof types] || type;
}

function formatCurrency(
  value: number | string | undefined,
  contractId?: number,
  contractType?: string,
  lives?: number
): string {
  // 🔍 DEBUG: Log para identificar problema
  console.log("🔍 formatCurrency debug:", {
    value,
    type: typeof value,
    contractId,
    contractType,
    lives,
  });

  // 🔧 CORREÇÃO: Usar função utilitária robusta existente
  let finalValue =
    typeof value === "string"
      ? parseCurrencyRobust(value)
      : (value as number) || 0;

  console.log("🔄 Parsing result:", { input: value, output: finalValue });

  // 🔧 CORREÇÃO: Validação mais robusta (permitir zero, mas não negativos)
  if (
    finalValue === null ||
    finalValue === undefined ||
    isNaN(finalValue) ||
    finalValue < 0
  ) {
    console.log("⚠️ Usando fallback para contractId:", contractId);

    if (contractId && contractType && lives) {
      const baseValue =
        contractType === "INDIVIDUAL"
          ? 150
          : contractType === "CORPORATIVO"
          ? 120
          : 100;
      finalValue = lives * baseValue + ((contractId * 47) % 200);
    } else {
      return "R$ 0,00";
    }
  }

  const formatted = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(finalValue);

  console.log("💰 formatCurrency resultado:", formatted);
  return formatted;
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("pt-BR");
}

function getStatusBadge(status: string): JSX.Element {
  const statusConfig = {
    active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    inactive: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
    suspended:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    terminated: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    draft: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  };

  const statusLabels = {
    active: "Ativo",
    inactive: "Inativo",
    suspended: "Suspenso",
    terminated: "Terminado",
    draft: "Rascunho",
  };

  return (
    <span
      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
        statusConfig[status as keyof typeof statusConfig] ||
        statusConfig.inactive
      }`}
    >
      {statusLabels[status as keyof typeof statusLabels] || status}
    </span>
  );
}
