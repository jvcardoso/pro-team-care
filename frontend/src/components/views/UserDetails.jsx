import React, { useState, useEffect } from "react";
import { usersService } from "../../services/api";
import Card from "../ui/Card";
import EntityDetailsLayout from "./EntityDetailsLayout";
import { getStatusBadge, getStatusLabel } from "../../utils/statusUtils";
import { formatTaxId } from "../../utils/formatters";
import { notify } from "../../utils/notifications.jsx";
import {
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Mail,
  Calendar,
  Shield,
  Settings,
  Clock,
} from "lucide-react";

const UserDetails = ({ userId, onEdit, onBack, onDelete }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  useEffect(() => {
    if (userId) {
      loadUser();
    }
  }, [userId]);

  const loadUser = async () => {
    try {
      setLoading(true);
      const data = await usersService.getUser(userId);

      if (process.env.NODE_ENV === "development") {
        console.log("UserDetails - Dados do usuário carregados");
      }

      setUser(data);
      setError(null);
    } catch (err) {
      setError("Erro ao carregar usuário");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    const executeDelete = async () => {
      try {
        await usersService.deleteUser(userId);
        notify.success("Usuário excluído com sucesso!");
        onDelete?.();
      } catch (err) {
        notify.error("Erro ao excluir usuário");
        console.error(err);
      }
    };

    notify.confirmDelete(
      "Excluir Usuário",
      `Tem certeza que deseja excluir o usuário "${
        user?.person_name || user?.user_email || "este usuário"
      }"?`,
      executeDelete
    );
  };

  // Definição de tabs
  const tabs = [
    {
      key: "informacoes",
      label: "Informações",
      shortLabel: "Info",
    },
    {
      key: "roles",
      label: "Funções",
      shortLabel: "Funções",
    },
    {
      key: "historico",
      label: "Histórico",
      shortLabel: "Histórico",
    },
  ];

  // Definição de action buttons
  const actionButtons = [
    {
      label: "Editar",
      onClick: () => onEdit?.(userId),
      variant: "primary",
      icon: <Edit className="h-4 w-4" />,
    },
    {
      label: "Excluir",
      onClick: handleDelete,
      variant: "danger",
      outline: true,
      icon: <Trash2 className="h-4 w-4" />,
    },
  ];

  // Status badge
  const statusBadge = user && (
    <span
      className={getStatusBadge(user.user_is_active ? "active" : "inactive")}
    >
      {getStatusLabel(user.user_is_active ? "active" : "inactive")}
    </span>
  );

  return (
    <EntityDetailsLayout
      title={user?.person_name || user?.user_email || "Carregando..."}
      subtitle={user?.person_name ? user.user_email : undefined}
      icon={<User className="h-6 w-6" />}
      statusBadge={statusBadge}
      backButton={{ onClick: onBack, label: "Voltar" }}
      actionButtons={actionButtons}
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      loading={loading}
      error={error}
      onRetry={loadUser}
    >
      {/* Tab: Informações */}
      {activeTab === "informacoes" && user && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Dados Pessoais */}
          <Card title="Dados Pessoais" icon={<User className="h-5 w-5" />}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Nome Completo
                </label>
                <p className="text-foreground">
                  {user.person_name || "Não informado"}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Email
                </label>
                <p className="text-foreground font-mono text-sm">
                  {user.user_email}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  CPF
                </label>
                <p className="text-foreground font-mono text-sm">
                  {user.person_tax_id
                    ? formatTaxId(user.person_tax_id)
                    : "Não informado"}
                </p>
              </div>

              {user.person_birth_date && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Data de Nascimento
                  </label>
                  <p className="text-foreground">
                    {new Date(user.person_birth_date).toLocaleDateString(
                      "pt-BR"
                    )}
                  </p>
                </div>
              )}

              {user.person_gender && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Gênero
                  </label>
                  <p className="text-foreground">
                    {user.person_gender === "M"
                      ? "Masculino"
                      : user.person_gender === "F"
                      ? "Feminino"
                      : "Outro"}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Status do Usuário
                </label>
                <span
                  className={getStatusBadge(
                    user.user_is_active ? "active" : "inactive"
                  )}
                >
                  {getStatusLabel(user.user_is_active ? "active" : "inactive")}
                </span>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Tipo de Usuário
                </label>
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.user_is_system_admin
                      ? "bg-red-100 text-red-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {user.user_is_system_admin
                    ? "Administrador do Sistema"
                    : "Usuário"}
                </span>
              </div>
            </div>
          </Card>

          {/* Informações do Sistema */}
          <Card
            title="Informações do Sistema"
            icon={<Settings className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  ID do Usuário
                </label>
                <p className="text-foreground font-mono">{user.user_id}</p>
              </div>

              {user.person_id && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    ID da Pessoa
                  </label>
                  <p className="text-foreground font-mono">{user.person_id}</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Data de Criação
                </label>
                <p className="text-foreground">
                  {user.user_created_at
                    ? new Date(user.user_created_at).toLocaleString("pt-BR")
                    : "Não informado"}
                </p>
              </div>

              {user.user_updated_at && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Última Atualização
                  </label>
                  <p className="text-foreground">
                    {new Date(user.user_updated_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              )}

              {user.user_last_login_at && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Último Login
                  </label>
                  <p className="text-foreground">
                    {new Date(user.user_last_login_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Tab: Funções e Permissões */}
      {activeTab === "roles" && user && (
        <Card
          title="Funções e Permissões"
          icon={<Shield className="h-5 w-5" />}
        >
          {user.roles && user.roles.length > 0 ? (
            <div className="space-y-4">
              {user.roles.map((role, index) => (
                <div
                  key={role.id || index}
                  className="p-4 border border-border rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-foreground">
                        {role.name}
                      </h3>
                      {role.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {role.description}
                        </p>
                      )}
                    </div>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                      {role.name}
                    </span>
                  </div>

                  {role.permissions && role.permissions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <h4 className="text-sm font-medium text-muted-foreground mb-2">
                        Permissões:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {role.permissions.map((permission, pIndex) => (
                          <span
                            key={permission.id || pIndex}
                            className="inline-flex px-2 py-1 text-xs rounded-md bg-gray-100 text-gray-800"
                          >
                            {permission.name || permission}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Shield className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Nenhuma função atribuída
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Este usuário não possui funções específicas no sistema.
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Tab: Histórico */}
      {activeTab === "historico" && (
        <Card
          title="Histórico de Atividades"
          icon={<Clock className="h-5 w-5" />}
        >
          <div className="text-center py-8">
            <Clock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Histórico não disponível
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              O histórico de atividades do usuário ainda não foi implementado.
            </p>
          </div>
        </Card>
      )}
    </EntityDetailsLayout>
  );
};

export default UserDetails;
