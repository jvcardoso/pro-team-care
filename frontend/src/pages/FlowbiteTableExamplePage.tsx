import React, { useState, useEffect } from "react";
import { contractsService, Contract } from "../services/contractsService";
import { clientsService } from "../services/clientsService";
import DataTableTemplate from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { createContractsConfig } from "../config/tables/contracts.config";

// Extend Contract type to include client name
interface ContractWithClientName extends Contract {
  client_name?: string;
}

const FlowbiteTableExamplePage: React.FC = () => {
  const [contracts, setContracts] = useState<ContractWithClientName[]>([]);
  const [loading, setLoading] = useState(true);

  // Initialize data table hook
  const dataTableProps = useDataTable<ContractWithClientName>({
    config: createContractsConfig(),
    initialData: contracts,
  });

  // Load contracts data
  useEffect(() => {
    const loadContracts = async () => {
      try {
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
            const client = await clientsService.getById(clientId);
            // Client must exist if contract exists - no fallback
            const clientName = client.person?.name || client.name;
            if (!clientName) {
              throw new Error(`Cliente ${clientId} não possui nome válido`);
            }
            clientsMap.set(clientId, clientName);
          })
        );

        // Add client names to contracts
        const contractsWithNames: ContractWithClientName[] = contractsList.map(
          (contract) => ({
            ...contract,
            client_name: clientsMap.get(contract.client_id)!,
          })
        );

        setContracts(contractsWithNames);
      } catch (error) {
        console.error("Erro ao carregar contratos:", error);
      } finally {
        setLoading(false);
      }
    };

    loadContracts();
  }, []);

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
        config={createContractsConfig()}
        tableData={dataTableProps}
      />
    </div>
  );
};

export default FlowbiteTableExamplePage;
