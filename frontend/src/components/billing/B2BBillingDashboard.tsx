import React, { useState, useEffect } from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Alert } from "../ui/Alert";
import { notify } from "../../utils/notifications";
import {
  DollarSign,
  Building2,
  FileText,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Calendar,
  CreditCard,
  PieChart,
  BarChart3,
  RefreshCw,
  Download,
  Plus,
} from "lucide-react";
import { B2BBillingService } from "../../services/b2bBillingService";
import CompanyBillingCard from "./CompanyBillingCard";
import B2BInvoicesList from "./B2BInvoicesList";
import type {
  B2BDashboardProps,
  B2BDashboardData,
  ProTeamCareInvoice,
} from "../../types/b2b-billing.types";

const B2BBillingDashboard: React.FC<B2BDashboardProps> = ({
  refreshInterval = 300000, // 5 minutos
  onCompanyClick,
  onInvoiceClick,
}) => {
  const [dashboardData, setDashboardData] = useState<B2BDashboardData | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "companies" | "invoices" | "plans"
  >("overview");
  const [selectedInvoice, setSelectedInvoice] =
    useState<ProTeamCareInvoice | null>(null);

  useEffect(() => {
    loadDashboardData();

    // Auto refresh
    if (refreshInterval > 0) {
      const interval = setInterval(loadDashboardData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      const data = await B2BBillingService.getDashboardData();
      setDashboardData(data);
      setLastUpdated(new Date());
    } catch (err: any) {
      notify.error("Erro ao carregar dados do dashboard: " + err.message);
      console.error("Erro no dashboard B2B:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkGeneration = async () => {
    const currentDate = new Date();
    const month = currentDate.getMonth() + 1;
    const year = currentDate.getFullYear();

    try {
      setLoading(true);
      const result = await B2BBillingService.bulkGenerateInvoices({
        target_month: month,
        target_year: year,
      });

      if (result.success) {
        notify.success(
          `${result.invoices_created} faturas geradas com sucesso!`
        );
        await loadDashboardData();
      } else {
        notify.warning(
          `Geração concluída com problemas: ${result.errors.join(", ")}`
        );
      }
    } catch (err: any) {
      notify.error("Erro na geração em lote: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getMetricsCards = () => {
    if (!dashboardData) return null;

    const { metrics } = dashboardData;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card
          title="Empresas Clientes"
          actions={<Building2 className="h-4 w-4 text-muted-foreground" />}
        >
          <div className="text-2xl font-bold">{metrics.total_companies}</div>
          <p className="text-xs text-muted-foreground">
            {metrics.active_subscriptions} assinaturas ativas
          </p>
        </Card>

        <Card
          title="Receita Mensal"
          actions={<DollarSign className="h-4 w-4 text-muted-foreground" />}
        >
          <div className="text-2xl font-bold">
            {B2BBillingService.formatCurrency(metrics.monthly_revenue)}
          </div>
          <p className="text-xs text-muted-foreground">
            Receita recorrente mensal
          </p>
        </Card>

        <Card
          title="Faturas Pendentes"
          actions={<FileText className="h-4 w-4 text-muted-foreground" />}
        >
          <div className="text-2xl font-bold text-yellow-600">
            {metrics.pending_invoices}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.overdue_invoices > 0 && (
              <span className="text-red-600">
                {metrics.overdue_invoices} vencidas
              </span>
            )}
          </p>
        </Card>

        <Card
          title="Recebido este Mês"
          actions={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
        >
          <div className="text-2xl font-bold text-green-600">
            {B2BBillingService.formatCurrency(metrics.total_revenue_this_month)}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.paid_invoices_this_month} faturas pagas
          </p>
        </Card>
      </div>
    );
  };

  const getOverviewContent = () => {
    if (!dashboardData) return null;

    return (
      <div className="space-y-6">
        {/* Métricas principais */}
        {getMetricsCards()}

        {/* Alertas e ações */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Alertas */}
          <Card
            title={
              <>
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                Alertas e Ações
              </>
            }
          >
            <div className="space-y-4">
              {dashboardData.metrics.overdue_invoices > 0 && (
                <Alert type="error">
                  <strong>
                    {dashboardData.metrics.overdue_invoices} faturas vencidas
                  </strong>{" "}
                  requerem atenção
                </Alert>
              )}

              <div className="space-y-3">
                <Button
                  onClick={handleBulkGeneration}
                  disabled={loading}
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Gerar Faturas do Mês
                </Button>
                <Button
                  variant="outline"
                  onClick={loadDashboardData}
                  disabled={loading}
                  className="w-full"
                >
                  <RefreshCw
                    className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
                  />
                  Atualizar Dados
                </Button>
              </div>
            </div>
          </Card>

          {/* Distribuição de planos */}
          <Card
            title={
              <>
                <PieChart className="h-5 w-5 text-blue-600" />
                Distribuição de Planos
              </>
            }
          >
            <div className="space-y-3">
              {Object.entries(dashboardData.plan_distribution).map(
                ([plan, count]) => (
                  <div key={plan} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{plan}</span>
                    <Badge variant="outline">{count} empresas</Badge>
                  </div>
                )
              )}
              {Object.keys(dashboardData.plan_distribution).length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  Nenhum plano ativo encontrado
                </p>
              )}
            </div>
          </Card>
        </div>

        {/* Pagamentos recentes */}
        <Card
          title={
            <>
              <CheckCircle className="h-5 w-5 text-green-600" />
              Pagamentos Recentes
            </>
          }
        >
          {dashboardData.recent_payments.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">
              Nenhum pagamento recente
            </p>
          ) : (
            <div className="space-y-3">
              {dashboardData.recent_payments.slice(0, 5).map((invoice) => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <div className="font-medium">{invoice.invoice_number}</div>
                    <div className="text-sm text-gray-600">
                      Pago em:{" "}
                      {invoice.paid_at
                        ? B2BBillingService.formatDate(invoice.paid_at)
                        : "N/A"}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-green-600">
                      {B2BBillingService.formatCurrency(invoice.amount)}
                    </div>
                    <Badge className="text-xs">
                      {B2BBillingService.getStatusLabel(invoice.payment_method)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    );
  };

  const getCompaniesContent = () => {
    if (!dashboardData) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">
            Status de Cobrança por Empresa
          </h3>
          <Badge variant="outline">
            {dashboardData.companies_status.length} empresas
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {dashboardData.companies_status.map((companyStatus) => (
            <CompanyBillingCard
              key={companyStatus.company_id}
              company={{
                id: companyStatus.company_id,
                name: companyStatus.company_name,
              }}
              onCreateSubscription={onCompanyClick}
              onManageSubscription={(subscription) =>
                onCompanyClick?.(subscription.company_id)
              }
              onCreateInvoice={onCompanyClick}
            />
          ))}
        </div>

        {dashboardData.companies_status.length === 0 && (
          <Card>
            <div className="text-center py-8">
              <Building2 className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p className="text-gray-500">Nenhuma empresa encontrada</p>
            </div>
          </Card>
        )}
      </div>
    );
  };

  const getInvoicesContent = () => {
    return (
      <div className="space-y-6">
        <B2BInvoicesList
          limit={100}
          onInvoiceClick={(invoice) => {
            setSelectedInvoice(invoice);
            onInvoiceClick?.(invoice);
          }}
          onPaymentConfirm={(invoice) => {
            // Implementar confirmação de pagamento
            console.log("Confirmar pagamento:", invoice);
          }}
        />
      </div>
    );
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Faturamento Pro Team Care
          </h1>
          <p className="text-gray-600">
            Gerencie a cobrança das empresas clientes
            {lastUpdated && (
              <span className="ml-2 text-sm">
                • Atualizado em{" "}
                {B2BBillingService.formatDateTime(lastUpdated.toISOString())}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadDashboardData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "overview", label: "Visão Geral", icon: BarChart3 },
            { id: "companies", label: "Empresas", icon: Building2 },
            { id: "invoices", label: "Faturas", icon: FileText },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="min-h-96">
        {activeTab === "overview" && getOverviewContent()}
        {activeTab === "companies" && getCompaniesContent()}
        {activeTab === "invoices" && getInvoicesContent()}
      </div>
    </div>
  );
};

export default B2BBillingDashboard;
