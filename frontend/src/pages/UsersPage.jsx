import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { usersService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import UserForm from "../components/forms/UserForm";
import UserDetails from "../components/views/UserDetails";
import UserMobileCard from "../components/mobile/UserMobileCard";
import ActionDropdown from "../components/ui/ActionDropdown";
import ChangePasswordModal from "../components/forms/ChangePasswordModal";
import { getStatusBadge, getStatusLabel } from "../utils/statusUtils";
import { notify } from "../utils/notifications.jsx";
import {
  Users,
  Search,
  Plus,
  Filter,
  Phone,
  Mail,
  Edit,
  Eye,
  Key,
  Calendar,
  UserCheck,
  UserX,
  UserPlus,
  ArrowUpDown,
} from "lucide-react";

const UsersPage = () => {
  return (
    <PageErrorBoundary pageName="Usuários">
      <UsersPageContent />
    </PageErrorBoundary>
  );
};

const UsersPageContent = () => {
  // Add error boundary logging
  if (typeof window !== "undefined") {
    window.addEventListener("error", (e) => {
      console.error("Page Error:", e.error);
    });
  }
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("todos");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] =
    useState(false);
  const [selectedUserForPassword, setSelectedUserForPassword] = useState(null);

  // URL parameters support
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { id } = useParams();
  const establishmentId = searchParams.get("establishmentId");
  const actionParam = searchParams.get("action");

  // Handle URL parameters for direct navigation from establishment
  useEffect(() => {
    // Se há um ID na URL, mostrar detalhes do usuário
    if (id) {
      console.log("🔍 ID do usuário detectado na URL:", id);
      setSelectedUserId(parseInt(id));
      setCurrentView("details");
    } else if (actionParam === "create") {
      setCurrentView("create");
    }
  }, [actionParam, id]);

  // Debounce search term
  useEffect(() => {
    if (currentView !== "list") return;

    const timeoutId = setTimeout(
      () => {
        loadUsers();
        loadTotalCount();
      },
      searchTerm ? 500 : 0
    ); // 500ms debounce for search, immediate for other filters

    return () => clearTimeout(timeoutId);
  }, [currentPage, searchTerm, filterStatus, currentView]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors

      const params = {
        page: currentPage,
        size: itemsPerPage,
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && {
          is_active: filterStatus === "active",
        }),
      };

      console.log("Loading users with params:", params);
      const response = await usersService.getUsers(params);
      console.log("Users response:", response);

      // Backend retorna { items: [...], total, page, per_page, pages }
      const users = response?.items || response?.users || response || [];
      console.log("Users extracted:", users?.length || 0);

      // Remove duplicates based on user_id to prevent React key warnings
      const uniqueUsers = Array.isArray(users)
        ? users.filter(
            (user, index, self) =>
              index === self.findIndex((u) => u.user_id === user.user_id)
          )
        : [];

      console.log("Unique users after deduplication:", uniqueUsers.length);
      setUsers(uniqueUsers);
    } catch (err) {
      console.error("Error loading users:", err);
      setError(
        `Erro ao carregar usuários: ${err.message || "Erro desconhecido"}`
      );
      setUsers([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const loadTotalCount = async () => {
    try {
      const params = {
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && {
          is_active: filterStatus === "active",
        }),
      };
      const data = await usersService.getUsersCount(params);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error("Erro ao carregar contagem:", err);
      setTotalCount(0);
    }
  };

  const handleToggleStatus = async (userId, newStatus) => {
    const user = users.find((u) => u.user_id === userId);
    const userName = user?.person_name || user?.user_email || "este usuário";
    const action = newStatus ? "ativar" : "inativar";

    const executeToggle = async () => {
      try {
        await usersService.toggleUserStatus(userId, newStatus);
        notify.success(
          `Usuário ${
            action === "ativar" ? "ativado" : "inativado"
          } com sucesso!`
        );
        loadUsers();
        loadTotalCount();
      } catch (err) {
        notify.error(`Erro ao ${action} usuário`);
        console.error(err);
      }
    };

    notify.confirm(
      `${action === "ativar" ? "Ativar" : "Inativar"} Usuário`,
      `Tem certeza que deseja ${action} o usuário "${userName}"?`,
      executeToggle
    );
  };

  const handleChangePassword = (user) => {
    setSelectedUserForPassword(user);
    setIsChangePasswordModalOpen(true);
  };

  const handleCreate = () => {
    // Garantir limpeza completa do estado antes de criar
    setSelectedUserId(null);
    setCurrentView("create");
    // Pequeno delay para garantir que o estado seja atualizado
    setTimeout(() => {
      if (selectedUserId !== null) {
        console.warn(
          "selectedUserId não foi limpo adequadamente, forçando limpeza"
        );
        setSelectedUserId(null);
      }
    }, 0);
  };

  const handleEdit = (userId) => {
    setSelectedUserId(userId);
    setCurrentView("edit");
  };

  const handleView = (userId) => {
    // Usar URL params em vez de estado interno (Padrão C)
    navigate(`/admin/usuarios/${userId}?tab=informacoes`);
  };

  const handleSave = () => {
    setCurrentView("list");
    setSelectedUserId(null);
    loadUsers();
    loadTotalCount();
  };

  const handleCancel = () => {
    setCurrentView("list");
    setSelectedUserId(null);
    // Limpar qualquer estado residual
    setTimeout(() => {
      if (currentView !== "list" || selectedUserId !== null) {
        console.warn("Estado não foi limpo adequadamente no cancelamento");
        setCurrentView("list");
        setSelectedUserId(null);
      }
    }, 0);
  };

  const handleBack = () => {
    // Voltar para lista de usuários
    navigate("/admin/usuarios", { replace: true });
  };

  const handleDeleteFromDetails = () => {
    // Voltar para lista após exclusão
    navigate("/admin/usuarios", { replace: true });
    loadUsers();
    loadTotalCount();
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    // Garantir que userId seja null no modo de criação
    const userIdToPass = currentView === "create" ? null : selectedUserId;

    return (
      <UserForm
        userId={userIdToPass}
        establishmentId={establishmentId}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    );
  }

  if (currentView === "details") {
    return (
      <UserDetails
        userId={selectedUserId}
        onEdit={handleEdit}
        onBack={handleBack}
        onDelete={handleDeleteFromDetails}
      />
    );
  }

  // List view loading states
  if (loading && users.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando usuários...</p>
        </div>
      </div>
    );
  }

  if (error && users.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={loadUsers}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Usuários</h1>
          <p className="text-muted-foreground">
            Gerencie os usuários cadastrados no sistema
          </p>
        </div>
        <Button
          onClick={handleCreate}
          icon={<Plus className="h-4 w-4" />}
          className="shrink-0"
        >
          <span className="hidden sm:inline">Novo Usuário</span>
          <span className="sm:hidden">Novo</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          {/* Search and Status Filter */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="Buscar usuários..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="flex-1 min-w-0"
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none min-w-0 sm:w-48"
            >
              <option value="todos">Todos os status</option>
              <option value="active">Ativos</option>
              <option value="inactive">Inativos</option>
            </select>
          </div>

          {/* Additional Filters Button */}
          <div className="flex justify-end">
            <Button
              variant="secondary"
              outline
              icon={<Filter className="h-4 w-4" />}
            >
              <span className="hidden sm:inline">Filtros Avançados</span>
              <span className="sm:hidden">Filtros</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total Usuários</p>
              <p className="text-2xl font-bold text-foreground">{totalCount}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativos</p>
              <p className="text-2xl font-bold text-foreground">
                {users.filter((u) => u.user_is_active === true).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-gray-100 dark:bg-gray-900 rounded-lg">
              <UserX className="h-6 w-6 text-gray-600 dark:text-gray-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Inativos</p>
              <p className="text-2xl font-bold text-foreground">
                {users.filter((u) => u.user_is_active === false).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <UserX className="h-6 w-6 text-red-600 dark:text-red-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Administradores</p>
              <p className="text-2xl font-bold text-foreground">
                {users.filter((u) => u.user_is_system_admin === true).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Users Table */}
      <Card title="Lista de Usuários">
        {/* Desktop Table */}
        <div className="hidden lg:block">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Usuário
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Função
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Criado em
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, index) => (
                  <tr
                    key={`${user.user_id}-${index}`}
                    className="border-b border-border hover:bg-muted/50"
                  >
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium text-foreground">
                          {user.person_name || user.user_email}
                        </p>
                        {user.person_name &&
                          user.person_name !== user.user_email && (
                            <p className="text-sm text-muted-foreground">
                              {user.user_email}
                            </p>
                          )}
                        {!user.person_name && (
                          <p className="text-sm text-muted-foreground">
                            ID: {user.user_id}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col gap-1">
                        {user.user_is_system_admin ? (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            Administrador
                          </span>
                        ) : (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            Usuário
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={getStatusBadge(
                          user.user_is_active ? "active" : "inactive"
                        )}
                      >
                        {getStatusLabel(
                          user.user_is_active ? "active" : "inactive"
                        )}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      {user.user_created_at
                        ? new Date(user.user_created_at).toLocaleDateString(
                            "pt-BR"
                          )
                        : "-"}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-center">
                        {/* Action Dropdown - Todas as ações em um só lugar */}
                        <ActionDropdown>
                          <ActionDropdown.Item
                            icon={<Eye className="h-4 w-4" />}
                            onClick={() => handleView(user.user_id)}
                          >
                            Ver Detalhes
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<Edit className="h-4 w-4" />}
                            onClick={() => handleEdit(user.user_id)}
                            variant="default"
                          >
                            Editar Usuário
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<Key className="h-4 w-4" />}
                            onClick={() => handleChangePassword(user)}
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
                              handleToggleStatus(
                                user.user_id,
                                !user.user_is_active
                              )
                            }
                            variant={
                              user.user_is_active ? "warning" : "success"
                            }
                          >
                            {user.user_is_active
                              ? "Inativar Usuário"
                              : "Ativar Usuário"}
                          </ActionDropdown.Item>
                        </ActionDropdown>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tablet: Cards compactos */}
        <div className="hidden md:block lg:hidden space-y-3 p-4">
          {users.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhum usuário encontrado
              </p>
            </div>
          ) : (
            users.map((user, index) => (
              <div
                key={`${user?.user_id || "unknown"}-${index}`}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {user.person_name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {user.user_email}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                        {user.role_display_name || "Sem função"}
                      </p>
                    </div>
                    <div className="text-center">
                      <span className={getStatusBadge(user.user_is_active)}>
                        {getStatusLabel(user.user_is_active)}
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {user.user_created_at
                          ? new Date(user.user_created_at).toLocaleDateString(
                              "pt-BR"
                            )
                          : "-"}
                      </p>
                    </div>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <ActionDropdown>
                      <ActionDropdown.Item
                        icon={<Eye className="h-4 w-4" />}
                        onClick={() => handleView(user.user_id)}
                      >
                        Ver Detalhes
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<Edit className="h-4 w-4" />}
                        onClick={() => handleEdit(user.user_id)}
                      >
                        Editar
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<ArrowUpDown className="h-4 w-4" />}
                        onClick={() =>
                          handleToggleStatus(user.user_id, user.user_is_active)
                        }
                      >
                        {user.user_is_active ? "Desativar" : "Ativar"}
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
          {users.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhum usuário encontrado
              </p>
            </div>
          ) : (
            users.map((user, index) => (
              <UserMobileCard
                key={`${user?.user_id || "unknown"}-${index}`}
                user={user}
                onView={handleView}
                onEdit={handleEdit}
                onToggleStatus={handleToggleStatus}
                getStatusBadge={getStatusBadge}
                getStatusLabel={getStatusLabel}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Mostrando{" "}
              {Math.min((currentPage - 1) * itemsPerPage + 1, totalCount)} a{" "}
              {Math.min(currentPage * itemsPerPage, totalCount)} de {totalCount}{" "}
              usuários
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                outline
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                outline
                size="sm"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Próxima
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={isChangePasswordModalOpen}
        onClose={() => {
          setIsChangePasswordModalOpen(false);
          setSelectedUserForPassword(null);
        }}
        user={selectedUserForPassword}
      />
    </div>
  );
};

export default UsersPage;
