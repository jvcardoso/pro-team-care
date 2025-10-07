/**
 * Contract Lives Table Configuration
 * Defines all settings for the contract lives data table
 *
 * ATUALIZADO: Usando tipos do backend (contract-lives.types.ts)
 */

import React from "react";
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
  User,
  Calendar,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  History,
  ArrowRightLeft,
} from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import type {
  ContractLife,
  ContractLivesTableCallbacks,
} from "../../types/contract-lives.types";

// Re-export do tipo para compatibilidade
export type { ContractLife };

export const createContractLivesConfig = (actions?: {
  onView?: (life: ContractLife) => void;
  onEdit?: (life: ContractLife) => void;
  onDelete?: (life: ContractLife) => void;
  onAdd?: () => void;
  onSubstitute?: (life: ContractLife) => void;
  onViewTimeline?: (life: ContractLife) => void;
}): DataTableConfig<ContractLife> => ({
  // Basic Info
  entity: "vida",
  title: "👥 Gestão de Vidas dos Contratos",
  description:
    "Visualização e gerenciamento de todas as vidas cadastradas nos contratos",

  // Data Structure
  columns: [
    {
      key: "person_name",
      label: "Pessoa",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div>
          <div className="text-base font-semibold flex items-center">
            <User className="w-4 h-4 mr-2 text-gray-400" />
            {value}
          </div>
          {item.person_cpf && (
            <div className="font-normal text-gray-500 text-sm">
              CPF: {item.person_cpf}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "contract_number",
      label: "Contrato",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div>
          <div className="text-base font-semibold">{value}</div>
          {item.client_name && (
            <div className="font-normal text-gray-500 text-sm">
              {item.client_name}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "start_date",
      label: "Período",
      type: "date",
      sortable: true,
      render: (value, item) => (
        <div className="flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <div>
            <div className="text-sm">{formatDate(value)}</div>
            {item.end_date && (
              <div className="text-xs text-gray-500">
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
      sortable: true,
      render: (value) => getStatusBadge(value),
    },
    {
      key: "notes",
      label: "Observações",
      type: "text",
      render: (value) => (
        <div className="max-w-xs truncate text-sm">{value || "-"}</div>
      ),
    },
  ],

  searchFields: [
    "person_name",
    "person_cpf",
    "contract_number",
    "client_name",
    "notes",
  ],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics
  metrics: {
    primary: [
      {
        id: "total",
        title: "Total de Vidas",
        value: 0,
        subtitle: "Cadastradas no sistema",
        icon: <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />,
        color: "blue",
      },
      {
        id: "active",
        title: "Vidas Ativas",
        value: 0,
        subtitle: "Em contratos ativos",
        icon: (
          <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-300" />
        ),
        color: "green",
      },
      {
        id: "inactive",
        title: "Vidas Inativas",
        value: 0,
        subtitle: "Não ativas",
        icon: <XCircle className="h-6 w-6 text-gray-600 dark:text-gray-300" />,
        color: "gray",
      },
      {
        id: "recent_week",
        title: "Novas Esta Semana",
        value: 0,
        subtitle: "Adicionadas recentemente",
        icon: (
          <Calendar className="h-6 w-6 text-purple-600 dark:text-purple-300" />
        ),
        color: "purple",
      },
    ],
    detailed: {
      title: "📊 Métricas Detalhadas das Vidas",
      sections: [
        {
          title: "📊 Status das Vidas",
          items: [
            {
              id: "status_active",
              title: "✅ Ativas",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>✅</span>,
              color: "green",
            },
            {
              id: "status_inactive",
              title: "⏸️ Inativas",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>⏸️</span>,
              color: "gray",
            },
            {
              id: "status_suspended",
              title: "⏳ Suspensas",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>⏳</span>,
              color: "yellow",
            },
            {
              id: "status_terminated",
              title: "❌ Terminadas",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>❌</span>,
              color: "red",
            },
          ],
        },
      ],
      quickActions: [
        {
          label: "👥 Ver Vidas Ativas",
          action: () => {
            // This will be implemented in the component
          },
          color: "green",
        },
        {
          label: "📄 Exportar Todas",
          action: () => {
            // This will be implemented in the component
          },
          color: "blue",
        },
      ],
    },
  },

  // Filters
  filters: [
    {
      key: "status",
      label: "Status",
      type: "multiselect",
      multiple: true,
      options: [
        { value: "all", label: "📋 Todos Status" },
        { value: "active", label: "✅ Ativa" },
        { value: "inactive", label: "⏸️ Inativa" },
        { value: "substituted", label: "🔄 Substituída" },
        { value: "cancelled", label: "❌ Cancelada" },
      ],
    },
    {
      key: "contract_number",
      label: "Número do Contrato",
      type: "text",
      placeholder: "Buscar por contrato...",
    },
    {
      key: "client_name",
      label: "Cliente",
      type: "text",
      placeholder: "Buscar por cliente...",
    },
    {
      key: "person_name",
      label: "Nome da Pessoa",
      type: "text",
      placeholder: "Buscar por nome...",
    },
    {
      key: "person_cpf",
      label: "CPF",
      type: "text",
      placeholder: "Buscar por CPF...",
    },
  ],

  // Actions
  actions: [
    {
      id: "view_timeline",
      label: "Ver Histórico",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick: (life) => {
        actions?.onViewTimeline?.(life);
      },
    },
    {
      id: "substitute",
      label: "Substituir",
      icon: (
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
          />
        </svg>
      ),
      color: "purple",
      onClick: (life) => {
        actions?.onSubstitute?.(life);
      },
      condition: (life) =>
        life.status === "active" && life.substitution_allowed,
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (life) => {
        actions?.onEdit?.(life);
      },
    },
    {
      id: "delete",
      label: "Remover",
      icon: <Trash2 className="w-4 h-4" />,
      color: "red",
      onClick: (life) => {
        actions?.onDelete?.(life);
      },
      condition: (life) => life.status === "active",
    },
  ],

  bulkActions: [
    {
      id: "export_csv",
      label: "Exportar CSV",
      icon: <Download className="w-4 h-4" />,
      color: "blue",
      onClick: (lives) => {
        console.log("Exportar vidas selecionadas", lives);
      },
    },
  ],

  // Export
  export: {
    filename: "vidas_contratos",
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

// Helper functions

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("pt-BR");
}

function getStatusBadge(status: string): JSX.Element {
  const statusConfig = {
    active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    inactive: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
    substituted:
      "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    cancelled: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  };

  const statusLabels = {
    active: "Ativa",
    inactive: "Inativa",
    substituted: "Substituída",
    cancelled: "Cancelada",
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
