import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { establishmentsService } from "../../services/api";
import { clientsService } from "../../services/clientsService";
import DataTableTemplate from "../shared/DataTable/DataTableTemplate";
import { useDataTable } from "../../hooks/useDataTable";
import { createEstablishmentClientsConfig } from "../../config/tables/establishmentClients.config";
import EntityDetailsLayout from "./EntityDetailsLayout";
import Card from "../ui/Card";
import Button from "../ui/Button";
import {
  PhoneDisplayCard,
  EmailDisplayCard,
  AddressDisplayCard,
} from "../contacts";
import {
  getStatusBadge,
  getStatusLabel,
  getPhoneTypeLabel,
  getEmailTypeLabel,
  getAddressTypeLabel,
  formatPhone,
  formatZipCode,
} from "../../utils/statusUtils";
import { formatTaxId } from "../../utils/formatters";
import { notify } from "../../utils/notifications.jsx";
import {
  Edit,
  Trash2,
  Building,
  User,
  Users,
  Calendar,
  Settings,
  Clock,
  Activity,
  Shield,
  Briefcase,
  MapPin,
  Building2,
  UserCog,
} from "lucide-react";

const EstablishmentDetails = ({
  establishmentId,
  onEdit,
  onBack,
  onDelete,
}) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [establishment, setEstablishment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  const loadEstablishment = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await establishmentsService.getEstablishment(
        establishmentId
      );

      setEstablishment(data);
    } catch {
      setError("Erro ao carregar estabelecimento");
    } finally {
      setLoading(false);
    }
  }, [establishmentId]);

  useEffect(() => {
    if (establishmentId) {
      loadEstablishment();
    }
  }, [establishmentId, loadEstablishment]);

  // Sync URL tab parameter to state
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (
      tabParam &&
      [
        "informacoes",
        "clientes",
        "usuarios",
        "equipe",
        "configuracoes",
      ].includes(tabParam)
    ) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    navigate(`/admin/estabelecimentos/${establishmentId}?tab=${newTab}`, {
      replace: true,
    });
  };

  const handleAddUser = () => {
    navigate(
      `/admin/usuarios?establishmentId=${establishmentId}&action=create`
    );
  };

  const handleDelete = async () => {
    const executeDelete = async () => {
      try {
        await establishmentsService.deleteEstablishment(establishmentId);
        notify.success("Estabelecimento excluído com sucesso!");
        onDelete?.();
      } catch {
        notify.error("Erro ao excluir estabelecimento");
      }
    };

    notify.confirmDelete(
      "Excluir Estabelecimento",
      `Tem certeza que deseja excluir o estabelecimento "${
        establishment?.person?.name ||
        establishment?.code ||
        "este estabelecimento"
      }"?`,
      executeDelete
    );
  };

  const typeLabels = {
    matriz: "Matriz",
    filial: "Filial",
    unidade: "Unidade",
    posto: "Posto",
  };

  const categoryLabels = {
    clinica: "Clínica",
    hospital: "Hospital",
    laboratorio: "Laboratório",
    farmacia: "Farmácia",
    consultorio: "Consultório",
    upa: "UPA",
    ubs: "UBS",
    outro: "Outro",
  };

  // Tabs configuration
  const tabs = [
    { key: "informacoes", label: "Informações", shortLabel: "Info" },
    { key: "clientes", label: "Clientes", shortLabel: "Clientes" },
    { key: "usuarios", label: "Usuários", shortLabel: "Usuários" },
    { key: "equipe", label: "Equipe", shortLabel: "Equipe" },
    { key: "configuracoes", label: "Configurações", shortLabel: "Config" },
  ];

  // Action buttons
  const actionButtons = [
    {
      label: "Editar",
      onClick: () => onEdit?.(establishmentId),
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

  // Metrics cards horizontais
  const metrics = establishment
    ? [
        {
          icon: <Users className="h-6 w-6" />,
          label: "Usuários",
          value: establishment.user_count || 0,
          color:
            "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
          onClick: () => handleTabChange("usuarios"),
        },
        {
          icon: <Users className="h-6 w-6" />,
          label: "Clientes",
          value: establishment.client_count || 0,
          color:
            "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
          onClick: () => handleTabChange("clientes"),
        },
        {
          icon: <UserCog className="h-6 w-6" />,
          label: "Profissionais",
          value: establishment.professional_count || 0,
          color:
            "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
          onClick: () => handleTabChange("equipe"),
        },
      ]
    : [];

  // Status badge with additional info
  const statusBadge = establishment && (
    <div className="flex items-center gap-2">
      <span
        className={getStatusBadge(
          establishment.is_active ? "active" : "inactive"
        )}
      >
        {getStatusLabel(establishment.is_active ? "active" : "inactive")}
      </span>
      {establishment.is_principal && (
        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
          Principal
        </span>
      )}
    </div>
  );

  // Subtitle with code and type
  const subtitle = establishment
    ? `${establishment.code} • ${
        typeLabels[establishment.type] || establishment.type
      }`
    : undefined;

  return (
    <EntityDetailsLayout
      title={
        establishment?.person?.name || establishment?.code || "Carregando..."
      }
      subtitle={subtitle}
      icon={<Building className="h-6 w-6" />}
      statusBadge={statusBadge}
      backButton={{ onClick: onBack, label: "Voltar" }}
      actionButtons={actionButtons}
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={handleTabChange}
      metrics={metrics}
      loading={loading}
      error={error}
      onRetry={loadEstablishment}
    >
      {/* Tab: Informações */}
      {activeTab === "informacoes" && establishment && (
        <div className="space-y-6">
          {/* Dados do Estabelecimento */}
          <Card title="Dados do Estabelecimento">
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Nome
                  </div>
                  <p className="text-foreground font-medium">
                    {establishment.person?.name || "Não informado"}
                  </p>
                </div>
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Código
                  </div>
                  <p className="text-foreground font-mono text-sm">
                    {establishment.code}
                  </p>
                </div>
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    CNPJ
                  </div>
                  <p className="text-foreground font-mono text-sm">
                    {establishment.person?.tax_id
                      ? formatTaxId(establishment.person.tax_id)
                      : "Não informado"}
                  </p>
                </div>
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Status
                  </div>
                  <span
                    className={getStatusBadge(
                      establishment.is_active ? "active" : "inactive"
                    )}
                  >
                    {getStatusLabel(
                      establishment.is_active ? "active" : "inactive"
                    )}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Tipo
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 capitalize">
                    {typeLabels[establishment.type] || establishment.type}
                  </span>
                </div>
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Categoria
                  </div>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 capitalize">
                    {categoryLabels[establishment.category] ||
                      establishment.category}
                  </span>
                </div>
              </div>

              {establishment.person?.description && (
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    Observações
                  </div>
                  <p className="text-foreground text-sm">
                    {establishment.person.description}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Telefones */}
          <PhoneDisplayCard
            phones={establishment.phones || []}
            formatPhone={formatPhone}
            getPhoneTypeLabel={getPhoneTypeLabel}
          />

          {/* E-mails */}
          <EmailDisplayCard
            emails={establishment.emails || []}
            getEmailTypeLabel={getEmailTypeLabel}
          />

          {/* Endereços */}
          <AddressDisplayCard
            addresses={establishment.addresses || []}
            getAddressTypeLabel={getAddressTypeLabel}
            formatZipCode={formatZipCode}
          />

          {/* Empresa */}
          <Card title="Empresa">
            <div className="space-y-4">
              <div>
                <div className="block text-sm font-medium text-muted-foreground mb-1">
                  Nome
                </div>
                <p className="text-foreground font-medium">
                  {establishment.company_name || "Não informado"}
                </p>
              </div>

              {establishment.company_tax_id && (
                <div>
                  <div className="block text-sm font-medium text-muted-foreground mb-1">
                    CNPJ
                  </div>
                  <p className="text-foreground font-mono text-sm">
                    {formatTaxId(establishment.company_tax_id)}
                  </p>
                </div>
              )}

              <div>
                <div className="block text-sm font-medium text-muted-foreground mb-1">
                  ID da Empresa
                </div>
                <p className="text-foreground font-mono text-sm">
                  {establishment.company_id}
                </p>
              </div>
            </div>
          </Card>

          {/* Informações do Sistema */}
          <Card title="Informações do Sistema">
            <div className="space-y-4 text-sm">
              <div>
                <label className="block text-muted-foreground mb-1">
                  ID do Estabelecimento
                </label>
                <p className="text-foreground font-mono">#{establishment.id}</p>
              </div>

              <div>
                <label className="block text-muted-foreground mb-1">
                  Criado em
                </label>
                <p className="text-foreground">
                  {establishment.created_at
                    ? new Date(establishment.created_at).toLocaleString("pt-BR")
                    : "Não informado"}
                </p>
              </div>

              {establishment.updated_at && (
                <div>
                  <label className="block text-muted-foreground mb-1">
                    Atualizado em
                  </label>
                  <p className="text-foreground">
                    {new Date(establishment.updated_at).toLocaleString("pt-BR")}
                  </p>
                </div>
              )}

              <div>
                <label className="block text-muted-foreground mb-1">
                  Ordem de Exibição
                </label>
                <p className="text-foreground">
                  {establishment.display_order || 0}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Tab: Clientes */}
      {activeTab === "clientes" && establishment && (
        <div className="space-y-6">
          <EstablishmentClientsTab
            establishmentId={establishmentId}
            establishmentCode={establishment.code}
            establishmentName={establishment.person?.name || establishment.code}
          />
        </div>
      )}

      {/* Tab: Usuários */}
      {activeTab === "usuarios" && establishment && (
        <Card
          title="Usuários do Estabelecimento"
          icon={<Users className="h-5 w-5" />}
        >
          <div className="space-y-6">
            {/* Resumo de Usuários */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Total
                    </p>
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {establishment.user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                    <Activity className="h-6 w-6 text-green-600 dark:text-green-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Ativos
                    </p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {establishment.active_user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <Shield className="h-6 w-6 text-purple-600 dark:text-purple-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Administradores
                    </p>
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {establishment.admin_user_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Lista de Usuários */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-foreground">
                  Usuários Cadastrados
                </h3>
                <Button size="sm" variant="primary" onClick={handleAddUser}>
                  <User className="h-4 w-4 mr-2" />
                  Adicionar Usuário
                </Button>
              </div>

              {establishment.users && establishment.users.length > 0 ? (
                <div className="space-y-3">
                  {establishment.users.map((user) => (
                    <div
                      key={user.id}
                      className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <User className="h-5 w-5 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">
                            {user.person_name || user.email}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {user.email} •{" "}
                            {user.role_display_name || user.role_name}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.is_active
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
                          }`}
                        >
                          {user.is_active ? "Ativo" : "Inativo"}
                        </span>
                        {user.is_system_admin && (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                            Admin
                          </span>
                        )}
                        <Button size="sm" variant="secondary" outline>
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-muted/30 rounded-lg">
                  <Users className="mx-auto h-12 w-12 text-muted-foreground/50" />
                  <h3 className="mt-4 text-lg font-medium text-foreground">
                    Nenhum usuário encontrado
                  </h3>
                  <p className="mt-2 text-muted-foreground">
                    Este estabelecimento ainda não possui usuários cadastrados.
                  </p>
                  <Button
                    className="mt-4"
                    variant="primary"
                    onClick={handleAddUser}
                  >
                    <User className="h-4 w-4 mr-2" />
                    Adicionar Primeiro Usuário
                  </Button>
                </div>
              )}
            </div>

            {/* Permissões e Acessos */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Controle de Acesso
              </h3>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-foreground mb-2">
                      Perfis Disponíveis
                    </h4>
                    <div className="space-y-2">
                      {["Administrador", "Gestor", "Operador", "Consulta"].map(
                        (role, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between"
                          >
                            <span className="text-sm text-muted-foreground">
                              {role}
                            </span>
                            <span className="text-sm font-medium text-foreground">
                              {Math.floor(Math.random() * 5)}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground mb-2">
                      Últimos Acessos
                    </h4>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">
                        Sistema em desenvolvimento...
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Tab: Equipe */}
      {activeTab === "equipe" && establishment && (
        <Card
          title="Equipe do Estabelecimento"
          icon={<User className="h-5 w-5" />}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <User className="h-6 w-6 text-blue-600 dark:text-blue-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Usuários
                    </p>
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {establishment.user_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                    <UserCog className="h-6 w-6 text-green-600 dark:text-green-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Profissionais
                    </p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {establishment.professional_count || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <Building2 className="h-6 w-6 text-purple-600 dark:text-purple-300" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-muted-foreground">
                      Clientes
                    </p>
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {establishment.client_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">
                Detalhes da equipe do estabelecimento ainda não foram
                implementados.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Tab: Configurações */}
      {activeTab === "configuracoes" && establishment && (
        <Card
          title="Configurações do Estabelecimento"
          icon={<Settings className="h-5 w-5" />}
        >
          <div className="space-y-6">
            {/* Configurações Gerais */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Configurações Gerais
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card title="Status e Visibilidade">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Status do estabelecimento
                      </span>
                      <span
                        className={getStatusBadge(
                          establishment.is_active ? "active" : "inactive"
                        )}
                      >
                        {getStatusLabel(
                          establishment.is_active ? "active" : "inactive"
                        )}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Estabelecimento principal
                      </span>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          establishment.is_principal
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400"
                            : "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
                        }`}
                      >
                        {establishment.is_principal ? "Sim" : "Não"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Ordem de exibição
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.display_order || 0}
                      </span>
                    </div>
                  </div>
                </Card>

                <Card title="Informações de Contato">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Telefones cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.phones?.length || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        E-mails cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.emails?.length || 0}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">
                        Endereços cadastrados
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {establishment.addresses?.length || 0}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>

            {/* Configurações Avançadas */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Configurações Avançadas
              </h3>
              <div className="bg-muted/30 p-6 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-foreground mb-3 flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Segurança
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Autenticação 2FA
                        </span>
                        <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded">
                          Não configurado
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Backup automático
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                          Ativo
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-3 flex items-center gap-2">
                      <Briefcase className="h-4 w-4" />
                      Operacional
                    </h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Horário de funcionamento
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          08:00 - 18:00
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          Agendamento online
                        </span>
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                          Habilitado
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-border">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-4">
                      Configurações detalhadas e personalizações específicas do
                      estabelecimento serão implementadas em futuras
                      atualizações.
                    </p>
                    <Button variant="primary" size="sm">
                      <Settings className="h-4 w-4 mr-2" />
                      Configurar Estabelecimento
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Histórico de Alterações */}
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">
                Histórico
              </h3>
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <Clock className="h-4 w-4 text-green-600 dark:text-green-300" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          Estabelecimento criado
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {establishment.created_at
                            ? new Date(
                                establishment.created_at
                              ).toLocaleDateString("pt-BR")
                            : "Data não informada"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {establishment.updated_at && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <Edit className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">
                            Última modificação
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(
                              establishment.updated_at
                            ).toLocaleDateString("pt-BR")}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </EntityDetailsLayout>
  );
};

// Componente para a aba de Clientes do Estabelecimento
const EstablishmentClientsTab = ({
  establishmentId,
  establishmentCode,
  establishmentName,
}) => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadClients = useCallback(async () => {
    try {
      setLoading(true);
      const clientsData = await clientsService.getByEstablishment(
        establishmentId
      );
      const clientsList = clientsData || [];
      setClients(clientsList);
    } catch (err) {
      console.error("Erro ao carregar clientes:", err);
      setClients([]);
    } finally {
      setLoading(false);
    }
  }, [establishmentId]);

  useEffect(() => {
    if (establishmentId) {
      loadClients();
    }
  }, [loadClients]);

  const dataTableProps = useDataTable({
    config: createEstablishmentClientsConfig(
      establishmentId,
      establishmentCode
    ),
    initialData: clients,
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-3 text-muted-foreground">
          Carregando clientes...
        </span>
      </div>
    );
  }

  return (
    <DataTableTemplate
      config={createEstablishmentClientsConfig(
        establishmentId,
        establishmentCode
      )}
      tableData={dataTableProps}
    />
  );
};

export default EstablishmentDetails;
