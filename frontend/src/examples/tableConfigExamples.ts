/**
 * Table Configuration Examples
 * Demonstra como usar o novo sistema de configuração de tabelas
 */

import {
  createTableConfig,
  createContractsConfig,
  createClientsConfig,
  createUsersConfig,
  createIdColumn,
  createNameColumn,
  createStatusColumn,
  createDateColumn,
} from "../utils/tableConfigBuilder";

// ===============================
// EXEMPLO 1: Configuração básica usando helper
// ===============================

export const basicTableExample = createTableConfig({
  entity: "products",
  title: "Produtos",
  description: "Catálogo de produtos do sistema",

  columns: [
    createIdColumn(),
    createNameColumn("product_name", { label: "Nome do Produto" }),
    {
      key: "price",
      label: "Preço",
      type: "currency",
      sortable: true,
      render: (value) =>
        new Intl.NumberFormat("pt-BR", {
          style: "currency",
          currency: "BRL",
        }).format(value),
    },
    createStatusColumn(),
    createDateColumn("created_at", "Criado em"),
  ],

  theme: "compact",

  filters: [
    {
      key: "price",
      label: "Faixa de Preço",
      type: "range",
      min: 0,
      max: 10000,
      step: 10,
    },
    {
      key: "categories",
      label: "Categorias",
      type: "multiselect",
      options: [
        { value: "electronics", label: "📱 Eletrônicos" },
        { value: "clothing", label: "👔 Roupas" },
        { value: "books", label: "📚 Livros" },
      ],
    },
  ],
});

// ===============================
// EXEMPLO 2: Configuração de contratos com tema enterprise
// ===============================

