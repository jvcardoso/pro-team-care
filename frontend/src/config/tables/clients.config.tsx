/**
 * Clients Table Configuration
 * Defines all settings for the clients data table
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

export const clientsConfig: DataTableConfig<ClientDetailed> = {
  // Basic Info
  entity: "clientes",
  title: "👥 Dashboard de Clientes",
  description: "Gestão completa de clientes e suas informações",

  // Data Structure
  columns: [
    {
      key: "name",
      label: "Cliente",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div>
          <div className="text-base font-semibold">{value}</div>
          {item.client_code && (
            <div className="font-normal text-gray-500">
              Código: {item.client_code}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "tax_id",
      label: "Documento",
      type: "text",
      render: (value, item) => (
        <div>
          <div className="text-sm font-mono">{formatTaxId(value)}</div>
          <div className="text-xs text-gray-500">
            {item.person_type === PersonType.PF
              ? "Pessoa Física"
              : "Pessoa Jurídica"}
          </div>
        </div>
      ),
    },
    {
      key: "phones",
      label: "Contatos",
      type: "custom",
      render: (phones, item) => (
        <div className="flex flex-col gap-1">
          <div className="flex items-center text-sm text-muted-foreground">
            <Phone className="h-3 w-3 mr-1" />
            {(phones as any[])?.length || 0} telefone
            {(phones as any[])?.length !== 1 ? "s" : ""}
          </div>
          <div className="flex items-center text-sm text-muted-foreground">
            <Mail className="h-3 w-3 mr-1" />
            {(item.emails as any[])?.length || 0} email
            {(item.emails as any[])?.length !== 1 ? "s" : ""}
          </div>
          <div className="flex items-center text-sm text-muted-foreground">
            <MapPin className="h-3 w-3 mr-1" />
            {(item.addresses as any[])?.length || 0} endereço
            {(item.addresses as any[])?.length !== 1 ? "s" : ""}
          </div>
        </div>
      ),
    },
    {
      key: "establishment_name",
      label: "Estabelecimento",
      type: "custom",
      render: (value, item) => (
        <div>
          <div className="text-sm">{value}</div>
          <div className="text-xs text-gray-500">{item.establishment_code}</div>
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

  searchFields: ["name", "tax_id", "client_code"],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics
  metrics: {
    primary: [
      {
        id: "total_clients",
        title: "Total de Clientes",
        value: 0, // Will be calculated dynamically
        subtitle: "de {total}",
        icon: <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />,
        color: "blue",
      },
      {
        id: "active_clients",
        title: "Clientes Ativos",
        value: 0, // Will be calculated dynamically
        subtitle: "de {total}",
        icon: (
          <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
        ),
        color: "green",
      },
      {
        id: "inactive_clients",
        title: "Clientes Inativos",
        value: 0, // Will be calculated dynamically
        subtitle: "de {total}",
        icon: <UserX className="h-6 w-6 text-gray-600 dark:text-gray-300" />,
        color: "gray",
      },
      {
        id: "on_hold_clients",
        title: "Em Espera",
        value: 0, // Will be calculated dynamically
        subtitle: "de {total}",
        icon: (
          <Calendar className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
        ),
        color: "yellow",
      },
    ],
    detailed: {
      title: "📊 Métricas Detalhadas de Clientes",
      sections: [
        {
          title: "📊 Status dos Clientes",
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
              id: "status_on_hold",
              title: "⏳ Em Espera",
              value: 0,
              icon: <span>⏳</span>,
              color: "yellow",
            },
            {
              id: "status_archived",
              title: "📁 Arquivados",
              value: 0,
              icon: <span>📁</span>,
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
        { value: ClientStatus.ACTIVE, label: "✅ Ativo" },
        { value: ClientStatus.INACTIVE, label: "⏸️ Inativo" },
        { value: ClientStatus.ON_HOLD, label: "⏳ Em Espera" },
        { value: ClientStatus.ARCHIVED, label: "📁 Arquivado" },
      ],
    },
    {
      key: "person_type",
      label: "Tipo de Pessoa",
      type: "select",
      options: [
        { value: "all", label: "🏢 Todos os Tipos" },
        { value: PersonType.PF, label: "👤 Pessoa Física" },
        { value: PersonType.PJ, label: "🏢 Pessoa Jurídica" },
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
      onClick: (client) => {
        console.log("Ver detalhes do cliente", client);
      },
    },
    {
      id: "view_contracts",
      label: "Ver Contratos",
      icon: <FileContract className="w-4 h-4" />,
      color: "purple",
      onClick: (client) => {
        console.log("Ver contratos do cliente", client);
      },
    },
    {
      id: "view_lives",
      label: "Ver Vidas",
      icon: <Heart className="w-4 h-4" />,
      color: "red",
      onClick: (client) => {
        console.log("Ver vidas do cliente", client);
      },
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (client) => {
        console.log("Editar cliente", client);
      },
    },
    {
      id: "toggle_status",
      label: "Ativar/Inativar",
      icon: <UserCheck className="w-4 h-4" />,
      color: "success",
      onClick: (client) => {
        console.log("Toggle status do cliente", client);
      },
    },
    {
      id: "delete",
      label: "Excluir",
      icon: <Trash2 className="w-4 h-4" />,
      color: "red",
      onClick: (client) => {
        console.log("Excluir cliente", client);
      },
    },
  ],

  // Export
  export: {
    filename: "clientes",
    formats: ["csv", "json", "print"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization
  className: "",
  theme: "default",
};

// Helper functions

function formatTaxId(taxId: string): string {
  if (!taxId) return "";

  const clean = taxId.replace(/\D/g, "");

  if (clean.length === 11) {
    // CPF: 000.000.000-00
    return clean.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  } else if (clean.length === 14) {
    // CNPJ: 00.000.000/0000-00
    return clean.replace(
      /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
      "$1.$2.$3/$4-$5"
    );
  }

  return taxId;
}

function getStatusBadge(status: ClientStatus): JSX.Element {
  const statusConfig = {
    [ClientStatus.ACTIVE]:
      "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    [ClientStatus.INACTIVE]:
      "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
    [ClientStatus.ON_HOLD]:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    [ClientStatus.ARCHIVED]:
      "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  };

  const statusLabels = {
    [ClientStatus.ACTIVE]: "Ativo",
    [ClientStatus.INACTIVE]: "Inativo",
    [ClientStatus.ON_HOLD]: "Em Espera",
    [ClientStatus.ARCHIVED]: "Arquivado",
  };

  return (
    <span
      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
        statusConfig[status] || statusConfig[ClientStatus.INACTIVE]
      }`}
    >
      {statusLabels[status] || status}
    </span>
  );
}
