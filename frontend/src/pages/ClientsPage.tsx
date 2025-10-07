import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { clientsService } from "../services/clientsService";
import { PageErrorBoundary } from "../components/error";
import Button from "../components/ui/Button";
import ClientForm from "../components/forms/ClientForm";
import ClientDetails from "../components/views/ClientDetails";
import { notify } from "../utils/notifications.jsx";
import { ClientDetailed, ClientStatus, PersonType } from "../types";
import DataTableTemplate from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { clientsConfig } from "../config/tables/clients.config";
import { Plus } from "lucide-react";

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
  const [currentView, setCurrentView] = useState<string>("list"); // 'list', 'create', 'edit', 'details'
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null);
  const [selectedClient, setSelectedClient] = useState<ClientDetailed | null>(
    null
  );

  // Navigation
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();

  // URL parameters for establishment pre-selection
  const establishmentIdFromUrl = searchParams.get("establishmentId");
  const establishmentCodeFromUrl = searchParams.get("establishmentCode");
  const actionFromUrl = searchParams.get("action");

  // Handler functions - declared before use
  const handleCreate = () => {
    setSelectedClientId(null);
    setSelectedClient(null);
    setCurrentView("create");
  };

  const handleView = (clientId: number) => {
    // Usar URL params em vez de estado interno (Padrão C)
    navigate(`/admin/clientes/${clientId}?tab=informacoes`);
  };

  const handleViewContracts = (clientId: number) => {
    navigate(`/admin/clientes/${clientId}?tab=contratos`);
  };

  const handleViewLives = (clientId: number) => {
    navigate(`/admin/clientes/${clientId}?tab=vidas`);
  };

  const handleEdit = (clientId: number) => {
    const client = clients.find((c) => c.id === clientId);
    setSelectedClient(client || null);
    setSelectedClientId(clientId);
    setCurrentView("edit");
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
        // Reload clients data
        const response = await clientsService.getAll({ page: 1, size: 100 });
        setClients(response?.clients || []);
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
        // Reload clients data
        const response = await clientsService.getAll({ page: 1, size: 100 });
        setClients(response?.clients || []);
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

  const handleBackToList = async () => {
    // Voltar para lista de clientes
    navigate("/admin/clientes", { replace: true });
    setCurrentView("list");
    setSelectedClientId(null);
    setSelectedClient(null);
    // Reload data
    try {
      const response = await clientsService.getAll({ page: 1, size: 100 });
      setClients(response?.clients || []);
    } catch (err: any) {
      console.error("Error reloading clients:", err);
    }
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

  const reloadClients = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await clientsService.getAll({ page: 1, size: 100 });
      setClients(response?.clients || []);
    } catch (err: any) {
      console.error("Error reloading clients:", err);
      setError(`Erro ao carregar clientes: ${err.message}`);
      notify.error("Erro ao carregar clientes");
    } finally {
      setLoading(false);
    }
  };

  // Create dynamic config with proper action handlers
  const dynamicClientsConfig = {
    ...clientsConfig,
    onAdd: handleCreate,
    actions: clientsConfig.actions.map((action) => ({
      ...action,
      onClick: (client: ClientDetailed) => {
        switch (action.id) {
          case "view":
            handleView(client.id);
            break;
          case "view_contracts":
            handleViewContracts(client.id);
            break;
          case "view_lives":
            handleViewLives(client.id);
            break;
          case "edit":
            handleEdit(client.id);
            break;
          case "toggle_status":
            handleToggleStatus(
              client.id,
              client.status === ClientStatus.ACTIVE
                ? ClientStatus.INACTIVE
                : ClientStatus.ACTIVE
            );
            break;
          case "delete":
            handleDelete(client.id);
            break;
          default:
            console.log(`${action.id} action for client`, client);
        }
      },
    })),
  };

  // Initialize data table hook
  const dataTableProps = useDataTable<ClientDetailed>({
    config: dynamicClientsConfig,
    initialData: clients,
  });

  // Load clients data
  useEffect(() => {
    const loadClients = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load all clients for now - DataTableTemplate will handle pagination client-side
        // TODO: Implement server-side pagination if needed for large datasets
        const response = await clientsService.getAll({
          page: 1,
          size: 100, // Maximum allowed by API backend
        });

        const clientsData = response?.clients || [];
        setClients(clientsData);
      } catch (err: any) {
        console.error("Error loading clients:", err);
        setError(`Erro ao carregar clientes: ${err.message}`);
        notify.error("Erro ao carregar clientes");
      } finally {
        setLoading(false);
      }
    };

    if (currentView === "list") {
      loadClients();
    }
  }, [currentView]);

  // Handle URL parameters for direct navigation
  useEffect(() => {
    if (id) {
      console.log("🔍 ID do cliente detectado na URL:", id);
      setSelectedClientId(parseInt(id));
      setCurrentView("details");
    }
  }, [id]);

  // Detect establishment pre-selection from URL
  useEffect(() => {
    if (establishmentIdFromUrl && actionFromUrl === "create") {
      console.log("🏥 Estabelecimento pré-selecionado na URL:", {
        establishmentId: establishmentIdFromUrl,
        establishmentCode: establishmentCodeFromUrl,
      });
      setCurrentView("create");
    }
  }, [establishmentIdFromUrl, establishmentCodeFromUrl, actionFromUrl]);

  // Load selected client when selectedClientId changes
  useEffect(() => {
    const loadSelectedClient = async () => {
      if (selectedClientId && currentView === "details") {
        try {
          console.log("📋 Carregando cliente selecionado:", selectedClientId);
          const client = await clientsService.getById(selectedClientId);
          setSelectedClient(client);
          console.log("✅ Cliente carregado:", client.name);
        } catch (error) {
          console.error("❌ Erro ao carregar cliente:", error);
          setError("Erro ao carregar detalhes do cliente");
          // Fallback to list view
          setCurrentView("list");
          setSelectedClientId(null);
        }
      }
    };

    loadSelectedClient();
  }, [selectedClientId, currentView]);

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    return (
      <ClientForm
        initialData={selectedClient || undefined}
        onCancel={handleBackToList}
        onSave={handleBackToList} // Será chamado após sucesso
        mode={currentView as "create" | "edit"}
        establishmentId={
          establishmentIdFromUrl ? parseInt(establishmentIdFromUrl) : undefined
        }
        establishmentCode={establishmentCodeFromUrl || undefined}
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
          <Button onClick={reloadClients}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DataTableTemplate<ClientDetailed>
        config={dynamicClientsConfig}
        tableData={dataTableProps}
        loading={loading}
      />
    </div>
  );
};

export default ClientsPage;
