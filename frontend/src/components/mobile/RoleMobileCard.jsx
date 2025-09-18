import React from "react";
import ActionDropdown from "../ui/ActionDropdown";
import {
  Shield,
  Calendar,
  Eye,
  Edit,
  Trash2,
  Settings,
  Users,
  Lock,
  Building,
  Server,
} from "lucide-react";

const RoleMobileCard = React.memo(({ role, onView, onEdit, onDelete }) => {
  if (!role) {
    console.log("⚠️ RoleMobileCard: role is null/undefined");
    return null;
  }

  console.log("✅ RoleMobileCard rendering:", role.display_name || role.name);

  const getContextIcon = (contextType) => {
    switch (contextType) {
      case "system":
        return <Server className="h-4 w-4" />;
      case "company":
        return <Building className="h-4 w-4" />;
      case "establishment":
        return <Users className="h-4 w-4" />;
      default:
        return <Shield className="h-4 w-4" />;
    }
  };

  const getContextTypeLabel = (type) => {
    const labels = {
      system: "Sistema",
      company: "Empresa",
      establishment: "Estabelecimento",
    };
    return labels[type] || type;
  };

  const getLevelLabel = (level) => {
    if (level >= 90) return "Sistema";
    if (level >= 70) return "Administrativo";
    if (level >= 40) return "Intermediário";
    return "Básico";
  };

  const getLevelColor = (level) => {
    if (level >= 90) return "bg-purple-100 text-purple-800";
    if (level >= 70) return "bg-red-100 text-red-800";
    if (level >= 40) return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
      {/* Role Info */}
      <div className="mb-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-gray-900 dark:text-white text-base break-words">
              {role.display_name || role.name}
            </h3>
            {role.display_name && role.name !== role.display_name && (
              <p className="text-sm text-gray-600 dark:text-gray-300 break-words font-mono">
                {role.name}
              </p>
            )}
          </div>
          <span
            className={`px-2 py-1 text-xs font-semibold rounded-full ${
              role.is_active
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {role.is_active ? "Ativo" : "Inativo"}
          </span>
        </div>

        {/* Description */}
        {role.description && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">
            {role.description}
          </p>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          <div className="flex items-center">
            <Shield className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-gray-900 dark:text-white">ID: {role.id}</span>
          </div>
          <div className="flex items-center">
            <Calendar className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-gray-600 dark:text-gray-300">
              {role.created_at
                ? new Date(role.created_at).toLocaleDateString("pt-BR")
                : "-"}
            </span>
          </div>
        </div>
      </div>

      {/* Role Details */}
      <div className="mb-3">
        <div className="flex flex-wrap gap-2">
          {/* Context Type */}
          <div className="flex items-center bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded-md">
            {getContextIcon(role.context_type)}
            <span className="ml-1 text-xs font-medium text-blue-800 dark:text-blue-200">
              {getContextTypeLabel(role.context_type)}
            </span>
          </div>

          {/* Level */}
          <div
            className={`flex items-center px-2 py-1 rounded-md ${getLevelColor(
              role.level
            )}`}
          >
            <span className="text-xs font-medium">
              Nível {role.level} - {getLevelLabel(role.level)}
            </span>
          </div>

          {/* System Role Badge */}
          {role.is_system_role && (
            <div className="flex items-center bg-purple-50 dark:bg-purple-900/20 px-2 py-1 rounded-md">
              <Lock className="h-3 w-3 mr-1 text-purple-600" />
              <span className="text-xs font-medium text-purple-800 dark:text-purple-200">
                Sistema
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Permissions Count */}
      {role.permissions && (
        <div className="mb-3 text-sm">
          <div className="flex items-center text-gray-600 dark:text-gray-300">
            <Settings className="h-4 w-4 mr-2" />
            Permissões: {role.permissions.length || 0}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
        <ActionDropdown>
          <ActionDropdown.Item
            icon={<Eye className="h-4 w-4" />}
            onClick={() => onView?.(role)}
          >
            Ver Detalhes
          </ActionDropdown.Item>

          <ActionDropdown.Item
            icon={<Edit className="h-4 w-4" />}
            onClick={() => onEdit?.(role)}
            disabled={role.is_system_role}
            variant="default"
          >
            Editar Perfil
          </ActionDropdown.Item>

          <ActionDropdown.Item
            icon={<Trash2 className="h-4 w-4" />}
            onClick={() => onDelete?.(role.id, role.display_name || role.name)}
            disabled={role.is_system_role}
            variant="danger"
          >
            Excluir Perfil
          </ActionDropdown.Item>
        </ActionDropdown>
      </div>
    </div>
  );
});

RoleMobileCard.displayName = "RoleMobileCard";

export default RoleMobileCard;
