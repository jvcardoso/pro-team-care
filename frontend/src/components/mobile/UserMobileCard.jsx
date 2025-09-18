import React, { useState } from "react";
import Button from "../ui/Button";
import ActionDropdown from "../ui/ActionDropdown";
import ChangePasswordModal from "../forms/ChangePasswordModal";
import {
  User,
  Calendar,
  Mail,
  Shield,
  Edit,
  Eye,
  Key,
  UserCheck,
  UserX,
  UserPlus,
} from "lucide-react";

const UserMobileCard = React.memo(
  ({
    user,
    onView,
    onEdit,
    onToggleStatus,
    getStatusBadge,
    getStatusLabel,
  }) => {
    const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] =
      useState(false);

    if (!user) return null;

    return (
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800">
        {/* User Info */}
        <div className="mb-3">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 dark:text-white text-base break-words">
                {user.person_name ||
                  user.user_email ||
                  "Usuário não identificado"}
              </h3>
              {/* Sempre mostrar email quando disponível */}
              {user.user_email && (
                <div className="flex items-center mt-1">
                  <Mail className="h-3 w-3 mr-1 text-gray-500 flex-shrink-0" />
                  <p className="text-sm text-gray-600 dark:text-gray-300 break-words font-mono">
                    {user.user_email}
                  </p>
                </div>
              )}
            </div>
            <span
              className={getStatusBadge(
                user.user_is_active ? "active" : "inactive"
              )}
            >
              {getStatusLabel(user.user_is_active ? "active" : "inactive")}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
            <div className="flex items-center">
              <User className="h-4 w-4 mr-2 text-gray-500" />
              <span className="text-gray-900 dark:text-white">
                ID: {user.user_id}
              </span>
            </div>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2 text-gray-500" />
              <span className="text-gray-600 dark:text-gray-300">
                {user.user_created_at
                  ? new Date(user.user_created_at).toLocaleDateString("pt-BR")
                  : "-"}
              </span>
            </div>

            {user.person?.document_number && (
              <div className="flex items-center">
                <UserCheck className="h-4 w-4 mr-2 text-gray-500" />
                <span className="text-gray-600 dark:text-gray-300 font-mono">
                  {user.person.document_type?.toUpperCase()}:{" "}
                  {user.person.document_number}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Roles */}
        {user.roles && user.roles.length > 0 && (
          <div className="mb-3">
            <div className="flex items-center mb-2">
              <Shield className="h-4 w-4 mr-2 text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Funções
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {user.roles.map((role, index) => (
                <span
                  key={role.id || index}
                  className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800"
                >
                  {role.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Last Login */}
        {user.last_login_at && (
          <div className="mb-3 text-sm">
            <div className="flex items-center text-gray-600 dark:text-gray-300">
              <Calendar className="h-4 w-4 mr-2" />
              Último login:{" "}
              {new Date(user.last_login_at).toLocaleString("pt-BR")}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
          {/* Action Dropdown - Todas as ações em um só lugar */}
          <ActionDropdown>
            <ActionDropdown.Item
              icon={<Eye className="h-4 w-4" />}
              onClick={() => onView?.(user.user_id)}
            >
              Ver Detalhes
            </ActionDropdown.Item>

            <ActionDropdown.Item
              icon={<Edit className="h-4 w-4" />}
              onClick={() => onEdit?.(user.user_id)}
              variant="default"
            >
              Editar Usuário
            </ActionDropdown.Item>

            <ActionDropdown.Item
              icon={<Key className="h-4 w-4" />}
              onClick={() => setIsChangePasswordModalOpen(true)}
            >
              Alterar Senha
            </ActionDropdown.Item>

            <ActionDropdown.Item
              icon={
                user.user_is_active ? (
                  <UserX className="h-4 w-4" />
                ) : (
                  <UserCheck className="h-4 w-4" />
                )
              }
              onClick={() =>
                onToggleStatus?.(user.user_id, !user.user_is_active)
              }
              variant={user.user_is_active ? "warning" : "success"}
            >
              {user.user_is_active ? "Inativar Usuário" : "Ativar Usuário"}
            </ActionDropdown.Item>
          </ActionDropdown>
        </div>

        {/* Change Password Modal */}
        <ChangePasswordModal
          isOpen={isChangePasswordModalOpen}
          onClose={() => setIsChangePasswordModalOpen(false)}
          user={user}
        />
      </div>
    );
  }
);

UserMobileCard.displayName = "UserMobileCard";

export default UserMobileCard;
