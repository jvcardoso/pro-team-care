import React, { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { usersService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import DataTableTemplate from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { usersConfig } from "../config/tables/users.config";
import { notify } from "../utils/notifications.jsx";
import { Plus } from "lucide-react";
import Button from "../components/ui/Button";

const UsersPage = () => {
  return (
    <PageErrorBoundary pageName="Usuários">
      <UsersPageContent />
    </PageErrorBoundary>
  );
};

const UsersPageContent = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Calculate metric values
  const calculateMetricValue = (metricId) => {
    switch (metricId) {
      case "total_users":
        return users.length;
      case "active_users":
        return users.filter((u) => u.user_is_active === true).length;
      case "inactive_users":
        return users.filter((u) => u.user_is_active === false).length;
      case "admin_users":
        return users.filter((u) => u.user_is_system_admin === true).length;
      default:
        return 0;
    }
  };

  // Memoize metrics to avoid recalculating on every render
  const metrics = useMemo(
    () => ({
      ...usersConfig.metrics,
      primary: usersConfig.metrics.primary.map((metric) => ({
        ...metric,
        value: calculateMetricValue(metric.id),
      })),
    }),
    [users]
  );

  // Initialize data table hook
  const dataTableProps = useDataTable({
    config: {
      ...usersConfig,
      metrics,
    },
    initialData: users,
  });

  // Load users data
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoading(true);
        const response = await usersService.getUsers({
          skip: 0,
          limit: 1000, // Load more for table processing
        });

        const usersList = response.users || [];
        setUsers(usersList);
      } catch (error) {
        console.error("Erro ao carregar usuários:", error);
        notify.error("Erro ao carregar usuários");
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    loadUsers();
  }, []);

  // Handle actions
  const handleView = (user) => {
    navigate(`/admin/usuarios/${user.user_id}?tab=informacoes`);
  };

  const handleEdit = (user) => {
    navigate(`/admin/usuarios/${user.user_id}/editar`);
  };

  const handleChangePassword = (user) => {
    // TODO: Implement change password modal
    console.log("Change password for user:", user);
  };

  const handleToggleStatus = async (user) => {
    try {
      await usersService.toggleUserStatus(user.user_id, !user.user_is_active);
      notify.success(
        `Usuário ${
          !user.user_is_active ? "ativado" : "desativado"
        } com sucesso!`
      );
      // Reload users
      const response = await usersService.getUsers({
        skip: 0,
        limit: 1000,
      });
      const usersList = Array.isArray(response) ? response : [];
      setUsers(usersList);
    } catch (error) {
      notify.error("Erro ao alterar status do usuário");
      console.error(error);
    }
  };

  // Update config with action handlers
  const configWithActions = {
    ...usersConfig,
    actions: usersConfig.actions.map((action) => ({
      ...action,
      onClick: (user) => {
        switch (action.id) {
          case "view":
            handleView(user);
            break;
          case "edit":
            handleEdit(user);
            break;
          case "change_password":
            handleChangePassword(user);
            break;
          case "toggle_status":
            handleToggleStatus(user);
            break;
        }
      },
    })),
    metrics,
  };

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

      {/* Data Table */}
      <DataTableTemplate
        config={configWithActions}
        tableData={dataTableProps}
        loading={loading}
      />
    </div>
  );
};

export default UsersPage;
