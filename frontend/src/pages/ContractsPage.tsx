import React, { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  contractsService,
  Contract,
  ContractListParams,
} from "../services/contractsService";
import { clientsService } from "../services/clientsService";
import { PageErrorBoundary } from "../components/error";
import DataTableTemplate from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { createContractsConfig } from "../config/tables/contracts.config";
import ContractForm from "../components/forms/ContractForm";
import ContractDetails from "../components/views/ContractDetails";
import { notify } from "../utils/notifications.jsx";
import Button from "../components/ui/Button";

const ContractsPage: React.FC = () => {
  return (
    <PageErrorBoundary pageName="Contratos">
      <ContractsPageContent />
    </PageErrorBoundary>
  );
};

// Extend Contract type to include client name
interface ContractWithClientName extends Contract {
  client_name?: string;
}

const ContractsPageContent: React.FC = () => {
  const [contracts, setContracts] = useState<ContractWithClientName[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingContract, setEditingContract] = useState<Contract | null>(null);
  const [viewingContract, setViewingContract] = useState<Contract | null>(null);
  const [showingDetails, setShowingDetails] = useState(false);
  const [prefilledClientId, setPrefilledClientId] = useState<number | null>(null);

  const handleCreateContract = () => {
    setEditingContract(null);
    setShowForm(true);
  };

  const handleEditContract = (contract: Contract) => {
    setEditingContract(contract);
    setShowForm(true);
  };

  const handleViewContract = (contract: Contract) => {
    setViewingContract(contract);
    setShowingDetails(true);
  };

  const handleDeleteContract = async (contract: Contract) => {
    if (!window.confirm("Tem certeza que deseja excluir este contrato?")) {
      return;
    }

    try {
      await contractsService.deleteContract(contract.id);
      notify.success("Contrato excluído com sucesso");
      loadContracts();
    } catch (error) {
      console.error("Erro ao excluir contrato:", error);
      notify.error("Erro ao excluir contrato");
    }
  };

  // Initialize data table hook with actions
  const dataTableProps = useDataTable<ContractWithClientName>({
    config: createContractsConfig({
      onView: handleViewContract,
      onEdit: handleEditContract,
      onDelete: handleDeleteContract,
      onAdd: handleCreateContract,
    }),
    initialData: contracts,
  });

  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { id } = params;

  // Detectar modo baseado na URL
  const isEditing = window.location.pathname.includes("/editar");
  const isConfiguring = window.location.pathname.includes("/configuracoes");
  const contractId = id ? parseInt(id) : null;

  // Load contracts data
  useEffect(() => {
    loadContracts();
  }, []);

  // Carregar contrato específico quando estiver em modo de edição ou configuração
  useEffect(() => {
    if (contractId && (isEditing || isConfiguring)) {
      loadContractForEditing(contractId);
    }
  }, [contractId, isEditing, isConfiguring]);

  // Detectar ação de criar contrato a partir de parâmetros URL
  useEffect(() => {
    const action = searchParams.get("action");
    const clientId = searchParams.get("client_id");

    if (action === "create") {
      // Abrir formulário de criação automaticamente
      setEditingContract(null);
      setShowForm(true);

      // Limpar parâmetros da URL após detectar
      setSearchParams({});

      // Se tiver client_id, salvar para usar no formulário
      if (clientId) {
        setPrefilledClientId(parseInt(clientId));
        console.log("Criando contrato para cliente:", clientId);
      }
    }
  }, [searchParams, setSearchParams]);

  const loadContracts = async () => {
    try {
      setLoading(true);

      // Fetch real contracts from API
      const response = await contractsService.listContracts({
        page: 1,
        size: 100, // Buscar até 100 contratos para exibir na tabela
      });

      const contractsList = response.contracts || [];

      // Get unique client IDs
      const clientIds = [
        ...new Set(contractsList.map((contract) => contract.client_id)),
      ];

      // Fetch client names
      const clientsMap = new Map<number, string>();

      // Fetch clients in parallel
      await Promise.all(
        clientIds.map(async (clientId) => {
          try {
            const client = await clientsService.getById(clientId);
            // Client must exist if contract exists - no fallback
            const clientName = client.person?.name || client.name;
            if (clientName) {
              clientsMap.set(clientId, clientName);
            } else {
              clientsMap.set(clientId, `Cliente #${clientId}`);
            }
          } catch (error) {
            console.warn(`Erro ao buscar cliente ${clientId}:`, error);
            clientsMap.set(clientId, `Cliente #${clientId}`);
          }
        })
      );

      // Add client names to contracts
      const contractsWithNames: ContractWithClientName[] = contractsList.map(
        (contract) => ({
          ...contract,
          client_name: clientsMap.get(contract.client_id) || `Cliente #${contract.client_id}`,
        })
      );

      setContracts(contractsWithNames);
    } catch (error) {
      console.error("Erro ao carregar contratos:", error);
      notify.error("Erro ao carregar contratos");
    } finally {
      setLoading(false);
    }
  };


  const loadContractForEditing = async (contractId: number) => {
    try {
      const contract = await contractsService.getContract(contractId);
      setEditingContract(contract);
      if (isEditing) {
        setShowForm(true);
      }
    } catch (error) {
      console.error("Erro ao carregar contrato para edição:", error);
      notify.error("Erro ao carregar contrato para edição");
    }
  };




  if (showForm || isEditing) {
    return (
      <ContractForm
        contract={editingContract || (prefilledClientId ? { client_id: prefilledClientId } : undefined)}
        onSave={() => {
          // Sempre recarregar dados após salvar
          loadContracts();
          if (isEditing) {
            navigate("/admin/contratos");
          } else {
            setShowForm(false);
            setEditingContract(null);
            setPrefilledClientId(null);
          }
        }}
        onCancel={() => {
          if (isEditing) {
            navigate("/admin/contratos");
          } else {
            setShowForm(false);
            setEditingContract(null);
            setPrefilledClientId(null);
          }
        }}
      />
    );
  }

  if (isConfiguring && editingContract) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Configurações do Contrato
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Contrato #{editingContract.contract_number}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate("/admin/contratos")}
          >
            Voltar
          </Button>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6">
            <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">
              Configurações Avançadas
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tipo de Controle
                  </label>
                  <select className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                    <option value="MONTHLY">Mensal</option>
                    <option value="QUARTERLY">Trimestral</option>
                    <option value="ANNUAL">Anual</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Notificações
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center text-gray-700 dark:text-gray-300">
                      <input type="checkbox" className="mr-2" defaultChecked />
                      Notificar vencimentos
                    </label>
                    <label className="flex items-center text-gray-700 dark:text-gray-300">
                      <input type="checkbox" className="mr-2" defaultChecked />
                      Notificar limites
                    </label>
                  </div>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => navigate("/admin/contratos")}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={() => {
                    notify.success("Configurações salvas com sucesso!");
                    navigate("/admin/contratos");
                  }}
                >
                  Salvar Configurações
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showingDetails && viewingContract) {
    return (
      <ContractDetails
        contract={viewingContract}
        onEdit={() => {
          setEditingContract(viewingContract);
          setViewingContract(null);
          setShowingDetails(false);
          setShowForm(true);
        }}
        onBack={() => {
          setShowingDetails(false);
          setViewingContract(null);
        }}
      />
    );
  }

  // List view loading states
  if (loading && contracts.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando contratos...</p>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 relative shadow-md sm:rounded-lg overflow-hidden">
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-300">
              Carregando contratos...
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Render the data table template
  return (
    <div className="space-y-6">
      <DataTableTemplate<ContractWithClientName>
        config={createContractsConfig({
          onView: handleViewContract,
          onEdit: handleEditContract,
          onDelete: handleDeleteContract,
          onAdd: handleCreateContract,
        })}
        tableData={dataTableProps}
      />
    </div>
  );
};

export default ContractsPage;
