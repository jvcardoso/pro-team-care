/**
 * Establishment Clients Table Configuration
 * Defines all settings for the establishment clients data table
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
  Building,
  Calendar,
  Phone,
  Mail,
  MapPin,
  UserCheck,
  UserX,
  FileText as FileContract,
  Heart,
} from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { ClientDetailed, ClientStatus, PersonType } from "../../types";
import { formatTaxId } from "../../utils/formatters";

export const createEstablishmentClientsConfig = (
  establishmentId: number,
  establishmentCode: string
): DataTableConfig<ClientDetailed> => ({
  // Basic Info
  entity: "establishment-clients",
  title: "👥 Clientes do Estabelecimento",
  description: `Gestão de clientes do estabelecimento ${establishmentCode}`,

  // Data Structure
  searchFields: ["person.name", "client_code", "person.tax_id"],
  sortField: "created_at",
  sortDirection: "desc",
  columns: [
    {
      key: "name",
      label: "Cliente",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Users className="h-5 w-5 text-purple-600 dark:text-purple-300" />
            </div>
          </div>
          <div>
            <div className="text-base font-semibold text-gray-900 dark:text-white">
              {item.person?.name || "Nome não informado"}
            </div>
            {item.client_code && (
              <div className="font-mono text-sm font-normal text-gray-500 dark:text-gray-400">
                {item.client_code}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "person.tax_id",
      label: "CPF/CNPJ",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div className="font-mono text-sm">
          {item.person?.tax_id
            ? formatTaxId(item.person.tax_id)
            : "Não informado"}
        </div>
      ),
    },
    {
      key: "person.person_type",
      label: "Tipo",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <span
          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            item.person?.person_type === PersonType.PF
              ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
              : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
          }`}
        >
          {item.person?.person_type === PersonType.PF
            ? "Pessoa Física"
            : "Pessoa Jurídica"}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <span
          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
            item.status === ClientStatus.ACTIVE
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
          }`}
        >
          {item.status === ClientStatus.ACTIVE ? "Ativo" : "Inativo"}
        </span>
      ),
    },
    {
      key: "created_at",
      label: "Cadastrado em",
      type: "date",
      sortable: true,
      render: (value) => (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {value
            ? new Date(value).toLocaleDateString("pt-BR")
            : "Não informado"}
        </div>
      ),
    },
  ],

  // Actions
  actions: {
    // Bulk actions
    bulk: [
      {
        key: "export",
        label: "Exportar Selecionados",
        icon: <Download className="h-4 w-4" />,
        variant: "secondary",
        action: async (selectedItems) => {
          console.log("Exportando clientes:", selectedItems);
          // Implement export logic
        },
      },
      {
        key: "activate",
        label: "Ativar Selecionados",
        icon: <UserCheck className="h-4 w-4" />,
        variant: "success",
        action: async (selectedItems) => {
          console.log("Ativando clientes:", selectedItems);
          // Implement activation logic
        },
      },
      {
        key: "deactivate",
        label: "Inativar Selecionados",
        icon: <UserX className="h-4 w-4" />,
        variant: "warning",
        action: async (selectedItems) => {
          console.log("Inativando clientes:", selectedItems);
          // Implement deactivation logic
        },
      },
    ],

    // Row actions
    row: [
      {
        key: "view",
        label: "Ver Detalhes",
        icon: <Eye className="h-4 w-4" />,
        variant: "secondary",
        action: (item) => {
          window.location.href = `/admin/clientes/${item.id}`;
        },
      },
      {
        key: "edit",
        label: "Editar",
        icon: <Edit className="h-4 w-4" />,
        variant: "primary",
        action: (item) => {
          window.location.href = `/admin/clientes/${item.id}/edit`;
        },
      },
      {
        key: "contracts",
        label: "Contratos",
        icon: <FileContract className="h-4 w-4" />,
        variant: "secondary",
        action: (item) => {
          window.location.href = `/admin/contratos?clientId=${item.id}`;
        },
      },
      {
        key: "toggle-status",
        label: (item) =>
          item.status === ClientStatus.ACTIVE ? "Inativar" : "Ativar",
        icon: (item) =>
          item.status === ClientStatus.ACTIVE ? (
            <UserX className="h-4 w-4" />
          ) : (
            <UserCheck className="h-4 w-4" />
          ),
        variant: (item) =>
          item.status === ClientStatus.ACTIVE ? "warning" : "success",
        action: async (item) => {
          console.log(
            `${
              item.status === ClientStatus.ACTIVE ? "Inativando" : "Ativando"
            } cliente:`,
            item
          );
          // Implement toggle status logic
        },
      },
    ],

    // Toolbar actions
    toolbar: [
      {
        key: "add",
        label: "Novo Cliente",
        icon: <Plus className="h-4 w-4" />,
        variant: "primary",
        action: () => {
          window.location.href = `/admin/clientes?establishmentId=${establishmentId}&establishmentCode=${establishmentCode}&action=create`;
        },
      },
    ],
  },

  // Filters
  filters: [
    {
      key: "status",
      label: "Status",
      type: "select",
      options: [
        { value: "", label: "Todos" },
        { value: ClientStatus.ACTIVE, label: "Ativo" },
        { value: ClientStatus.INACTIVE, label: "Inativo" },
      ],
    },
    {
      key: "person_type",
      label: "Tipo de Pessoa",
      type: "select",
      options: [
        { value: "", label: "Todos" },
        { value: PersonType.INDIVIDUAL, label: "Pessoa Física" },
        { value: PersonType.LEGAL, label: "Pessoa Jurídica" },
      ],
    },
    {
      key: "created_at_range",
      label: "Período de Cadastro",
      type: "date-range",
    },
  ],

  // Search
  searchConfig: {
    placeholder: "Buscar por nome, código ou CPF/CNPJ...",
    fields: ["person.name", "client_code", "person.tax_id"],
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [5, 10, 20, 50],

  // Sorting
  defaultSort: {
    field: "created_at",
    direction: "desc",
  },

  // Layout
  layout: {
    showHeader: true,
    showFilters: true,
    showSearch: true,
    showPagination: true,
    showBulkActions: true,
    compactMode: false,
  },

  // Disable old add button since we use toolbar actions
  showAddButton: false,

  // Theme
  theme: {
    primaryColor: "purple",
    borderRadius: "lg",
  },

  // Metrics
  metrics: {
    primary: [
      {
        id: "total_clients",
        title: "Total de Clientes",
        value: 0, // Will be calculated dynamically
        subtitle: "do estabelecimento",
        icon: (
          <Users className="h-6 w-6 text-purple-600 dark:text-purple-300" />
        ),
        color: "purple",
      },
      {
        id: "active_clients",
        title: "Clientes Ativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: (
          <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
        ),
        color: "green",
      },
      {
        id: "inactive_clients",
        title: "Clientes Inativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: <UserX className="h-6 w-6 text-red-600 dark:text-red-300" />,
        color: "red",
      },
    ],
    detailed: {
      title: "📊 Métricas Detalhadas de Clientes do Estabelecimento",
      sections: [
        {
          title: "📊 Status dos Clientes",
          items: [
            {
              id: "status_active",
              title: "✅ Ativos",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <UserCheck className="h-5 w-5" />,
              color: "green",
            },
            {
              id: "status_inactive",
              title: "❌ Inativos",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <UserX className="h-5 w-5" />,
              color: "red",
            },
          ],
        },
        {
          title: "🏢 Tipo de Pessoa",
          items: [
            {
              id: "type_pf",
              title: "👤 Pessoa Física",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>👤</span>,
              color: "blue",
            },
            {
              id: "type_pj",
              title: "🏢 Pessoa Jurídica",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏢</span>,
              color: "purple",
            },
          ],
        },
      ],
    },
    quickActions: [
      {
        label: "🔍 Ver Clientes Ativos",
        action: () => {
          // This will be implemented in the component
        },
        color: "green",
      },
      {
        label: "⚠️ Revisar Inativos",
        action: () => {
          // This will be implemented in the component
        },
        color: "yellow",
      },
      {
        label: "📄 Exportar Lista",
        action: () => {
          // This will be implemented in the component
        },
        color: "blue",
      },
    ],
  },

  // Export Configuration
  export: {
    filename: "clientes_estabelecimento",
    formats: ["csv", "json", "print"],
  },

  // API Integration
  api: {
    // These will be handled by the parent component
    fetchData: undefined,
    updateItem: undefined,
    deleteItem: undefined,
  },
});
