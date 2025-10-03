import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Card from "../components/ui/Card";
import ActionDropdown from "../components/ui/ActionDropdown";
import RoleMobileCard from "../components/mobile/RoleMobileCard";
import { RoleForm } from "../components/forms/RoleForm";
import { rolesService } from "../services/rolesService";
import AccessDeniedError from "../components/error/AccessDeniedError";
import useErrorHandler from "../hooks/useErrorHandler";

export const RolesPage = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [viewingRole, setViewingRole] = useState(null);

  // Use error handler hook
  const {
    handleError,
    clearError,
    retry,
    isAccessDenied,
    hasError,
    userMessage,
    statusCode,
  } = useErrorHandler();
  const [filters, setFilters] = useState({
    search: "",
    context_type: "",
    is_active: "",
    level_min: "",
    level_max: "",
  });
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0,
    total_pages: 0,
  });

  // Navigation
  const navigate = useNavigate();
  const { id } = useParams();

  const loadRoles = async () => {
    try {
      setLoading(true);
      clearError(); // Clear previous errors

      const params = {
        ...filters,
        skip: (pagination.page - 1) * pagination.size,
        limit: pagination.size,
      };

      // Remove empty filters
      Object.keys(params).forEach((key) => {
        if (
          params[key] === "" ||
          params[key] === null ||
          params[key] === undefined
        ) {
          delete params[key];
        }
      });

      const response = await rolesService.listRoles(params);
      setRoles(response.roles || []);
      setPagination({
        page: response.page || pagination.page,
        size: response.size || pagination.size,
        total: response.total || 0,
        total_pages:
          response.total_pages ||
          Math.ceil((response.total || 0) / pagination.size),
      });
    } catch (err) {
      console.error("Erro ao carregar perfis:", err);
      handleError(err);
      setRoles([]); // Clear roles on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoles();
  }, [pagination.page, pagination.size]);

  // Handle URL parameters for direct navigation
  useEffect(() => {
    if (id) {
      console.log("🔍 ID do perfil detectado na URL:", id);
      // Encontrar o role e abrir em modo de visualização
      const role = roles.find((r) => r.id === parseInt(id));
      if (role) {
        setViewingRole(role);
        setShowForm(true);
      }
    }
  }, [id, roles]);

  const handleSearch = () => {
    setPagination((prev) => ({ ...prev, page: 1 }));
    loadRoles();
  };

  const handleClearFilters = () => {
    setFilters({
      search: "",
      context_type: "",
      is_active: "",
      level_min: "",
      level_max: "",
    });
    setPagination((prev) => ({ ...prev, page: 1 }));
    setTimeout(loadRoles, 100);
  };

  const handleView = (role) => {
    // Usar URL params em vez de estado interno (Padrão C)
    navigate(`/admin/perfis/${role.id}?tab=informacoes`);
  };

  const handleEdit = (role) => {
    setEditingRole(role);
    setShowForm(true);
  };

  const handleDelete = async (roleId, roleName) => {
    const confirmMessage = `Tem certeza que deseja excluir o perfil "${roleName}"?\n\nEsta ação não pode ser desfeita.`;
    if (!confirm(confirmMessage)) return;

    try {
      setLoading(true);
      clearError();
      await rolesService.deleteRole(roleId);
      loadRoles();
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async (formData) => {
    try {
      if (editingRole) {
        await rolesService.updateRole(editingRole.id, formData);
      } else {
        await rolesService.createRole(formData);
      }

      setShowForm(false);
      setEditingRole(null);
      loadRoles();
    } catch (err) {
      throw new Error("Erro ao salvar perfil: " + err.message);
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

  // Componente para visualização de perfil como página
  const RoleViewDetails = ({ role }) => {
    const [rolePermissions, setRolePermissions] = useState([]);
    const [loadingPermissions, setLoadingPermissions] = useState(true);

    useEffect(() => {
      const loadPermissions = async () => {
        try {
          setLoadingPermissions(true);
          const permissions = await rolesService.getRolePermissions(role.id);
          setRolePermissions(permissions);
        } catch (err) {
          console.error("Erro ao carregar permissões:", err);
        } finally {
          setLoadingPermissions(false);
        }
      };

      if (role?.id) {
        loadPermissions();
      }
    }, [role?.id]);

    return (
      <div className="space-y-6">
        <Card className="p-4 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Informações Básicas
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome Técnico
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 dark:bg-gray-700 p-2 rounded">
                {role.name}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome de Exibição
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 dark:bg-gray-700 p-2 rounded">
                {role.display_name}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contexto
              </label>
              <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                {getContextTypeLabel(role.context_type)}
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nível Hierárquico
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 dark:bg-gray-700 p-2 rounded">
                {role.level} - {getLevelLabel(role.level)}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Perfil do Sistema
              </label>
              <span
                className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  role.is_system_role
                    ? "bg-purple-100 text-purple-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {role.is_system_role ? "Sim" : "Não"}
              </span>
            </div>
          </div>

          {role.description && (
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Descrição
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 dark:bg-gray-700 p-3 rounded">
                {role.description}
              </p>
            </div>
          )}
        </Card>

        <Card className="p-4 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Permissões ({rolePermissions.length})
          </h3>

          {loadingPermissions ? (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Carregando permissões...
              </p>
            </div>
          ) : rolePermissions.length > 0 ? (
            <div className="space-y-4">
              {Object.entries(
                rolePermissions.reduce((acc, permission) => {
                  if (!acc[permission.module]) {
                    acc[permission.module] = [];
                  }
                  acc[permission.module].push(permission);
                  return acc;
                }, {})
              ).map(([module, permissions]) => (
                <div
                  key={module}
                  className="border border-gray-200 rounded-lg p-3"
                >
                  <h4 className="font-medium text-gray-900 mb-2 capitalize">
                    {module} ({permissions.length})
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {permissions.map((permission) => (
                      <div
                        key={permission.id}
                        className="flex items-center space-x-2 p-2 bg-green-50 rounded"
                      >
                        <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0"></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-gray-900 truncate">
                            {permission.display_name}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {permission.action} • {permission.resource}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-4">
              Este perfil não possui permissões atribuídas.
            </p>
          )}
        </Card>

        <Card className="p-4 sm:p-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Informações do Sistema
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-gray-500 dark:text-gray-400">
            <div>
              <span className="font-medium">ID:</span> {role.id}
            </div>
            <div>
              <span className="font-medium">Criado em:</span>{" "}
              {role.created_at
                ? new Date(role.created_at).toLocaleString("pt-BR")
                : "N/A"}
            </div>
            {role.updated_at && (
              <div>
                <span className="font-medium">Atualizado em:</span>{" "}
                {new Date(role.updated_at).toLocaleString("pt-BR")}
              </div>
            )}
          </div>
        </Card>
      </div>
    );
  };

  if (showForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => {
              setShowForm(false);
              setEditingRole(null);
              setViewingRole(null);
            }}
          >
            ← Voltar
          </Button>
        </div>

        {viewingRole ? (
          <RoleViewDetails role={viewingRole} />
        ) : (
          <RoleForm
            initialData={editingRole}
            onSubmit={handleFormSubmit}
            onCancel={() => {
              setShowForm(false);
              setEditingRole(null);
              setViewingRole(null);
            }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 p-4 sm:p-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-muted-foreground">
            Gerencie os perfis e permissões do sistema
          </p>
        </div>
        <Button
          onClick={() => setShowForm(true)}
          icon={<span className="text-lg">+</span>}
          className="shrink-0"
        >
          <span className="hidden sm:inline">Novo Perfil</span>
          <span className="sm:hidden">Novo</span>
        </Button>
      </div>

      {/* Filtros Responsivos */}
      <Card className="p-3 sm:p-4">
        <div className="space-y-4">
          {/* Busca principal */}
          <div className="w-full">
            <Input
              placeholder="Buscar perfis..."
              value={filters.search}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, search: e.target.value }))
              }
              className="w-full"
            />
          </div>

          {/* Filtros em grid responsivo */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <select
              className="border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm"
              value={filters.context_type}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  context_type: e.target.value,
                }))
              }
            >
              <option value="">Todos os contextos</option>
              <option value="system">Sistema</option>
              <option value="company">Empresa</option>
              <option value="establishment">Estabelecimento</option>
            </select>

            <select
              className="border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm"
              value={filters.is_active}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, is_active: e.target.value }))
              }
            >
              <option value="">Todos os status</option>
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>

            <Input
              type="number"
              placeholder="Nível mín"
              min="10"
              max="100"
              value={filters.level_min}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, level_min: e.target.value }))
              }
              className="text-sm"
            />

            <Input
              type="number"
              placeholder="Nível máx"
              min="10"
              max="100"
              value={filters.level_max}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, level_max: e.target.value }))
              }
              className="text-sm"
            />
          </div>

          {/* Botões de ação */}
          <div className="flex flex-col sm:flex-row gap-2">
            <Button onClick={handleSearch} className="flex-1 sm:flex-none">
              Filtrar
            </Button>
            <Button
              variant="outline"
              onClick={handleClearFilters}
              className="flex-1 sm:flex-none"
            >
              Limpar Filtros
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <div className="h-6 w-6 text-blue-600 dark:text-blue-300 flex items-center justify-center font-bold text-sm">
                👥
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total Perfis</p>
              <p className="text-2xl font-bold text-foreground">
                {pagination.total}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <div className="h-6 w-6 text-green-600 dark:text-green-300 flex items-center justify-center font-bold text-sm">
                ✓
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativos</p>
              <p className="text-2xl font-bold text-foreground">
                {roles.filter((r) => r.is_active === true).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <div className="h-6 w-6 text-purple-600 dark:text-purple-300 flex items-center justify-center font-bold text-sm">
                ⚙️
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Sistema</p>
              <p className="text-2xl font-bold text-foreground">
                {roles.filter((r) => r.is_system_role === true).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <div className="h-6 w-6 text-orange-600 dark:text-orange-300 flex items-center justify-center font-bold text-sm">
                🏢
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Empresa</p>
              <p className="text-2xl font-bold text-foreground">
                {roles.filter((r) => r.context_type === "company").length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Lista de Perfis */}
      {loading ? (
        <div className="space-y-6">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Carregando perfis...</p>
          </div>
        </div>
      ) : hasError && roles.length === 0 ? (
        // Show specific error component based on error type
        isAccessDenied ? (
          <AccessDeniedError
            title="Acesso Negado aos Perfis"
            message="Você não possui permissão para visualizar os perfis do sistema. Entre em contato com o administrador para solicitar acesso a esta funcionalidade."
            resource="perfis do sistema"
            action="visualizar"
            onRetry={() => {
              retry();
              loadRoles();
            }}
          />
        ) : (
          <div className="space-y-6">
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-red-600 text-2xl">⚠️</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Erro ao Carregar Perfis
              </h3>
              <p className="text-red-600 mb-4">{userMessage}</p>
              {statusCode && (
                <p className="text-sm text-gray-500 mb-4">
                  Código do erro: {statusCode}
                </p>
              )}
              <Button
                onClick={() => {
                  retry();
                  loadRoles();
                }}
              >
                Tentar Novamente
              </Button>
            </div>
          </div>
        )
      ) : (
        <Card title="Lista de Perfis" className="overflow-visible">
          {roles.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-lg mb-2">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Nenhum perfil encontrado
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                {Object.values(filters).some((v) => v !== "")
                  ? "Tente ajustar os filtros de busca"
                  : "Comece criando o primeiro perfil do sistema"}
              </p>
            </div>
          ) : (
            <>
              {/* Desktop: Tabela */}
              <div className="hidden lg:block overflow-x-auto overflow-y-visible">
                <table className="w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-2/5">
                        Perfil
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">
                        Contexto
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/8">
                        Nível
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/8">
                        Status
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/8">
                        Sistema
                      </th>
                      <th className="relative px-3 py-3 w-16">
                        <span className="sr-only">Ações</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
                    {roles.map((role) => (
                      <tr key={role.id} className="hover:bg-gray-50">
                        <td className="px-3 py-4">
                          <div className="max-w-xs">
                            <div className="text-sm font-medium text-gray-900 truncate">
                              {role.display_name}
                            </div>
                            <div className="text-xs text-gray-500 truncate">
                              {role.name}
                            </div>
                            {role.description && (
                              <div className="text-xs text-gray-400 mt-1 truncate">
                                {role.description.length > 40
                                  ? role.description.substring(0, 40) + "..."
                                  : role.description}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            {getContextTypeLabel(role.context_type)}
                          </span>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {role.level}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {getLevelLabel(role.level)}
                          </div>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              role.is_active
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {role.is_active ? "Ativo" : "Inativo"}
                          </span>
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap">
                          {role.is_system_role ? (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">
                              Sistema
                            </span>
                          ) : (
                            <span className="text-sm text-gray-500 dark:text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-3 py-4 whitespace-nowrap text-center">
                          <ActionDropdown>
                            <ActionDropdown.Item
                              onClick={() => handleView(role)}
                            >
                              Ver Detalhes
                            </ActionDropdown.Item>
                            <ActionDropdown.Item
                              onClick={() => handleEdit(role)}
                              disabled={role.is_system_role}
                            >
                              Editar
                            </ActionDropdown.Item>
                            <ActionDropdown.Item
                              onClick={() =>
                                handleDelete(role.id, role.display_name)
                              }
                              disabled={role.is_system_role}
                              variant="danger"
                            >
                              Excluir
                            </ActionDropdown.Item>
                          </ActionDropdown>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Tablet: Cards compactos */}
              <div className="hidden md:block lg:hidden space-y-3 p-4">
                {roles.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-lg mb-2">📋</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Nenhum perfil encontrado
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      {Object.values(filters).some((v) => v !== "")
                        ? "Tente ajustar os filtros de busca"
                        : "Comece criando o primeiro perfil do sistema"}
                    </p>
                  </div>
                ) : (
                  roles.map((role) => (
                    <div
                      key={role.id}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0 grid grid-cols-4 gap-4">
                          <div className="col-span-2">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {role.display_name}
                            </h3>
                            <p className="text-xs text-gray-500 truncate">
                              {role.name}
                            </p>
                            {role.description && (
                              <p className="text-xs text-gray-400 mt-1 truncate">
                                {role.description.length > 40
                                  ? role.description.substring(0, 40) + "..."
                                  : role.description}
                              </p>
                            )}
                          </div>
                          <div className="text-center">
                            <span className="px-2 py-1 text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                              {getContextTypeLabel(role.context_type)}
                            </span>
                            <div className="text-xs text-gray-500 mt-1">
                              Nível {role.level}
                            </div>
                          </div>
                          <div className="text-center">
                            <span
                              className={`px-2 py-1 text-xs leading-5 font-semibold rounded-full ${
                                role.is_active
                                  ? "bg-green-100 text-green-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {role.is_active ? "Ativo" : "Inativo"}
                            </span>
                            {role.is_system_role && (
                              <div className="mt-1">
                                <span className="px-2 py-1 text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">
                                  Sistema
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <ActionDropdown>
                            <ActionDropdown.Item
                              onClick={() => handleView(role)}
                            >
                              Ver Detalhes
                            </ActionDropdown.Item>
                            <ActionDropdown.Item
                              onClick={() => handleEdit(role)}
                              disabled={role.is_system_role}
                            >
                              Editar
                            </ActionDropdown.Item>
                            <ActionDropdown.Item
                              onClick={() =>
                                handleDelete(role.id, role.display_name)
                              }
                              disabled={role.is_system_role}
                              variant="danger"
                            >
                              Excluir
                            </ActionDropdown.Item>
                          </ActionDropdown>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden space-y-4">
                {roles.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-lg mb-2">📋</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Nenhum perfil encontrado
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      {Object.values(filters).some((v) => v !== "")
                        ? "Tente ajustar os filtros de busca"
                        : "Comece criando o primeiro perfil do sistema"}
                    </p>
                  </div>
                ) : (
                  roles.map((role) => (
                    <RoleMobileCard
                      key={role.id}
                      role={role}
                      onView={handleView}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))
                )}
              </div>

              {/* Paginação */}
              {pagination.total_pages > 1 && (
                <div className="bg-white dark:bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <Button
                      variant="outline"
                      disabled={pagination.page <= 1}
                      onClick={() =>
                        setPagination((prev) => ({
                          ...prev,
                          page: prev.page - 1,
                        }))
                      }
                    >
                      Anterior
                    </Button>
                    <Button
                      variant="outline"
                      disabled={pagination.page >= pagination.total_pages}
                      onClick={() =>
                        setPagination((prev) => ({
                          ...prev,
                          page: prev.page + 1,
                        }))
                      }
                    >
                      Próximo
                    </Button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        Mostrando{" "}
                        <span className="font-medium">
                          {(pagination.page - 1) * pagination.size + 1}
                        </span>{" "}
                        a{" "}
                        <span className="font-medium">
                          {Math.min(
                            pagination.page * pagination.size,
                            pagination.total
                          )}
                        </span>{" "}
                        de{" "}
                        <span className="font-medium">{pagination.total}</span>{" "}
                        resultados
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <Button
                          variant="outline"
                          disabled={pagination.page <= 1}
                          onClick={() =>
                            setPagination((prev) => ({
                              ...prev,
                              page: prev.page - 1,
                            }))
                          }
                          className="rounded-l-md"
                        >
                          Anterior
                        </Button>

                        {[...Array(pagination.total_pages)].map((_, i) => {
                          const pageNum = i + 1;
                          if (
                            pageNum === 1 ||
                            pageNum === pagination.total_pages ||
                            (pageNum >= pagination.page - 2 &&
                              pageNum <= pagination.page + 2)
                          ) {
                            return (
                              <Button
                                key={pageNum}
                                variant={
                                  pageNum === pagination.page
                                    ? "default"
                                    : "outline"
                                }
                                onClick={() =>
                                  setPagination((prev) => ({
                                    ...prev,
                                    page: pageNum,
                                  }))
                                }
                                className="border-l-0"
                              >
                                {pageNum}
                              </Button>
                            );
                          } else if (
                            pageNum === pagination.page - 3 ||
                            pageNum === pagination.page + 3
                          ) {
                            return (
                              <span
                                key={pageNum}
                                className="px-3 py-2 text-gray-500 dark:text-gray-400"
                              >
                                ...
                              </span>
                            );
                          }
                          return null;
                        })}

                        <Button
                          variant="outline"
                          disabled={pagination.page >= pagination.total_pages}
                          onClick={() =>
                            setPagination((prev) => ({
                              ...prev,
                              page: prev.page + 1,
                            }))
                          }
                          className="rounded-r-md border-l-0"
                        >
                          Próximo
                        </Button>
                      </nav>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </Card>
      )}
    </div>
  );
};
