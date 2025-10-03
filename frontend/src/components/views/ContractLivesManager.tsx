import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { contractsService, Contract } from "../../services/contractsService";
import DataTableTemplate from "../shared/DataTable/DataTableTemplate";
import { useDataTable } from "../../hooks/useDataTable";
import { createContractLivesConfig, ContractLife } from "../../config/tables/contractLives.config";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { notify } from "../../utils/notifications.jsx";
import {
  Users,
  ArrowRightLeft,
  UserPlus,
  UserMinus,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Calendar,
  FileText,
  ArrowLeft,
  Save,
  Edit,
  Trash2,
  History,
  X,
} from "lucide-react";

// ContractLife interface is now imported from config

interface LifeFormData {
  person_id: number;
  person_name: string;
  start_date: string;
  end_date?: string;
  notes?: string;
}

const ContractLivesManager: React.FC = () => {
  const { id: contractId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [contract, setContract] = useState<Contract | null>(null);
  const [lives, setLives] = useState<ContractLife[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showSubstituteForm, setShowSubstituteForm] = useState(false);
  const [selectedLife, setSelectedLife] = useState<ContractLife | null>(null);
  const [showTimeline, setShowTimeline] = useState(false);
  const [timelineLife, setTimelineLife] = useState<ContractLife | null>(null);
  const [formData, setFormData] = useState<LifeFormData>({
    person_id: 0,
    person_name: "",
    start_date: new Date().toISOString().split("T")[0],
    end_date: "",
    notes: "",
  });

  // Handler functions defined before dataTable initialization
  const handleAddLife = () => {
    setFormData({
      person_id: 0,
      person_name: "",
      start_date: new Date().toISOString().split("T")[0],
      end_date: "",
      notes: "",
    });
    setShowAddForm(true);
  };

  const handleSubstituteLife = (life: ContractLife) => {
    // Validate substitution
    const validationError = validateSubstitution(life);
    if (validationError) {
      notify.error(validationError);
      return;
    }

    setSelectedLife(life);
    setFormData({
      person_id: 0,
      person_name: "",
      start_date: new Date().toISOString().split("T")[0],
      end_date: "",
      notes: `Substituição de ${life.person_name}`,
    });
    setShowSubstituteForm(true);
  };

  const handleRemoveLife = async (life: ContractLife) => {
    // Validate removal
    const validationError = validateLifeRemoval(life);
    if (validationError) {
      notify.error(validationError);
      return;
    }

    if (
      !window.confirm(
        `Tem certeza que deseja remover ${life.person_name} do contrato?`
      )
    ) {
      return;
    }

    try {
      await contractsService.removeContractLife(parseInt(contractId!), life.id);
      notify.success(`${life.person_name} removido do contrato`);
      loadContractAndLives(); // Reload the list
    } catch (error) {
      console.error("Erro ao remover vida:", error);
      notify.error("Erro ao remover vida do contrato");
    }
  };

  const handleViewTimeline = (life: ContractLife) => {
    setTimelineLife(life);
    setShowTimeline(true);
  };

  // Initialize data table hook
  const dataTableProps = useDataTable<ContractLife>({
    config: createContractLivesConfig({
      onViewTimeline: handleViewTimeline,
      onSubstitute: handleSubstituteLife,
      onEdit: (life) => {
        // For now, just show substitute form as edit
        handleSubstituteLife(life);
      },
      onDelete: handleRemoveLife,
      onAdd: handleAddLife,
    }),
    initialData: lives,
  });

  useEffect(() => {
    if (contractId) {
      loadContractAndLives();
    } else {
      loadAllContractLives();
    }
  }, [contractId]);

  // Update data table when lives change
  useEffect(() => {
    dataTableProps.callbacks.onDataChange?.(lives);
  }, [lives, dataTableProps.callbacks]);

  const loadContractAndLives = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load contract details
      const contractData = await contractsService.getContract(
        parseInt(contractId!)
      );
      setContract(contractData);

      // Load contract lives from API
      const livesData = await contractsService.listContractLives(
        parseInt(contractId!)
      );
      setLives(livesData);
    } catch (error) {
      console.error("Erro ao carregar contrato e vidas:", error);
      setError("Erro ao carregar dados do contrato");
      notify.error("Erro ao carregar dados do contrato");
    } finally {
      setLoading(false);
    }
  };

  const loadAllContractLives = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all contracts and their lives
      const contractsResponse = await contractsService.listContracts();
      console.log(`📊 Encontrados ${contractsResponse.contracts.length} contratos`);
      const allLives: ContractLife[] = [];

      for (const contractData of contractsResponse.contracts) {
        try {
          const livesData = await contractsService.listContractLives(contractData.id);
          console.log(`📊 Contrato ${contractData.id} (${contractData.contract_number}): ${livesData.length} vidas`);
          // Add contract info to each life
          const livesWithContract = livesData.map(life => ({
            ...life,
            contract_number: contractData.contract_number,
            client_name: contractData.client_name
          }));
          allLives.push(...livesWithContract);
        } catch (error) {
          console.error(`❌ Erro contrato ${contractData.id}:`, error);
        }
      }

      console.log(`📋 Total de vidas carregadas: ${allLives.length}`);
      setLives(allLives);
      setContract(null); // No specific contract selected
    } catch (error) {
      console.error("Erro ao carregar todas as vidas:", error);
      setError("Erro ao carregar vidas dos contratos");
      notify.error("Erro ao carregar vidas dos contratos");
    } finally {
      setLoading(false);
    }
  };


  const validateLifeRemoval = (life: ContractLife): string | null => {
    const activeLives = lives.filter((l) => l.status === "active").length;

    // Check minimum lives limit
    if (contract.lives_minimum && activeLives <= contract.lives_minimum) {
      return `Não é possível remover: mínimo de ${contract.lives_minimum} vidas deve ser mantido`;
    }

    return null;
  };

  const validateSubstitution = (life: ContractLife): string | null => {
    // Check if substitution is allowed for this life
    if (!life.substitution_allowed) {
      return "Esta vida não permite substituição";
    }

    // Check if life is active
    if (life.status !== "active") {
      return "Apenas vidas ativas podem ser substituídas";
    }

    return null;
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (showAddForm) {
        // Validate addition
        const activeLives = lives.filter((l) => l.status === "active").length;
        let validationError: string | null = null;

        // Check maximum lives limit
        if (contract?.lives_maximum && activeLives >= contract.lives_maximum) {
          validationError = `Limite máximo de ${contract.lives_maximum} vidas atingido`;
        }

        // Check if contract allows more lives
        if (contract && activeLives >= contract.lives_contracted) {
          validationError = `Todas as ${contract.lives_contracted} vidas contratadas já estão em uso`;
        }
        if (validationError) {
          notify.error(validationError);
          return;
        }

        // Add new life via API
        await contractsService.addContractLife(parseInt(contractId!), {
          person_name: formData.person_name,
          start_date: formData.start_date,
          end_date: formData.end_date || null,
          notes: formData.notes,
          relationship_type: "FUNCIONARIO",
          allows_substitution: true,
        });

        notify.success(`${formData.person_name} adicionado ao contrato`);
        loadContractAndLives(); // Reload the list
      } else if (showSubstituteForm && selectedLife) {
        // Validate substitution
        const validationError = validateSubstitution(selectedLife);
        if (validationError) {
          notify.error(validationError);
          return;
        }

        // Update life via API (substitute)
        await contractsService.updateContractLife(
          parseInt(contractId!),
          selectedLife.id,
          {
            end_date: formData.start_date, // End current life
            status: "substituted",
            notes: `Substituído por ${formData.person_name} - ${formData.notes}`,
          }
        );

        // Add new life for the substitute
        await contractsService.addContractLife(parseInt(contractId!), {
          person_name: formData.person_name,
          start_date: formData.start_date,
          end_date: formData.end_date || null,
          notes: formData.notes,
          relationship_type: "FUNCIONARIO",
          allows_substitution: true,
        });

        notify.success(
          `${selectedLife.person_name} substituído por ${formData.person_name}`
        );
        loadContractAndLives(); // Reload the list
      }

      setShowAddForm(false);
      setShowSubstituteForm(false);
      setSelectedLife(null);
    } catch (error) {
      console.error("Erro ao salvar vida:", error);
      notify.error("Erro ao salvar vida no contrato");
    }
  };



  const activeLives = lives.filter((l) => l.status === "active").length;
  const totalLives = lives.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {contractId ? "Erro ao carregar contrato" : "Erro ao carregar vidas"}
          </h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <Button onClick={() => navigate(contractId ? "/admin/contratos" : "/admin")}>
            {contractId ? "Voltar para Contratos" : "Voltar ao Dashboard"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center space-x-4">
          <Button
            onClick={() => navigate(contractId ? "/admin/contratos" : "/admin")}
            variant="outline"
            size="sm"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {contractId ? "Voltar para Contratos" : "Voltar ao Dashboard"}
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <Users className="w-6 h-6 mr-2" />
              Gestão de Vidas
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {contract ? (
                <>
                  Contrato #{contract.contract_number} -{" "}
                  {contract.client_id
                    ? `Cliente #${contract.client_id}`
                    : "Cliente não identificado"}
                </>
              ) : (
                "Todas as vidas de todos os contratos"
              )}
            </p>
          </div>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button onClick={handleAddLife} className="flex items-center">
            <UserPlus className="w-4 h-4 mr-2" />
            Adicionar Vida
          </Button>
        </div>
      </div>

       {/* Contract Summary */}
       {contract && (
         <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
           <Card>
             <div className="p-4">
               <div className="flex items-center">
                 <Users className="w-8 h-8 text-blue-500" />
                 <div className="ml-3">
                   <p className="text-sm font-medium text-gray-500">
                     Vidas Ativas
                   </p>
                   <p className="text-2xl font-bold text-gray-900">
                     {activeLives}
                   </p>
                 </div>
               </div>
             </div>
           </Card>
           <Card>
             <div className="p-4">
               <div className="flex items-center">
                 <FileText className="w-8 h-8 text-green-500" />
                 <div className="ml-3">
                   <p className="text-sm font-medium text-gray-500">
                     Total de Vidas
                   </p>
                   <p className="text-2xl font-bold text-gray-900">{totalLives}</p>
                 </div>
               </div>
             </div>
           </Card>
           <Card>
             <div className="p-4">
               <div className="flex items-center">
                 <CheckCircle className="w-8 h-8 text-purple-500" />
                 <div className="ml-3">
                   <p className="text-sm font-medium text-gray-500">
                     Vidas Contratadas
                   </p>
                   <p className="text-2xl font-bold text-gray-900">
                     {contract.lives_contracted}
                   </p>
                 </div>
               </div>
             </div>
           </Card>
           <Card>
             <div className="p-4">
               <div className="flex items-center">
                 <Calendar className="w-8 h-8 text-orange-500" />
                 <div className="ml-3">
                   <p className="text-sm font-medium text-gray-500">
                     Vagas Disponíveis
                   </p>
                   <p className="text-2xl font-bold text-gray-900">
                     {Math.max(0, contract.lives_contracted - activeLives)}
                   </p>
                 </div>
               </div>
             </div>
           </Card>
         </div>
       )}



      {/* Add Life Form */}
      {showAddForm && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <UserPlus className="w-5 h-5 mr-2" />
              Adicionar Nova Vida
            </h3>
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome da Pessoa *
                  </label>
                  <Input
                    value={formData.person_name}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        person_name: e.target.value,
                      }))
                    }
                    placeholder="Digite o nome completo"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Início *
                  </label>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        start_date: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Fim (opcional)
                  </label>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        end_date: e.target.value,
                      }))
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observações
                  </label>
                  <Input
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        notes: e.target.value,
                      }))
                    }
                    placeholder="Observações sobre a inclusão"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddForm(false)}
                >
                  Cancelar
                </Button>
                <Button type="submit">
                  <Save className="w-4 h-4 mr-2" />
                  Adicionar Vida
                </Button>
              </div>
            </form>
          </div>
        </Card>
      )}

      {/* Substitute Life Form */}
      {showSubstituteForm && selectedLife && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <ArrowRightLeft className="w-5 h-5 mr-2" />
              Substituir Vida: {selectedLife.person_name}
            </h3>
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Novo Nome da Pessoa *
                  </label>
                  <Input
                    value={formData.person_name}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        person_name: e.target.value,
                      }))
                    }
                    placeholder="Digite o nome completo da nova pessoa"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Substituição *
                  </label>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        start_date: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Data de Fim (opcional)
                  </label>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        end_date: e.target.value,
                      }))
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observações
                  </label>
                  <Input
                    value={formData.notes}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        notes: e.target.value,
                      }))
                    }
                    placeholder="Motivo da substituição"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowSubstituteForm(false);
                    setSelectedLife(null);
                  }}
                >
                  Cancelar
                </Button>
                <Button type="submit">
                  <Save className="w-4 h-4 mr-2" />
                  Substituir Vida
                </Button>
              </div>
            </form>
          </div>
        </Card>
      )}

      {/* Timeline Modal */}
      {showTimeline && timelineLife && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <History className="w-5 h-5 mr-2" />
                  Histórico: {timelineLife.person_name}
                </h3>
                <Button
                  onClick={() => {
                    setShowTimeline(false);
                    setTimelineLife(null);
                  }}
                  variant="ghost"
                  size="sm"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            <div className="p-6 overflow-y-auto max-h-96">
              <div className="space-y-4">
                {/* Mock timeline events - in real app, this would come from API */}
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      Vida adicionada ao contrato
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(timelineLife.created_at).toLocaleString(
                        "pt-BR"
                      )}
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      Status inicial: Ativo
                    </p>
                  </div>
                </div>

                {timelineLife.updated_at !== timelineLife.created_at && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        Informações atualizadas
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(timelineLife.updated_at).toLocaleString(
                          "pt-BR"
                        )}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">
                        Última modificação dos dados
                      </p>
                    </div>
                  </div>
                )}

                {timelineLife.status === "terminated" &&
                  timelineLife.end_date && (
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          Vida removida do contrato
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(timelineLife.end_date).toLocaleString(
                            "pt-BR"
                          )}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          Status alterado para: Terminado
                        </p>
                      </div>
                    </div>
                  )}
              </div>
            </div>
          </div>
        </div>
      )}

       {/* Lives List */}
       <DataTableTemplate<ContractLife>
         config={createContractLivesConfig({
           onViewTimeline: handleViewTimeline,
           onSubstitute: handleSubstituteLife,
           onEdit: (life) => {
             // For now, just show substitute form as edit
             handleSubstituteLife(life);
           },
           onDelete: handleRemoveLife,
           onAdd: handleAddLife,
         })}
         tableData={dataTableProps}
         loading={loading}
       />
    </div>
  );
};

export default ContractLivesManager;
