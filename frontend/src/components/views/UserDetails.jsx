import React, { useState, useEffect } from "react";
import { usersService } from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { getStatusBadge, getStatusLabel } from "../../utils/statusUtils";
import { notify } from "../../utils/notifications.jsx";
import {
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Mail,
  Calendar,
  Shield,
  Key,
  Settings,
  FileText,
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
        user?.person?.name || user?.email || "este usuário"
      }"?`,
      executeDelete
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">
            Carregando dados do usuário...
          </p>
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">
            {error || "Usuário não encontrado"}
          </p>
          <Button onClick={onBack} icon={<ArrowLeft className="h-4 w-4" />}>
            Voltar
          </Button>
        </div>
      </div>
    );
  }

  const tabs = [
    {
      id: "informacoes",
      label: "Informações",
      icon: <User className="h-4 w-4" />,
    },
    { id: "roles", label: "Funções", icon: <Shield className="h-4 w-4" /> },
    {
      id: "historico",
      label: "Histórico",
      icon: <Clock className="h-4 w-4" />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            outline
            onClick={onBack}
            icon={<ArrowLeft className="h-4 w-4" />}
          >
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {user.person?.name || user.email}
            </h1>
            <p className="text-muted-foreground">
              {user.person?.name && user.email}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="primary"
            onClick={() => onEdit?.(userId)}
            icon={<Edit className="h-4 w-4" />}
          >
            Editar
          </Button>
          <Button
            variant="danger"
            outline
            onClick={handleDelete}
            icon={<Trash2 className="h-4 w-4" />}
          >
            Excluir
          </Button>
        </div>
      </div>

      {/* Status Card */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <User className="h-8 w-8 text-blue-600 dark:text-blue-300" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {user.person?.name || "Usuário"}
              </h2>
              <p className="text-muted-foreground flex items-center gap-2">
                <Mail className="h-4 w-4" />
                {user.email}
              </p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className={getStatusBadge(user.status)}>
              {getStatusLabel(user.status)}
            </span>
            {user.created_at && (
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Criado em{" "}
                {new Date(user.created_at).toLocaleDateString("pt-BR")}
              </span>
            )}
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-gray-300"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "informacoes" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Dados Pessoais */}
          <Card title="Dados Pessoais" icon={<User className="h-5 w-5" />}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Nome Completo
                </label>
                <p className="text-foreground">
                  {user.person?.name || "Não informado"}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Email
                </label>
                <p className="text-foreground font-mono text-sm">
                  {user.email}
                </p>
              </div>

              {user.person?.document_number && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      Tipo de Documento
                    </label>
                    <p className="text-foreground uppercase">
                      {user.person.document_type}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-muted-foreground mb-1">
                      Número do Documento
                    </label>
                    <p className="text-foreground font-mono">
                      {user.person.document_number}
                    </p>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-1">
                  Status
                </label>
                <span className={getStatusBadge(user.status)}>
                  {getStatusLabel(user.status)}
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
                <p className="text-foreground font-mono">{user.id}</p>
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
                  {user.created_at
                    ? new Date(user.created_at).toLocaleString("pt-BR")
                    : "Não informado"}
                </p>
              </div>

              {user.updated_at && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Última Atualização
                  </label>
                  <p className="text-foreground">
                    {new Date(user.updated_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              )}

              {user.last_login_at && (
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-1">
                    Último Login
                  </label>
                  <p className="text-foreground">
                    {new Date(user.last_login_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {activeTab === "roles" && (
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
    </div>
  );
};

export default UserDetails;
