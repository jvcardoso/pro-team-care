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
        (sum, c) => sum + (Number(c.lives_contracted) || 0),
        0
      );
      const monthlyRevenue = contractsList.reduce((sum, c) => {
        const value = Number(c.monthly_value);
        return sum + (isNaN(value) ? 0 : value);
      }, 0);

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <BarChart3 className="w-6 h-6 mr-2" />
            Dashboard Executivo - Contratos Home Care
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
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
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Contratos
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalContracts}
                </p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 dark:text-green-400 mr-1" />
                  <span className="text-sm text-green-600 dark:text-green-400">
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
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Contratos Ativos
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.activeContracts}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {metrics.totalContracts > 0
                    ? (
                        (metrics.activeContracts / metrics.totalContracts) *
                        100
                      ).toFixed(1)
                    : "0.0"}
                  % do total
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Vidas Contratadas
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalLives}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Média:{" "}
                  {metrics.totalContracts > 0
                    ? (metrics.totalLives / metrics.totalContracts).toFixed(1)
                    : "0.0"}{" "}
                  por contrato
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <DollarSign className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Receita Mensal
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(metrics.monthlyRevenue)}
                </p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 dark:text-green-400 mr-1" />
                  <span className="text-sm text-green-600 dark:text-green-400">
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
          <Card className="border-yellow-200 dark:border-yellow-900/50 bg-yellow-50 dark:bg-yellow-900/20">
            <div className="p-4">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                    Contratos Expirando
                  </p>
                  <p className="text-lg font-bold text-yellow-900 dark:text-yellow-200">
                    {metrics.expiringContracts} contratos
                  </p>
                  <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
                    Nos próximos 30 dias
                  </p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="border-green-200 dark:border-green-900/50 bg-green-50 dark:bg-green-900/20">
            <div className="p-4">
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-500 mr-2" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">
                    Novos Contratos
                  </p>
                  <p className="text-lg font-bold text-green-900 dark:text-green-200">
                    {metrics.newContractsThisMonth}
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-400 mt-1">
                    Este mês
                  </p>
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
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
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
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-bg-card)",
                    borderColor: "var(--color-border)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Contract Types Distribution */}
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Distribuição por Tipo
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--color-border)"
                />
                <XAxis dataKey="name" stroke="var(--color-text-secondary)" />
                <YAxis stroke="var(--color-text-secondary)" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-bg-card)",
                    borderColor: "var(--color-border)",
                  }}
                />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Revenue Trend */}
        <Card className="lg:col-span-2">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Evolução da Receita Mensal
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="var(--color-border)"
                />
                <XAxis dataKey="name" stroke="var(--color-text-secondary)" />
                <YAxis
                  tickFormatter={(value) => `R$ ${(value / 1000).toFixed(0)}k`}
                  stroke="var(--color-text-secondary)"
                />
                <Tooltip
                  formatter={(value) => [
                    formatCurrency(value as number),
                    "Receita",
                  ]}
                  contentStyle={{
                    backgroundColor: "var(--color-bg-card)",
                    borderColor: "var(--color-border)",
                  }}
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
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            Atividade Recente
          </h3>
          <div className="space-y-4">
            {contracts.slice(0, 5).map((contract) => (
              <div
                key={contract.id}
                className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0"
              >
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full mr-3"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Contrato #{contract.contract_number}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {getContractTypeLabel(contract.contract_type)} •{" "}
                      {contract.lives_contracted} vidas
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(contract.monthly_value || 0)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
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