export const enterpriseContractsExample = createContractsConfig({
  title: "📋 Gestão Empresarial de Contratos",
  description: "Dashboard executivo de contratos home care",
  theme: "enterprise",

  // Métricas customizadas para executivos
  metrics: {
    primary: [
      {
        id: "total_revenue",
        title: "Receita Total",
        value: 0,
        subtitle: "Este mês",
        icon: (
          <svg
            className="h-6 w-6 text-green-600"
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
        color: "green",
      },
      {
        id: "client_retention",
        title: "Retenção de Clientes",
        value: "94.5%",
        subtitle: "Últimos 12 meses",
        icon: (
          <svg
            className="h-6 w-6 text-blue-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"
            />
          </svg>
        ),
        color: "blue",
      },
    ],
  },

  // Filtros avançados para análise executiva
  filters: [
    {
      key: "performance_tier",
      label: "Tier de Performance",
      type: "select",
      options: [
        { value: "all", label: "📊 Todos os Tiers" },
        { value: "premium", label: "⭐ Premium" },
        { value: "standard", label: "📈 Standard" },
        { value: "basic", label: "📋 Basic" },
      ],
    },
    {
      key: "contract_value",
      label: "Valor do Contrato",
      type: "range",
      min: 1000,
      max: 100000,
      step: 1000,
    },
    {
      key: "renewal_period",
      label: "Período de Renovação",
      type: "daterange",
    },
  ],
});

// ===============================
// EXEMPLO 3: Tabela de clientes com tema comfortable
// ===============================

export const comfortableClientsExample = createClientsConfig({
  title: "👥 Central de Relacionamento com Clientes",
  description: "Gestão completa do relacionamento e atendimento",
  theme: "comfortable",

  columns: [
    createIdColumn(),
    {
      key: "avatar",
      label: "Avatar",
      type: "custom",
      width: "w-16",
      render: (value, item) => (
        <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full text-white font-bold">
          {item.name?.charAt(0)?.toUpperCase() || "?"}
        </div>
      ),
    },
    createNameColumn("full_name", {
      label: "Nome Completo",
      width: "w-64",
    }),
    {
      key: "contact_info",
      label: "Contato",
      type: "custom",
      render: (value, item) => (
        <div className="space-y-1">
          <div className="text-sm">{item.email}</div>
          <div className="text-xs text-gray-500">{item.phone}</div>
        </div>
      ),
    },
    {
      key: "satisfaction_score",
      label: "Satisfação",
      type: "custom",
      render: (value) => (
        <div className="flex items-center space-x-2">
          <div className="w-16 bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${value || 0}%` }}
            ></div>
          </div>
          <span className="text-sm font-medium">{value || 0}%</span>
        </div>
      ),
    },
    createStatusColumn(),
    createDateColumn("last_contact", "Último Contato"),
  ],

  filters: [
    {
      key: "client_search",
      label: "Buscar Cliente",
      type: "search",
      placeholder: "Nome, email ou telefone...",
    },
    {
      key: "satisfaction_range",
      label: "Nível de Satisfação",
      type: "range",
      min: 0,
      max: 100,
      step: 5,
    },
    {
      key: "contact_preferences",
      label: "Preferências de Contato",
      type: "multiselect",
      options: [
        { value: "email", label: "📧 Email" },
        { value: "phone", label: "📞 Telefone" },
        { value: "whatsapp", label: "💬 WhatsApp" },
        { value: "sms", label: "📱 SMS" },
      ],
    },
  ],
});

// ===============================
// EXEMPLO 4: Tabela minimalista para relatórios
// ===============================

export const minimalReportsExample = createTableConfig({
  entity: "reports",
  title: "Relatórios Executivos",
  description: "Dados consolidados para tomada de decisão",
  theme: "minimal",

  columns: [
    {
      key: "report_name",
      label: "Relatório",
      type: "text",
      sortable: true,
    },
    {
      key: "period",
      label: "Período",
      type: "text",
      sortable: true,
    },
    {
      key: "status",
      label: "Status",
      type: "badge",
      render: (value) => (
        <span
          className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
            value === "generated"
              ? "bg-green-100 text-green-800"
              : value === "processing"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {value === "generated"
            ? "Gerado"
            : value === "processing"
            ? "Processando"
            : "Pendente"}
        </span>
      ),
    },
    {
      key: "download",
      label: "Download",
      type: "custom",
      render: (value, item) => (
        <button className="text-blue-600 hover:text-blue-800 underline text-sm">
          Baixar PDF
        </button>
      ),
    },
  ],

  filters: [
    {
      key: "report_period",
      label: "Período do Relatório",
      type: "daterange",
    },
    {
      key: "report_type",
      label: "Tipo de Relatório",
      type: "select",
      options: [
        { value: "all", label: "Todos os Tipos" },
        { value: "financial", label: "Financeiro" },
        { value: "operational", label: "Operacional" },
        { value: "customer", label: "Clientes" },
      ],
    },
  ],

  // Configuração simplificada para relatórios
  defaultPageSize: 25,
  pageSizeOptions: [25, 50, 100],

  export: {
    filename: "relatorios_executivos",
    formats: ["csv", "json"],
    includeFiltered: true,
  },
});

// ===============================
// EXEMPLO 5: Como usar os helpers individualmente
// ===============================

export const customTableWithHelpers = createTableConfig({
  entity: "tasks",
  title: "Gestão de Tarefas",
  description: "Sistema de acompanhamento de tarefas e projetos",

  columns: [
    createIdColumn({ width: "w-16" }),

    // Coluna customizada para título da tarefa
    {
      key: "title",
      label: "Tarefa",
      type: "custom",
      sortable: true,
      width: "w-80",
      render: (value, item) => (
        <div>
          <div className="font-medium text-gray-900 dark:text-white">
            {value}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {item.description}
          </div>
        </div>
      ),
    },

    // Usando helper para status com customização
    createStatusColumn({
      render: (value) => (
        <span
          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            value === "completed"
              ? "bg-green-100 text-green-800"
              : value === "in_progress"
              ? "bg-blue-100 text-blue-800"
              : value === "pending"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-gray-100 text-gray-800"
          }`}
        >
          {value === "completed"
            ? "✅ Concluída"
            : value === "in_progress"
            ? "🔄 Em Andamento"
            : value === "pending"
            ? "⏳ Pendente"
            : value}
        </span>
      ),
    }),

    // Usando helper para data com customização
    createDateColumn("due_date", "Prazo", {
      render: (value) => {
        const date = new Date(value);
        const isOverdue = date < new Date();
        return (
          <span
            className={
              isOverdue
                ? "text-red-600 font-medium"
                : "text-gray-900 dark:text-white"
            }
          >
            {date.toLocaleDateString("pt-BR")}
            {isOverdue && " ⚠️"}
          </span>
        );
      },
    }),
  ],

  theme: "default",

  filters: [
    {
      key: "task_status",
      label: "Status da Tarefa",
      type: "multiselect",
      options: [
        { value: "pending", label: "⏳ Pendente" },
        { value: "in_progress", label: "🔄 Em Andamento" },
        { value: "completed", label: "✅ Concluída" },
      ],
    },
    {
      key: "due_date_range",
      label: "Prazo",
      type: "daterange",
    },
    {
      key: "priority",
      label: "Prioridade",
      type: "select",
      options: [
        { value: "all", label: "Todas" },
        { value: "high", label: "🔴 Alta" },
        { value: "medium", label: "🟡 Média" },
        { value: "low", label: "🟢 Baixa" },
      ],
    },
  ],
});

export default {
  basicTableExample,
  enterpriseContractsExample,
  comfortableClientsExample,
  minimalReportsExample,
  customTableWithHelpers,
};
