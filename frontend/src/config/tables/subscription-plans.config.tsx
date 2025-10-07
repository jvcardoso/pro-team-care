/**
 * Subscription Plans Table Configuration
 * Defines all settings for the subscription plans data table
 */

import React from "react";
import { Users, Building, Check, Eye, Edit, Trash2 } from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { SubscriptionPlan } from "../../types/b2b-billing.types";

export const createSubscriptionPlansConfig = (
  onCreatePlan?: () => void,
  onEditPlan?: (plan: SubscriptionPlan) => void,
  onViewPlan?: (plan: SubscriptionPlan) => void,
  onDeletePlan?: (plan: SubscriptionPlan) => void
): DataTableConfig<SubscriptionPlan> => ({
  // Basic Info
  entity: "plano",
  title: "💳 Planos de Assinatura",
  description: "Gestão completa de planos de assinatura disponíveis",

  // Data Structure - Optimized for responsive layout
  columns: [
    {
      key: "name",
      label: "Plano",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div className="min-w-0 flex-1">
          <div className="font-semibold text-sm truncate">{value}</div>
          {item.description && (
            <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {item.description}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "monthly_price",
      label: "Valor",
      type: "currency",
      sortable: true,
      render: (value) => {
        const numValue =
          typeof value === "number" ? value : parseFloat(value) || 0;
        return (
          <div className="font-semibold text-green-600 dark:text-green-400 text-sm whitespace-nowrap">
            R$ {numValue.toFixed(2)}
          </div>
        );
      },
    },
    {
      key: "limits",
      label: "Limites",
      type: "custom",
      render: (value, item) => (
        <div className="text-xs space-y-1">
          <div className="flex items-center">
            <Users className="w-3 h-3 mr-1 text-blue-500 flex-shrink-0" />
            <span className="truncate">
              {item.max_users ? `${item.max_users}` : "∞"}
            </span>
          </div>
          <div className="flex items-center">
            <Building className="w-3 h-3 mr-1 text-purple-500 flex-shrink-0" />
            <span className="truncate">
              {item.max_establishments ? `${item.max_establishments}` : "∞"}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: "features",
      label: "Recursos",
      type: "custom",
      render: (features) => {
        const featureCount = features ? Object.keys(features).length : 0;
        return (
          <div className="flex items-center justify-center">
            <div className="flex items-center bg-green-100 dark:bg-green-900 px-2 py-1 rounded-full">
              <Check className="w-3 h-3 mr-1 text-green-600 dark:text-green-400" />
              <span className="text-xs font-medium text-green-800 dark:text-green-200">
                {featureCount}
              </span>
            </div>
          </div>
        );
      },
    },
    {
      key: "is_active",
      label: "Status",
      type: "badge",
      render: (value) => (
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${
            value
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
          }`}
        >
          {value ? "Ativo" : "Inativo"}
        </span>
      ),
    },
  ],

  searchFields: ["name", "description"],
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
      key: "is_active",
      label: "Status",
      type: "select",
      options: [
        { value: "all", label: "📋 Todos os status" },
        { value: "active", label: "✅ Ativos" },
        { value: "inactive", label: "⏸️ Inativos" },
      ],
    },
    {
      key: "monthly_price",
      label: "Faixa de Preço",
      type: "range",
      min: 0,
      max: 1000,
      step: 50,
    },
    {
      key: "max_users",
      label: "Máximo de Usuários",
      type: "range",
      min: 1,
      max: 500,
      step: 10,
    },
  ],

  // Actions
  actions: [
    {
      id: "view",
      label: "Ver Detalhes",
      icon: <Eye className="w-4 h-4" />,
      color: "blue",
      onClick: (_plan) => {
        if (onViewPlan) {
          onViewPlan(_plan);
        }
      },
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (plan) => {
        if (onEditPlan) {
          onEditPlan(plan);
        }
      },
    },
    {
      id: "delete",
      label: "Desativar",
      icon: <Trash2 className="w-4 h-4" />,
      color: "red",
      onClick: (plan) => {
        if (onDeletePlan) {
          onDeletePlan(plan);
        }
      },
      condition: (plan) => plan.is_active, // Only show for active plans
    },
  ],

  // Show add button
  showAddButton: true,
  onAdd: () => {
    if (onCreatePlan) {
      onCreatePlan();
    }
  },

  // Export
  export: {
    filename: "planos-assinatura",
    formats: ["csv", "json", "print"],
    includeFiltered: true,
  },

  // Pagination
  defaultPageSize: 10,
  pageSizeOptions: [10, 25, 50, 100],

  // Customization - Compact table for better responsiveness
  className: "subscription-plans-table",
  theme: "default",

  // Table styling overrides
  tableStyles: {
    compact: true,
    cellPadding: "px-2 py-3",
    fontSize: "text-sm",
  },
});

// Versão padrão para compatibilidade
export const subscriptionPlansConfig = createSubscriptionPlansConfig();

export default subscriptionPlansConfig;
