/**
 * Company Clients Table Configuration
 * Configuração simplificada para aba de clientes em CompanyDetails
 * SEM métricas, apenas tabela limpa
 */

import React from "react";
import { Eye, Calendar, Building } from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { ClientDetailed, ClientStatus, PersonType } from "../../types";

export const createCompanyClientsConfig = (actions?: {
  onView?: (client: ClientDetailed) => void;
}): DataTableConfig<ClientDetailed> => ({
  // Basic Info
  entity: "clientes",
  title: "",
  description: "",

  // Data Structure - APENAS COLUNAS SOLICITADAS
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
            <div className="font-normal text-gray-500 text-sm">
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
      key: "establishment_name",
      label: "Estabelecimento",
      type: "custom",
      sortable: true,
      render: (value, item) => (
        <div className="flex items-center">
          <Building className="w-4 h-4 mr-2 text-gray-400" />
          <div>
            <div className="text-sm">{value || "N/A"}</div>
            {item.establishment_code && (
              <div className="text-xs text-gray-500">
                {item.establishment_code}
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
      key: "created_at",
      label: "Criado em",
      type: "date",
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <span className="text-sm">
            {new Date(value).toLocaleDateString("pt-BR")}
          </span>
        </div>
      ),
    },
  ],

  // Search
  searchFields: ["name", "tax_id", "client_code"],
  sortField: "name",
  sortDirection: "asc",

  // NO METRICS/CARDS - objeto vazio para compatibilidade com useDataTable
  metrics: {
    primary: [], // Sem métricas = array vazio
    detailed: undefined, // Sem detalhamento
  },

  // Filters (opcional, manter simples)
  filters: [
    {
      key: "status",
      label: "Status",
      type: "select",
      options: [
        { value: "all", label: "Todos Status" },
        { value: ClientStatus.ACTIVE, label: "✅ Ativo" },
        { value: ClientStatus.INACTIVE, label: "⏸️ Inativo" },
        { value: ClientStatus.ON_HOLD, label: "⏳ Em Espera" },
        { value: ClientStatus.ARCHIVED, label: "📁 Arquivado" },
      ],
    },
  ],

  // Actions - APENAS "VER"
  actions: [
    {
      id: "view",
      label: "Ver",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick:
        actions?.onView ||
        ((client) => {
          console.log("Ver cliente", client);
        }),
    },
  ],

  // Export
  export: {
    filename: "clientes-empresa",
    formats: ["csv", "json"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization
  className: "",
  theme: "default",
});

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
