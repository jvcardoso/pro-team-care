/**
 * Users Table Configuration
 * Defines all settings for the users data table
 */

import React from "react";
import {
  Users,
  UserCheck,
  UserX,
  Eye,
  Edit,
  Key,
  Calendar,
  Mail,
  Shield,
} from "lucide-react";
import { DataTableConfig } from "../../types/dataTable.types";
import { getStatusBadge, getStatusLabel } from "../../utils/statusUtils";

export interface User {
  user_id: number;
  person_name?: string;
  user_email: string;
  user_is_active: boolean;
  user_is_system_admin: boolean;
  user_created_at: string;
  role_display_name?: string;
}

export const usersConfig: DataTableConfig<User> = {
  // Basic Info
  entity: "usuarios",
  title: "👥 Dashboard de Usuários",
  description: "Gestão completa de usuários cadastrados no sistema",

  // Data Structure
  columns: [
    {
      key: "person_name",
      label: "Usuário",
      type: "text",
      sortable: true,
      render: (value, item) => (
        <div>
          <div className="text-base font-semibold">
            {value || item.user_email}
          </div>
          {value && value !== item.user_email && (
            <div className="font-normal text-gray-500 text-sm">
              {item.user_email}
            </div>
          )}
          {!value && (
            <div className="font-normal text-gray-500 text-sm">
              ID: {item.user_id}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "user_is_system_admin",
      label: "Função",
      type: "custom",
      render: (value) => (
        <div className="flex flex-col gap-1">
          {value ? (
            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">
              <Shield className="w-3 h-3 mr-1" />
              Administrador
            </span>
          ) : (
            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
              <Users className="w-3 h-3 mr-1" />
              Usuário
            </span>
          )}
        </div>
      ),
    },
    {
      key: "user_is_active",
      label: "Status",
      type: "badge",
      render: (value) => getStatusBadge(value ? "active" : "inactive"),
    },
    {
      key: "user_created_at",
      label: "Criado em",
      type: "date",
      render: (value) => (
        <div className="flex items-center">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <span>
            {value ? new Date(value).toLocaleDateString("pt-BR") : "-"}
          </span>
        </div>
      ),
    },
  ],

  searchFields: ["person_name", "user_email"],

  // Metrics
  metrics: {
    primary: [
      {
        id: "total_users",
        title: "Total Usuários",
        value: 0, // Will be calculated dynamically
        subtitle: "cadastrados",
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
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
            />
          </svg>
        ),
        color: "blue",
      },
      {
        id: "active_users",
        title: "Usuários Ativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
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
        id: "inactive_users",
        title: "Usuários Inativos",
        value: 0, // Will be calculated dynamically
        subtitle: "({percentage}%)",
        icon: (
          <svg
            className="h-6 w-6 text-gray-600 dark:text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        ),
        color: "gray",
      },
      {
        id: "admin_users",
        title: "Administradores",
        value: 0, // Will be calculated dynamically
        subtitle: "do sistema",
        icon: (
          <svg
            className="h-6 w-6 text-red-600 dark:text-red-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
        ),
        color: "red",
      },
    ],
    detailed: {
      title: "📊 Estatísticas de Usuários",
      sections: [
        {
          title: "📈 Status dos Usuários",
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
          ],
        },
        {
          title: "👑 Funções",
          items: [
            {
              id: "role_admin",
              title: "👑 Administradores",
              value: 0,
              subtitle: "acesso total",
              icon: <span>👑</span>,
              color: "red",
            },
            {
              id: "role_user",
              title: "👤 Usuários Comuns",
              value: 0,
              subtitle: "acesso limitado",
              icon: <span>👤</span>,
              color: "blue",
            },
          ],
        },
      ],
      quickActions: [
        {
          label: "➕ Novo Usuário",
          action: () => {
            // This will be implemented in the component
          },
          color: "blue",
        },
        {
          label: "📧 Convites Pendentes",
          action: () => {
            // This will be implemented in the component
          },
          color: "purple",
        },
        {
          label: "📋 Relatório de Acesso",
          action: () => {
            // This will be implemented in the component
          },
          color: "green",
        },
      ],
    },
  },

  // Filters
  filters: [
    {
      key: "user_is_active",
      label: "Status",
      type: "select",
      options: [
        { value: "all", label: "📋 Todos os status" },
        { value: "true", label: "✅ Ativo" },
        { value: "false", label: "⏸️ Inativo" },
      ],
    },
    {
      key: "user_is_system_admin",
      label: "Função",
      type: "select",
      options: [
        { value: "all", label: "👥 Todas as funções" },
        { value: "true", label: "👑 Administrador" },
        { value: "false", label: "👤 Usuário" },
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
      onClick: (user) => {
        console.log("Ver usuário", user);
      },
    },
    {
      id: "edit",
      label: "Editar",
      icon: <Edit className="w-4 h-4" />,
      color: "yellow",
      onClick: (user) => {
        console.log("Editar usuário", user);
      },
    },
    {
      id: "change_password",
      label: "Alterar Senha",
      icon: <Key className="w-4 h-4" />,
      color: "purple",
      onClick: (user) => {
        console.log("Alterar senha do usuário", user);
      },
    },
    {
      id: "toggle_status",
      label: "Alternar Status",
      icon: <UserCheck className="w-4 h-4" />,
      color: "green",
      onClick: (user) => {
        console.log("Alternar status do usuário", user);
      },
    },
  ],

  // Export
  export: {
    filename: "usuarios",
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

export default usersConfig;
