/**
 * Table Config Builder - Helper para criar configurações de tabela reutilizáveis
 * Facilita a criação de configs padronizadas com overrides específicos
 */

import {
  DataTableConfig,
  BaseEntity,
  DataTableColumn,
  DataTableFilter,
  DataTableAction,
} from "../types/dataTable.types";

// ===============================
// DEFAULT CONFIGURATIONS
// ===============================

const defaultColumns: DataTableColumn[] = [
  {
    key: "id",
    label: "ID",
    type: "number",
    sortable: true,
    width: "w-20",
  },
  {
    key: "created_at",
    label: "Criado em",
    type: "date",
    sortable: true,
    width: "w-32",
  },
  {
    key: "status",
    label: "Status",
    type: "badge",
    sortable: true,
    width: "w-24",
  },
];

const defaultFilters: DataTableFilter[] = [
  {
    key: "status",
    label: "Status",
    type: "select",
    options: [
      { value: "all", label: "📋 Todos Status" },
      { value: "active", label: "✅ Ativo" },
      { value: "inactive", label: "⏸️ Inativo" },
    ],
  },
];

const defaultActions: DataTableAction[] = [
  {
    id: "view",
    label: "Visualizar",
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
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
        />
      </svg>
    ),
    color: "blue",
    onClick: (item) => console.log("Ver item:", item),
  },
  {
    id: "edit",
    label: "Editar",
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
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
        />
      </svg>
    ),
    color: "yellow",
    onClick: (item) => console.log("Editar item:", item),
  },
  {
    id: "delete",
    label: "Excluir",
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
          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
        />
      </svg>
    ),
    color: "red",
    onClick: (item) => console.log("Excluir item:", item),
  },
];

const defaultConfig: Partial<DataTableConfig> = {
  // Data Structure
  columns: defaultColumns,
  searchFields: ["id", "status"],
  sortField: "created_at",
  sortDirection: "desc",

  // Metrics - Basic template
  metrics: {
    primary: [
      {
        id: "total",
        title: "Total de Itens",
        value: 0,
        subtitle: "no sistema",
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
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        ),
        color: "blue",
      },
      {
        id: "active",
        title: "Ativos",
        value: 0,
        subtitle: "em uso",
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
    ],
  },

  // Filters
  filters: defaultFilters,

  // Actions
  actions: defaultActions,
  bulkActions: [
    {
      id: "export_csv",
      label: "Exportar CSV",
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
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      ),
      color: "blue",
      onClick: (items) => console.log("Exportar itens:", items),
    },
  ],

  // Export
  export: {
    filename: "data",
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

// ===============================
// BUILDER FUNCTIONS
// ===============================

/**
 * Cria uma configuração de tabela mesclando configurações padrão com overrides
 */
export function createTableConfig<T extends BaseEntity>(
  overrides: Partial<DataTableConfig<T>>
): DataTableConfig<T> {
  return {
    ...defaultConfig,
    ...overrides,
    // Merge arrays instead of replacing
    columns: overrides.columns || defaultConfig.columns || [],
    filters: overrides.filters || defaultConfig.filters || [],
    actions: overrides.actions || defaultConfig.actions || [],
    searchFields: overrides.searchFields || defaultConfig.searchFields || [],
    // Deep merge metrics if provided
    metrics: overrides.metrics
      ? {
          ...defaultConfig.metrics,
          ...overrides.metrics,
          primary:
            overrides.metrics.primary || defaultConfig.metrics?.primary || [],
        }
      : defaultConfig.metrics || { primary: [] },
    // Deep merge export settings
    export: overrides.export
      ? {
          ...defaultConfig.export,
          ...overrides.export,
        }
      : defaultConfig.export || {
          filename: "data",
          formats: ["csv"],
          includeFiltered: true,
        },
  } as DataTableConfig<T>;
}

/**
 * Builder para configurações específicas de contratos
 */
export function createContractsConfig<T extends BaseEntity>(
  overrides?: Partial<DataTableConfig<T>>
): DataTableConfig<T> {
  const contractsDefaults: Partial<DataTableConfig<T>> = {
    entity: "contracts",
    title: "Contratos",
    description: "Gestão de contratos do sistema",
    searchFields: ["contract_number", "client_name", "status"] as (keyof T)[],
    export: {
      filename: "contratos",
      formats: ["csv", "json", "print"],
      includeFiltered: true,
    },
  };

  return createTableConfig({
    ...contractsDefaults,
    ...overrides,
  });
}

/**
 * Builder para configurações específicas de clientes
 */
export function createClientsConfig<T extends BaseEntity>(
  overrides?: Partial<DataTableConfig<T>>
): DataTableConfig<T> {
  const clientsDefaults: Partial<DataTableConfig<T>> = {
    entity: "clients",
    title: "Clientes",
    description: "Gestão de clientes do sistema",
    searchFields: ["name", "email", "document", "status"] as (keyof T)[],
    export: {
      filename: "clientes",
      formats: ["csv", "json", "print"],
      includeFiltered: true,
    },
  };

  return createTableConfig({
    ...clientsDefaults,
    ...overrides,
  });
}

/**
 * Builder para configurações específicas de usuários
 */
export function createUsersConfig<T extends BaseEntity>(
  overrides?: Partial<DataTableConfig<T>>
): DataTableConfig<T> {
  const usersDefaults: Partial<DataTableConfig<T>> = {
    entity: "users",
    title: "Usuários",
    description: "Gestão de usuários do sistema",
    searchFields: ["name", "email", "role", "status"] as (keyof T)[],
    export: {
      filename: "usuarios",
      formats: ["csv", "json"],
      includeFiltered: true,
    },
  };

  return createTableConfig({
    ...usersDefaults,
    ...overrides,
  });
}

// ===============================
// COLUMN BUILDERS
// ===============================

/**
 * Helper para criar coluna de ID padrão
 */
export const createIdColumn = (
  options?: Partial<DataTableColumn>
): DataTableColumn => ({
  key: "id",
  label: "ID",
  type: "number",
  sortable: true,
  width: "w-20",
  ...options,
});

/**
 * Helper para criar coluna de nome/título
 */
export const createNameColumn = (
  key: string = "name",
  options?: Partial<DataTableColumn>
): DataTableColumn => ({
  key: key as any,
  label: "Nome",
  type: "text",
  sortable: true,
  width: "w-64",
  ...options,
});

/**
 * Helper para criar coluna de status
 */
export const createStatusColumn = (
  options?: Partial<DataTableColumn>
): DataTableColumn => ({
  key: "status",
  label: "Status",
  type: "badge",
  sortable: true,
  width: "w-24",
  render: (value) => (
    <span
      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
        value === "active"
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
          : value === "inactive"
          ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
          : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
      }`}
    >
      {value === "active" ? "Ativo" : value === "inactive" ? "Inativo" : value}
    </span>
  ),
  ...options,
});

/**
 * Helper para criar coluna de data
 */
export const createDateColumn = (
  key: string,
  label: string,
  options?: Partial<DataTableColumn>
): DataTableColumn => ({
  key: key as any,
  label,
  type: "date",
  sortable: true,
  width: "w-32",
  render: (value) =>
    value ? new Date(value).toLocaleDateString("pt-BR") : "-",
  ...options,
});

export default {
  createTableConfig,
  createContractsConfig,
  createClientsConfig,
  createUsersConfig,
  createIdColumn,
  createNameColumn,
  createStatusColumn,
  createDateColumn,
};
