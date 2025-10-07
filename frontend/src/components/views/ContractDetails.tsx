import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Card from "../ui/Card";
import Button from "../ui/Button";
import EntityDetailsLayout from "./EntityDetailsLayout";
import { PageErrorBoundary } from "../error";
import { contractsService } from "../../services/contractsService";
import { notify } from "../../utils/notifications.jsx";
import { formatCurrencyDisplay } from "../../utils/formatters";
import {
  FileText,
  Users,
  Calendar,
  DollarSign,
  Building2,
  Edit,
  ArrowLeft,
  User,
  Heart,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  CreditCard,
} from "lucide-react";
import ContractFinancialSummary from "../billing/ContractFinancialSummary";
import RecentInvoicesTable from "../billing/RecentInvoicesTable";

interface ContractDetailsProps {
  contract?: any; // Contract passed as prop
  onEdit?: () => void;
  onBack?: () => void;
}

const ContractDetails: React.FC<ContractDetailsProps> = ({
  contract: contractProp,
  onEdit,
  onBack,
}) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contract, setContract] = useState<any>(contractProp || null);
  const [loading, setLoading] = useState(!contractProp);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("informacoes");

  useEffect(() => {
    if (contractProp) {
      // Contract passed as prop, use it directly
      setContract(contractProp);
      setLoading(false);
    } else if (id) {
      // No contract prop, load from API using URL params
      loadContract();
    }
  }, [id, contractProp]);

  const loadContract = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await contractsService.getById(parseInt(id!));
      setContract(data);
    } catch (err: any) {
      console.error("Erro ao carregar contrato:", err);
      setError("Erro ao carregar detalhes do contrato");
    } finally {
      setLoading(false);
    }
  };

  // Reutilizar função centralizada de formatação
  const formatCurrency = (value: number) => formatCurrencyDisplay(value);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: {
        color: "bg-green-100 text-green-800",
        icon: CheckCircle,
        label: "Ativo",
      },
      suspended: {
        color: "bg-yellow-100 text-yellow-800",
        icon: AlertTriangle,
        label: "Suspenso",
      },
      cancelled: {
        color: "bg-red-100 text-red-800",
        icon: XCircle,
        label: "Cancelado",
      },
      expired: {
        color: "bg-gray-100 text-gray-800",
        icon: Clock,
        label: "Expirado",
      },
    };

    const config =
      statusConfig[status as keyof typeof statusConfig] || statusConfig.active;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${config.color}`}
      >
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </span>
    );
  };

  const getContractTypeLabel = (type: string) => {
    const labels = {
      INDIVIDUAL: "Individual",
      CORPORATIVO: "Corporativo",
      EMPRESARIAL: "Empresarial",
    };
    return labels[type as keyof typeof labels] || type;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Carregando contrato...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadContract}>Tentar Novamente</Button>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Contrato não encontrado</p>
        <Button onClick={onBack} className="mt-4">
          Voltar
        </Button>
      </div>
    );
  }

  const metrics = [
    {
      icon: <Users className="h-5 w-5 text-green-600" />,
      label: "Vidas",
      value: `${contract.lives_active || 0}/${contract.lives_contracted}`,
    },
    {
      icon: <DollarSign className="h-5 w-5 text-purple-600" />,
      label: "Valor Mensal",
      value: formatCurrency(contract.monthly_value),
    },
    {
      icon: <Calendar className="h-5 w-5 text-orange-600" />,
      label: "Vigência",
      value: contract.end_date
        ? `${formatDate(contract.start_date)} - ${formatDate(
            contract.end_date
          )}`
        : formatDate(contract.start_date),
    },
  ];

  const tabs = [
    { key: "informacoes", label: "Informações", shortLabel: "Info" },
    { key: "financeiro", label: "Financeiro", shortLabel: "💰" },
    { key: "vidas", label: "Vidas" },
    { key: "servicos", label: "Serviços" },
    { key: "historico", label: "Histórico", shortLabel: "Hist." },
  ];

  const actionButtons = onEdit
    ? [
        {
          label: "Editar Contrato",
          onClick: onEdit,
          icon: <Edit className="h-4 w-4" />,
        },
      ]
    : [];

  const renderTabContent = () => {
    switch (activeTab) {
      case "informacoes":
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Informações Básicas */}
            <Card
              title="Informações Básicas"
              icon={<FileText className="h-5 w-5" />}
            >
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Número do Contrato
                  </label>
                  <p className="text-foreground font-mono">
                    {contract.contract_number}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Tipo de Contrato
                  </label>
                  <p className="text-foreground">
                    {getContractTypeLabel(contract.contract_type)}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Nome do Plano
                  </label>
                  <p className="text-foreground">{contract.plan_name}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Cliente
                  </label>
                  <p className="text-foreground">{contract.client_name}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Estabelecimento
                  </label>
                  <p className="text-foreground">
                    {contract.establishment_name}
                  </p>
                </div>
              </div>
            </Card>

            {/* Configurações de Vidas */}
            <Card
              title="Configurações de Vidas"
              icon={<Users className="h-5 w-5" />}
            >
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Vidas Contratadas
                  </label>
                  <p className="text-foreground font-semibold">
                    {contract.lives_contracted}
                  </p>
                </div>

                {contract.lives_minimum && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">
                      Vidas Mínimas
                    </label>
                    <p className="text-foreground">{contract.lives_minimum}</p>
                  </div>
                )}

                {contract.lives_maximum && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">
                      Vidas Máximas
                    </label>
                    <p className="text-foreground">{contract.lives_maximum}</p>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Permite Substituição
                  </label>
                  <p className="text-foreground">
                    {contract.allows_substitution ? "Sim" : "Não"}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Período de Controle
                  </label>
                  <p className="text-foreground">
                    {contract.control_period || "MENSAL"}
                  </p>
                </div>
              </div>
            </Card>

            {/* Valores Financeiros */}
            <Card
              title="Valores Financeiros"
              icon={<DollarSign className="h-5 w-5" />}
            >
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Valor Mensal
                  </label>
                  <p className="text-foreground text-xl font-bold">
                    {formatCurrency(contract.monthly_value)}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground">
                    Valor Anual Estimado
                  </label>
                  <p className="text-foreground">
                    {formatCurrency(contract.monthly_value * 12)}
                  </p>
                </div>
              </div>
            </Card>

            {/* Endereços de Serviço */}
            <Card
              title="Endereços de Serviço"
              icon={<Building2 className="h-5 w-5" />}
            >
              <div className="space-y-3">
                {contract.service_addresses &&
                contract.service_addresses.length > 0 ? (
                  contract.service_addresses.map(
                    (address: any, index: number) => (
                      <div
                        key={index}
                        className="border border-border rounded-lg p-3"
                      >
                        <p className="font-medium text-foreground">
                          {address.street}
                          {address.number && `, ${address.number}`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {address.neighborhood}, {address.city} -{" "}
                          {address.state}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          CEP: {address.zip_code}
                        </p>
                      </div>
                    )
                  )
                ) : (
                  <p className="text-muted-foreground text-sm">
                    Nenhum endereço de serviço cadastrado
                  </p>
                )}
              </div>
            </Card>
          </div>
        );

      case "financeiro":
        return (
          <div className="space-y-6">
            {/* Financial Summary */}
            <ContractFinancialSummary contract={contract} />

            {/* Recent Invoices */}
            <RecentInvoicesTable contractId={contract.id} limit={10} />
          </div>
        );

      case "vidas":
        return (
          <div className="text-center py-12">
            <Heart className="h-12 w-12 text-blue-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Gestão de Vidas
            </h3>
            <p className="text-muted-foreground mb-6">
              Gerencie as vidas contratadas, adicione novas pessoas ou faça
              substituições
            </p>
            <Button
              onClick={() => navigate(`/admin/contratos/${id}/vidas`)}
              className="flex items-center"
            >
              <Users className="w-4 h-4 mr-2" />
              Gerenciar Vidas
            </Button>
          </div>
        );

      case "servicos":
        return (
          <div className="text-center py-12">
            <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Serviços Contratados
            </h3>
            <p className="text-muted-foreground">
              Em breve: Visualize os serviços contratados
            </p>
          </div>
        );

      case "historico":
        return (
          <div className="text-center py-12">
            <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Histórico do Contrato
            </h3>
            <p className="text-muted-foreground">
              Em breve: Visualize o histórico de alterações
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <PageErrorBoundary pageName="ContractDetails">
      <EntityDetailsLayout
        title={`Contrato ${contract.contract_number}`}
        subtitle={`${contract.plan_name} - ${contract.client_name}`}
        icon={<FileText className="h-6 w-6" />}
        statusBadge={getStatusBadge(contract.status)}
        backButton={onBack ? { onClick: onBack } : undefined}
        actionButtons={actionButtons}
        metrics={metrics}
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        loading={loading}
        error={error}
        onRetry={loadContract}
      >
        {renderTabContent()}
      </EntityDetailsLayout>
    </PageErrorBoundary>
  );
};

export default ContractDetails;
