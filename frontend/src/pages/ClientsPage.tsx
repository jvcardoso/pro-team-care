import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { clientsService } from "../services/clientsService";
import { PageErrorBoundary } from "../components/error";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import ClientForm from "../components/forms/ClientForm";
import ClientDetails from "../components/views/ClientDetails";
import ActionDropdown from "../components/ui/ActionDropdown";
import { getStatusBadge, getStatusLabel } from "../utils/statusUtils";
import { formatTaxId } from "../utils/formatters";
import { notify } from "../utils/notifications.jsx";
import { ClientDetailed, ClientStatus, PersonType } from "../types";
import {
  Users,
  Search,
  Plus,
  Filter,
  Phone,
  Mail,
  Edit,
  Eye,
  CreditCard,
  Calendar,
  UserCheck,
  UserX,
  Building2,
  MapPin,
  ArrowUpDown,
} from "lucide-react";

const ClientsPage: React.FC = () => {
  return (
    <PageErrorBoundary pageName="Clientes">
      <ClientsPageContent />
    </PageErrorBoundary>
  );
};

const ClientsPageContent: React.FC = () => {
  const [clients, setClients] = useState<ClientDetailed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("todos");
  const [filterPersonType, setFilterPersonType] = useState<string>("todos");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [currentView, setCurrentView] = useState<string>("list"); // 'list', 'create', 'edit', 'details'
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [selectedClient, setSelectedClient] = useState<ClientDetailed | null>(
    null
  );

  // Navigation
  const navigate = useNavigate();
  const { id } = useParams();

  // Debounce search term
  useEffect(() => {
    if (currentView !== "list") return;

    const timeoutId = setTimeout(
      () => {
        loadClients();
      },
      searchTerm ? 500 : 0
    ); // 500ms debounce for search, immediate for other filters

    return () => clearTimeout(timeoutId);
  }, [currentPage, searchTerm, filterStatus, filterPersonType, currentView]);

  // Handle URL parameters for direct navigation
  useEffect(() => {
    if (id) {
      console.log("🔍 ID do cliente detectado na URL:", id);
      setSelectedClientId(parseInt(id));
      setCurrentView("details");
    }
  }, [id]);

  const loadClients = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        page: currentPage,
        size: itemsPerPage,
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && {
          status: filterStatus as ClientStatus,
        }),
        ...(filterPersonType !== "todos" && {
          person_type: filterPersonType as PersonType,
        }),
      };

      console.log("Loading clients with params:", params);
      const response = await clientsService.getAll(params);
      console.log("Clients response:", response);

      const clientsData = response?.clients || [];
      setClients(clientsData);
      setTotalCount(response?.total || 0);
    } catch (err: any) {
      console.error("Error loading clients:", err);
      setError(`Erro ao carregar clientes: ${err.message}`);
      notify.error("Erro ao carregar clientes");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (
    clientId: number,
    newStatus: ClientStatus
  ) => {
    const client = clients.find((c) => c.id === clientId);
    const clientName = client?.name || "este cliente";
    const action = newStatus === ClientStatus.ACTIVE ? "ativar" : "inativar";

    const executeToggle = async () => {
      try {
        await clientsService.updateStatus(clientId, newStatus);
        notify.success(
          `Cliente ${
            action === "ativar" ? "ativado" : "inativado"
          } com sucesso!`
        );
        loadClients();
      } catch (err: any) {
        console.error("Error updating client status:", err);
        notify.error(`Erro ao ${action} cliente`);
      }
    };

    notify.confirm(
      `${action === "ativar" ? "Ativar" : "Inativar"} Cliente`,
      `Tem certeza que deseja ${action} o cliente "${clientName}"?`,
      executeToggle
    );
  };

  const handleDelete = async (clientId: number) => {
    const client = clients.find((c) => c.id === clientId);
    const clientName = client?.name || "este cliente";

    const executeDelete = async () => {
      try {
        await clientsService.delete(clientId);
        notify.success("Cliente excluído com sucesso!");
        loadClients();
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || "Erro desconhecido";
        notify.error(`Erro ao excluir cliente: ${errorMessage}`);
      }
    };

    notify.confirmDelete(
      "Excluir Cliente",
      `Tem certeza que deseja excluir o cliente "${clientName}"?`,
      executeDelete
    );
  };

  const handleView = (clientId: number) => {
    // Usar URL params em vez de estado interno (Padrão C)
    navigate(`/admin/clientes/${clientId}?tab=informacoes`);
  };

  const handleCreate = () => {
    setSelectedClientId(null);
    setSelectedClient(null);
    setCurrentView("create");
  };

  const handleEdit = (clientId: number) => {
    const client = clients.find((c) => c.id === clientId);
    setSelectedClient(client || null);
    setSelectedClientId(clientId);
    setCurrentView("edit");
  };

  const handleBackToList = () => {
    // Voltar para lista de clientes
    navigate("/admin/clientes", { replace: true });
    loadClients(); // Reload data
  };

  const handleSave = async (clientData: any) => {
    try {
      if (currentView === "edit" && selectedClientId) {
        await clientsService.update(selectedClientId, clientData);
        notify.success("Cliente atualizado com sucesso!");
      } else {
        await clientsService.create(clientData);
        notify.success("Cliente criado com sucesso!");
      }
      handleBackToList();
    } catch (err: any) {
      console.error("Error saving client:", err);
      notify.error(`Erro ao salvar cliente: ${err.message}`);
      throw err; // Re-throw to let form handle it
    }
  };

  const handleClearFilters = () => {
    setSearchTerm("");
    setFilterStatus("todos");
    setFilterPersonType("todos");
    setCurrentPage(1);
  };

  const totalPages = totalCount > 0 ? Math.ceil(totalCount / itemsPerPage) : 1;

  const formatPhone = (phone: string): string => {
    const clean = phone.replace(/\D/g, "");
    if (clean.length === 11) {
      return clean.replace(/(\d{2})(\d{5})(\d{4})/, "($1) $2-$3");
    } else if (clean.length === 10) {
      return clean.replace(/(\d{2})(\d{4})(\d{4})/, "($1) $2-$3");
    }
    return phone;
  };

  const getPersonTypeLabel = (type: PersonType): string => {
    return type === PersonType.PF ? "Pessoa Física" : "Pessoa Jurídica";
  };

  const getClientStatusLabel = (status: ClientStatus): string => {
    const labels = {
      [ClientStatus.ACTIVE]: "Ativo",
      [ClientStatus.INACTIVE]: "Inativo",
      [ClientStatus.ON_HOLD]: "Em Espera",
      [ClientStatus.ARCHIVED]: "Arquivado",
    };
    return labels[status] || status;
  };

  const getClientStatusColor = (status: ClientStatus): string => {
    const colors = {
      [ClientStatus.ACTIVE]: "bg-green-100 text-green-800",
      [ClientStatus.INACTIVE]: "bg-gray-100 text-gray-800",
      [ClientStatus.ON_HOLD]: "bg-yellow-100 text-yellow-800",
      [ClientStatus.ARCHIVED]: "bg-red-100 text-red-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    return (
      <ClientForm
        initialData={selectedClient || undefined}
        onCancel={handleBackToList}
        onSave={handleBackToList} // Será chamado após sucesso
        mode={currentView as "create" | "edit"}
      />
    );
  }

  if (currentView === "details" && selectedClient) {
    return (
      <ClientDetails
        client={selectedClient}
        onEdit={() => handleEdit(selectedClientId!)}
        onBack={handleBackToList}
        onDelete={() => {
          handleDelete(selectedClientId!);
          handleBackToList();
        }}
      />
    );
  }

  // List view loading states
  if (loading && clients.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando clientes...</p>
        </div>
      </div>
    );
  }

  if (error && clients.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={loadClients}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Clientes</h1>
          <p className="text-muted-foreground">
            Gerencie clientes e suas informações
          </p>
        </div>
        <Button
          onClick={handleCreate}
          icon={<Plus className="h-4 w-4" />}
          className="shrink-0"
        >
          <span className="hidden sm:inline">Novo Cliente</span>
          <span className="sm:hidden">Novo</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          {/* Search and Main Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Input
              placeholder="Buscar por nome, CPF/CNPJ ou código..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="sm:col-span-2"
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todos">Todos os status</option>
              <option value={ClientStatus.ACTIVE}>Ativos</option>
              <option value={ClientStatus.INACTIVE}>Inativos</option>
              <option value={ClientStatus.ON_HOLD}>Em Espera</option>
              <option value={ClientStatus.ARCHIVED}>Arquivados</option>
            </select>

            <select
              value={filterPersonType}
              onChange={(e) => setFilterPersonType(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todos">Todos os tipos</option>
              <option value={PersonType.PF}>Pessoa Física</option>
              <option value={PersonType.PJ}>Pessoa Jurídica</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          <div className="flex justify-end">
            <Button
              variant="secondary"
              outline
              onClick={handleClearFilters}
              icon={<Filter className="h-4 w-4" />}
              size="sm"
            >
              <span className="hidden sm:inline">Limpar Filtros</span>
              <span className="sm:hidden">Limpar</span>
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
              <p className="text-sm text-muted-foreground">Total</p>
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
                {clients.filter((c) => c.status === ClientStatus.ACTIVE).length}
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
                {
                  clients.filter((c) => c.status === ClientStatus.INACTIVE)
                    .length
                }
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <Calendar className="h-6 w-6 text-yellow-600 dark:text-yellow-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Em Espera</p>
              <p className="text-2xl font-bold text-foreground">
                {
                  clients.filter((c) => c.status === ClientStatus.ON_HOLD)
                    .length
                }
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Clients Table */}
      <Card title="Lista de Clientes">
        {/* Desktop Table */}
        <div className="hidden lg:block">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Cliente
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Documento
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Estabelecimento
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
                {clients.map((client) => (
                  <tr
                    key={client.id}
                    className="border-b border-border hover:bg-muted/50"
                  >
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium text-foreground">
                          {client.name}
                        </p>
                        {client.client_code && (
                          <p className="text-sm text-muted-foreground">
                            Código: {client.client_code}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm font-mono">
                          {formatTaxId(client.tax_id)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {getPersonTypeLabel(client.person_type)}
                        </p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm">{client.establishment_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {client.establishment_code}
                        </p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getClientStatusColor(
                          client.status
                        )}`}
                      >
                        {getClientStatusLabel(client.status)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      {new Date(client.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-center">
                        <ActionDropdown>
                          <ActionDropdown.Item
                            icon={<Eye className="h-4 w-4" />}
                            onClick={() => handleView(client.id)}
                          >
                            Ver Detalhes
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<Edit className="h-4 w-4" />}
                            onClick={() => handleEdit(client.id)}
                          >
                            Editar
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={
                              client.status === ClientStatus.ACTIVE ? (
                                <UserX className="h-4 w-4" />
                              ) : (
                                <UserCheck className="h-4 w-4" />
                              )
                            }
                            onClick={() =>
                              handleToggleStatus(
                                client.id,
                                client.status === ClientStatus.ACTIVE
                                  ? ClientStatus.INACTIVE
                                  : ClientStatus.ACTIVE
                              )
                            }
                            variant={
                              client.status === ClientStatus.ACTIVE
                                ? "warning"
                                : "success"
                            }
                          >
                            {client.status === ClientStatus.ACTIVE
                              ? "Inativar"
                              : "Ativar"}
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<ArrowUpDown className="h-4 w-4" />}
                            onClick={() => handleDelete(client.id)}
                            variant="danger"
                          >
                            Excluir
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
          {clients.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhum cliente encontrado
              </p>
            </div>
          ) : (
            clients.map((client) => (
              <div
                key={client.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {client.name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate font-mono">
                        {formatTaxId(client.tax_id)}
                      </p>
                      {client.client_code && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                          Código: {client.client_code}
                        </p>
                      )}
                    </div>
                    <div className="text-center">
                      <span className={getStatusBadge(client.status)}>
                        {getStatusLabel(client.status)}
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(client.created_at).toLocaleDateString(
                          "pt-BR"
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <ActionDropdown>
                      <ActionDropdown.Item
                        icon={<Eye className="h-4 w-4" />}
                        onClick={() => handleView(client.id)}
                      >
                        Ver Detalhes
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<Edit className="h-4 w-4" />}
                        onClick={() => handleEdit(client.id)}
                      >
                        Editar
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<Trash2 className="h-4 w-4" />}
                        onClick={() => handleDelete(client.id)}
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
          {clients.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhum cliente encontrado
              </p>
            </div>
          ) : (
            clients.map((client, index) => (
              <div
                key={client?.id || index}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900 dark:text-white text-base">
                        {client.name}
                      </h3>
                    </div>
                    {client.client_code && (
                      <p className="text-sm text-gray-600 dark:text-gray-300 font-mono">
                        {client.client_code}
                      </p>
                    )}
                  </div>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getClientStatusColor(
                      client.status
                    )}`}
                  >
                    {getClientStatusLabel(client.status)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                  <div className="flex items-center">
                    <CreditCard className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">
                      {getPersonTypeLabel(client.person_type)}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Building2 className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">
                      {client.establishment_name?.substring(0, 20) ||
                        `Estabelecimento ${client.establishment_id}`}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">
                      {client.created_at
                        ? new Date(client.created_at).toLocaleDateString(
                            "pt-BR"
                          )
                        : "-"}
                    </span>
                  </div>
                  {client.phones?.length > 0 && (
                    <div className="flex items-center">
                      <Phone className="h-4 w-4 mr-2 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-300">
                        {formatPhone(client.phones[0].number)}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
                  <ActionDropdown>
                    <ActionDropdown.Item
                      icon={<Eye className="h-4 w-4" />}
                      onClick={() => handleView(client.id)}
                    >
                      Ver Detalhes
                    </ActionDropdown.Item>

                    <ActionDropdown.Item
                      icon={<Edit className="h-4 w-4" />}
                      onClick={() => handleEdit(client.id)}
                    >
                      Editar
                    </ActionDropdown.Item>

                    <ActionDropdown.Item
                      icon={
                        client.status === ClientStatus.ACTIVE ? (
                          <UserX className="h-4 w-4" />
                        ) : (
                          <UserCheck className="h-4 w-4" />
                        )
                      }
                      onClick={() =>
                        handleToggleStatus(
                          client.id,
                          client.status === ClientStatus.ACTIVE
                            ? ClientStatus.INACTIVE
                            : ClientStatus.ACTIVE
                        )
                      }
                      variant={
                        client.status === ClientStatus.ACTIVE
                          ? "warning"
                          : "success"
                      }
                    >
                      {client.status === ClientStatus.ACTIVE
                        ? "Inativar"
                        : "Ativar"}
                    </ActionDropdown.Item>

                    <ActionDropdown.Item
                      icon={<ArrowUpDown className="h-4 w-4" />}
                      onClick={() => handleDelete(client.id)}
                      variant="danger"
                    >
                      Excluir
                    </ActionDropdown.Item>
                  </ActionDropdown>
                </div>
              </div>
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
              clientes
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
    </div>
  );
};

export default ClientsPage;
