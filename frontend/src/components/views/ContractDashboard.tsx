import React, { useState, useEffect } from "react";
import { contractsService, Contract } from "../../services/contractsService";
import { medicalAuthorizationsService } from "../../services/medicalAuthorizationsService";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { notify } from "../../utils/notifications.jsx";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  Calendar,
  DollarSign,
  Activity,
  BarChart3,
  PieChart as PieChartIcon,
} from "lucide-react";

interface DashboardMetrics {
  totalContracts: number;
  activeContracts: number;
  totalLives: number;
  monthlyRevenue: number;
  expiringContracts: number;
  newContractsThisMonth: number;
  contractGrowth: number;
  revenueGrowth: number;
}

interface ChartData {
  name: string;
  value: number;
  contracts?: number;
  revenue?: number;
}

const ContractDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    totalContracts: 0,
    activeContracts: 0,
    totalLives: 0,
    monthlyRevenue: 0,
    expiringContracts: 0,
    newContractsThisMonth: 0,
    contractGrowth: 0,
    revenueGrowth: 0,
  });
  const [loading, setLoading] = useState(true);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [statusData, setStatusData] = useState<ChartData[]>([]);
  const [revenueData, setRevenueData] = useState<ChartData[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load contracts data
      const contractsResponse = await contractsService.listContracts({
        size: 100,
      });
      const contractsList = contractsResponse.contracts;
      setContracts(contractsList);

      // Calculate metrics
      const activeContracts = contractsList.filter(
        (c) => c.status === "active"
      );
      const totalLives = contractsList.reduce(
        (sum, c) => sum + c.lives_contracted,
        0
      );
      const monthlyRevenue = contractsList.reduce(
        (sum, c) => sum + (c.monthly_value || 0),
        0
      );

      // Calculate expiring contracts (next 30 days)
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

      const expiringContracts = contractsList.filter((c) => {
        if (!c.end_date) return false;
        const endDate = new Date(c.end_date);
        return endDate <= thirtyDaysFromNow && endDate >= new Date();
      }).length;

      // Calculate new contracts this month
      const thisMonth = new Date();
      thisMonth.setDate(1);
      const newContractsThisMonth = contractsList.filter((c) => {
        const createdDate = new Date(c.created_at);
        return createdDate >= thisMonth;
      }).length;

      // Mock growth data (in real app, compare with previous period)
      const contractGrowth = 12.5;
      const revenueGrowth = 8.3;

      setMetrics({
        totalContracts: contractsList.length,
        activeContracts: activeContracts.length,
        totalLives,
        monthlyRevenue,
        expiringContracts,
        newContractsThisMonth,
        contractGrowth,
        revenueGrowth,
      });

      // Prepare chart data
      prepareChartData(contractsList);
    } catch (error) {
      console.error("Erro ao carregar dados do dashboard:", error);
      notify.error("Erro ao carregar dados do dashboard");
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = (contractsList: Contract[]) => {
    // Status distribution
    const statusCounts = contractsList.reduce((acc, contract) => {
      acc[contract.status] = (acc[contract.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const statusChartData = Object.entries(statusCounts).map(
      ([status, count]) => ({
        name: getStatusLabel(status),
        value: count,
      })
    );
    setStatusData(statusChartData);

    // Contract type distribution
    const typeCounts = contractsList.reduce((acc, contract) => {
      acc[contract.contract_type] = (acc[contract.contract_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const typeChartData = Object.entries(typeCounts).map(([type, count]) => ({
      name: getContractTypeLabel(type),
      value: count,
    }));
    setChartData(typeChartData);

    // Revenue by month (mock data for last 6 months)
    const revenueChartData = [
      { name: "Jan", revenue: 45000 },
      { name: "Fev", revenue: 52000 },
      { name: "Mar", revenue: 48000 },
      { name: "Abr", revenue: 61000 },
      { name: "Mai", revenue: 55000 },
      { name: "Jun", revenue: metrics.monthlyRevenue },
    ];
    setRevenueData(revenueChartData);
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      active: "Ativo",
      inactive: "Inativo",
      suspended: "Suspenso",
      terminated: "Terminado",
      draft: "Rascunho",
    };
    return labels[status as keyof typeof labels] || status;
  };

  const getContractTypeLabel = (type: string) => {
    const labels = {
      INDIVIDUAL: "Individual",
      CORPORATIVO: "Corporativo",
      EMPRESARIAL: "Empresarial",
    };
    return labels[type as keyof typeof labels] || type;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="w-6 h-6 mr-2" />
            Dashboard Executivo - Contratos Home Care
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Visão geral e métricas em tempo real do sistema de contratos
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button onClick={loadDashboardData} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Atualizar Dados
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  Total Contratos
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.totalContracts}
                </p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">
                    +{metrics.contractGrowth}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  Contratos Ativos
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.activeContracts}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {(
                    (metrics.activeContracts / metrics.totalContracts) *
                    100
                  ).toFixed(1)}
                  % do total
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  Vidas Contratadas
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.totalLives}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Média:{" "}
                  {(metrics.totalLives / metrics.totalContracts).toFixed(1)} por
                  contrato
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 rounded-lg">
                <DollarSign className="w-6 h-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  Receita Mensal
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.monthlyRevenue)}
                </p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">
                    +{metrics.revenueGrowth}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Alert Cards */}
      {metrics.expiringContracts > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="border-yellow-200 bg-yellow-50">
            <div className="p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">
                    Contratos Expirando
                  </p>
                  <p className="text-lg font-bold text-yellow-900">
                    {metrics.expiringContracts} contratos
                  </p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Nos próximos 30 dias
                  </p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="border-green-200 bg-green-50">
            <div className="p-4">
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
                <div>
                  <p className="text-sm font-medium text-green-800">
                    Novos Contratos
                  </p>
                  <p className="text-lg font-bold text-green-900">
                    {metrics.newContractsThisMonth}
                  </p>
                  <p className="text-xs text-green-700 mt-1">Este mês</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contract Status Distribution */}
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <PieChartIcon className="w-5 h-5 mr-2" />
              Distribuição por Status
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Contract Types Distribution */}
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Distribuição por Tipo
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Revenue Trend */}
        <Card className="lg:col-span-2">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Evolução da Receita Mensal
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis
                  tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(value) => [
                    formatCurrency(value as number),
                    "Receita",
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            Atividade Recente
          </h3>
          <div className="space-y-4">
            {contracts.slice(0, 5).map((contract) => (
              <div
                key={contract.id}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0"
              >
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Contrato #{contract.contract_number}
                    </p>
                    <p className="text-xs text-gray-500">
                      {getContractTypeLabel(contract.contract_type)} •{" "}
                      {contract.lives_contracted} vidas
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {formatCurrency(contract.monthly_value || 0)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(contract.created_at).toLocaleDateString("pt-BR")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ContractDashboard;
