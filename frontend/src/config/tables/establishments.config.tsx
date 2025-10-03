/**
 * Establishments Table Configuration
 * Defines all settings for the establishments data table
 */

import React from "react";
import {
  Building2,
  Building,
  MapPin,
  Calendar,
  Eye,
  Edit,
  Trash2,
  UserCheck,
  UserX,
  ArrowUpDown,
} from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { getStatusBadge, getStatusLabel } from "../../utils/statusUtils";
import { formatTaxId } from "../../utils/formatters";

// Define Establishment type based on API structure
export interface Establishment {
  id: number;
  code: string;
  type: string;
  category: string;
  is_active: boolean;
  is_principal: boolean;
  created_at: string;
  updated_at?: string;
  company_id: number;
  company_name: string;
  company_tax_id?: string;
  person?: {
    name: string;
    tax_id?: string;
  };
}

export const createEstablishmentsConfig = (
  navigate?: (path: string) => void,
  actionHandlers?: {
    onToggleStatus?: (establishmentId: number, newStatus: boolean) => void;
    onDelete?: (establishmentId: number) => void;
  }
): DataTableConfig<Establishment> => ({
  // Basic Info
  entity: "Estabelecimento",
  title: "🏥 Dashboard de Estabelecimentos",
  description: "Gestão completa de estabelecimentos cadastrados no sistema",

  // Data Structure
  columns: [
    {
      key: "name",
      label: "Estabelecimento",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div>
          <div className="text-base font-semibold">
            {item.person?.name || item.code}
          </div>
          <div className="font-normal text-gray-500 text-sm">
            Código: {item.code}
          </div>
          {item.is_principal && (
            <div className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 mt-1">
              Principal
            </div>
          )}
        </div>
      ),
    },
    {
      key: "company_name",
      label: "Empresa",
      type: "text",
      render: (value, item) => (
        <div>
          <div className="text-sm font-medium">{value}</div>
          {item.company_tax_id && (
            <div className="text-xs text-gray-500 font-mono">
              {formatTaxId(item.company_tax_id)}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "type_category",
      label: "Tipo/Categoria",
      type: "custom",
      render: (value, item) => (
        <div>
          <div className="text-sm font-medium capitalize">{item.type}</div>
          <div className="text-xs text-gray-500 capitalize">
            {item.category}
          </div>
        </div>
      ),
    },
    {
      key: "is_active",
      label: "Status",
      type: "badge",
      render: (value) => (
        <span className={getStatusBadge(value ? "active" : "inactive")}>
          {getStatusLabel(value ? "active" : "inactive")}
        </span>
      ),
    },
    {
      key: "created_at",
      label: "Criado em",
      type: "date",
      render: (value) => (
        <div className="flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <span>{new Date(value).toLocaleDateString("pt-BR")}</span>
        </div>
      ),
    },
  ],

  searchFields: ["person.name", "code", "company_name", "type", "category"],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics
  metrics: {
    primary: [
      {
        id: "total_establishments",
        title: "Total Estabelecimentos",
        value: 0, // Will be calculated dynamically
        subtitle: "cadastrados",
        icon: (
          <Building2 className="h-6 w-6 text-blue-600 dark:text-blue-300" />
        ),
        color: "blue",
      },
      {
        id: "active_establishments",
        title: "Estabelecimentos Ativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: (
          <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
        ),
        color: "green",
      },
      {
        id: "inactive_establishments",
        title: "Estabelecimentos Inativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: <UserX className="h-6 w-6 text-gray-600 dark:text-gray-300" />,
        color: "gray",
      },
      {
        id: "principal_establishments",
        title: "Estabelecimentos Principais",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: (
          <Building className="h-6 w-6 text-purple-600 dark:text-purple-300" />
        ),
        color: "purple",
      },
    ],
    detailed: {
      title: "📊 Estatísticas de Estabelecimentos",
      sections: [
        {
          title: "📈 Status dos Estabelecimentos",
          items: [
            {
              id: "active_establishments",
              title: "✅ Ativos",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>✅</span>,
              color: "green",
            },
            {
              id: "inactive_establishments",
              title: "⏸️ Inativos",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>⏸️</span>,
              color: "gray",
            },
          ],
        },
        {
          title: "🏢 Tipos de Estabelecimento",
          items: [
            {
              id: "principal_establishments",
              title: "🏛️ Principais",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏛️</span>,
              color: "purple",
            },
            {
              id: "matriz_establishments",
              title: "🏢 Matrizes",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏢</span>,
              color: "blue",
            },
            {
              id: "filial_establishments",
              title: "🏪 Filiais",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏪</span>,
              color: "orange",
            },
          ],
        },
        {
          title: "🏥 Categorias",
          items: [
            {
              id: "clinica_establishments",
              title: "🏥 Clínicas",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏥</span>,
              color: "red",
            },
            {
              id: "hospital_establishments",
              title: "🏥 Hospitais",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🏥</span>,
              color: "red",
            },
            {
              id: "laboratorio_establishments",
              title: "🔬 Laboratórios",
              value: 0,
              subtitle: "({percentage}%)",
              icon: <span>🔬</span>,
              color: "green",
            },
          ],
        },
      ],
      quickActions: [
        {
          label: "📊 Exportar Ativos",
          action: () => {
            // This will be implemented in the component
          },
          color: "green",
        },
        {
          label: "📋 Relatório Geral",
          action: () => {
            // This will be implemented in the component
          },
          color: "purple",
        },
      ],
    },
  },

  // Filters
  filters: [
    {
      key: "is_active",
      label: "Status",
      type: "select",
      options: [
        { value: "all", label: "📋 Todos os status" },
        { value: true, label: "✅ Ativo" },
        { value: false, label: "⏸️ Inativo" },
      ],
    },
    {
      key: "company_id",
      label: "Empresa",
      type: "select",
      options: [
        { value: "all", label: "🏢 Todas as empresas" },
        // Companies will be loaded dynamically in the component
      ],
      dynamic: true, // Mark as dynamic to load options from API
    },
    {
      key: "type",
      label: "Tipo",
      type: "select",
      options: [
        { value: "all", label: "🏢 Todos os tipos" },
        { value: "matriz", label: "🏢 Matriz" },
        { value: "filial", label: "🏪 Filial" },
        { value: "unidade", label: "🏥 Unidade" },
        { value: "posto", label: "🏥 Posto" },
      ],
    },
    {
      key: "category",
      label: "Categoria",
      type: "select",
      options: [
        { value: "all", label: "🏥 Todas as categorias" },
        { value: "clinica", label: "🏥 Clínica" },
        { value: "hospital", label: "🏥 Hospital" },
        { value: "laboratorio", label: "🔬 Laboratório" },
        { value: "farmacia", label: "💊 Farmácia" },
        { value: "consultorio", label: "🏥 Consultório" },
        { value: "upa", label: "🏥 UPA" },
        { value: "ubs", label: "🏥 UBS" },
        { value: "outro", label: "🏢 Outro" },
      ],
    },
  ],

  // Actions
  actions: [
    {
      id: "view",
      label: "Ver Detalhes",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick: (establishment) => {
        // Navegar para página de detalhes do estabelecimento
        if (navigate) {
          navigate(`/admin/estabelecimentos/${establishment.id}`);
        } else {
          window.location.href = `/admin/estabelecimentos/${establishment.id}`;
        }
      },
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (establishment) => {
        // Navegar para edição
        if (navigate) {
          navigate(
            `/admin/estabelecimentos?establishmentId=${establishment.id}&action=edit`
          );
        } else {
          window.location.href = `/admin/estabelecimentos?establishmentId=${establishment.id}&action=edit`;
        }
      },
    },
    {
      id: "toggle_status",
      label: "Alternar Status",
      icon: <ArrowUpDown className="w-4 h-4" />,
      color: "orange",
      onClick: (establishment) => {
        if (actionHandlers?.onToggleStatus) {
          actionHandlers.onToggleStatus(
            establishment.id,
            !establishment.is_active
          );
        }
      },
    },
    {
      id: "delete",
      label: "Excluir",
      icon: <Trash2 className="w-4 h-4" />,
      color: "red",
      onClick: (establishment) => {
        if (actionHandlers?.onDelete) {
          actionHandlers.onDelete(establishment.id);
        }
      },
    },
  ],

  // Show add button
  showAddButton: true,
  onAdd: () => {
    if (navigate) {
      navigate("/admin/estabelecimentos?action=create");
    }
  },

  // Export
  export: {
    filename: "estabelecimentos",
    formats: ["csv", "json", "print"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization
  className: "",
  theme: "default",
});

// Versão padrão para compatibilidade
export const establishmentsConfig = createEstablishmentsConfig();

export default establishmentsConfig;
