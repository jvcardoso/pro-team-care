import React, { useState, useEffect } from "react";
import { contractsService, Contract } from "../services/contractsService";
import { medicalAuthorizationsService } from "../services/medicalAuthorizationsService";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { notify } from "../utils/notifications.jsx";
import {
  FileText,
  Download,
  Filter,
  Calendar,
  BarChart3,
  PieChart,
  TrendingUp,
  Users,
  DollarSign,
  FileSpreadsheet,
  File,
  Search,
  RefreshCw,
} from "lucide-react";

interface ReportFilters {
  dateFrom: string;
  dateTo: string;
  contractType: string;
  status: string;
  clientId?: number;
}

interface ReportData {
  contracts: Contract[];
  authorizations: any[];
  summary: {
    totalContracts: number;
    activeContracts: number;
    totalRevenue: number;
    totalLives: number;
    totalAuthorizations: number;
    activeAuthorizations: number;
  };
}

const ReportsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [filters, setFilters] = useState<ReportFilters>({
    dateFrom: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
      .toISOString()
      .split("T")[0],
    dateTo: new Date().toISOString().split("T")[0],
    contractType: "todos",
    status: "todos",
  });
  const [reportType, setReportType] = useState<
    "contracts" | "authorizations" | "financial" | "comprehensive"
  >("comprehensive");

  useEffect(() => {
    generateReport();
  }, [filters, reportType]);

  const generateReport = async () => {
    try {
      setLoading(true);

      // Load contracts data
      const contractsResponse = await contractsService.listContracts({
        page: 1,
        size: 1000,
        status: filters.status !== "todos" ? filters.status : undefined,
        contract_type:
          filters.contractType !== "todos" ? filters.contractType : undefined,
      });

      // Load authorizations data
      const authResponse =
        await medicalAuthorizationsService.listAuthorizations({
          page: 1,
          size: 1000,
        });

      // Filter by date range
      const filteredContracts = contractsResponse.contracts.filter(
        (contract) => {
          const contractDate = new Date(contract.created_at);
          const fromDate = new Date(filters.dateFrom);
          const toDate = new Date(filters.dateTo);
          return contractDate >= fromDate && contractDate <= toDate;
        }
      );

      const filteredAuths = authResponse.authorizations.filter((auth) => {
        const authDate = new Date(auth.authorization_date);
        const fromDate = new Date(filters.dateFrom);
        const toDate = new Date(filters.dateTo);
        return authDate >= fromDate && authDate <= toDate;
      });

      // Calculate summary
      const summary = {
        totalContracts: filteredContracts.length,
        activeContracts: filteredContracts.filter((c) => c.status === "active")
          .length,
        totalRevenue: filteredContracts.reduce(
          (sum, c) => sum + (c.monthly_value || 0),
          0
        ),
        totalLives: filteredContracts.reduce(
          (sum, c) => sum + c.lives_contracted,
          0
        ),
        totalAuthorizations: filteredAuths.length,
        activeAuthorizations: filteredAuths.filter((a) => a.status === "active")
          .length,
      };

      setReportData({
        contracts: filteredContracts,
        authorizations: filteredAuths,
        summary,
      });
    } catch (error) {
      console.error("Erro ao gerar relatório:", error);
      notify.error("Erro ao gerar relatório");
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      notify.error("Não há dados para exportar");
      return;
    }

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(","),
      ...data.map((row) =>
        headers
          .map((header) => {
            const value = row[header];
            // Handle values that might contain commas
            return typeof value === "string" && value.includes(",")
              ? `"${value}"`
              : value;
          })
          .join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportContractsReport = () => {
    if (!reportData) return;

    const exportData = reportData.contracts.map((contract) => ({
      "Número do Contrato": contract.contract_number,
      Cliente: `Cliente #${contract.client_id}`,
      Tipo: contract.contract_type,
      Status: contract.status,
      "Vidas Contratadas": contract.lives_contracted,
      "Valor Mensal": contract.monthly_value || 0,
      "Data de Início": contract.start_date,
      "Data de Fim": contract.end_date || "Indefinido",
      "Data de Criação": contract.created_at,
    }));

    exportToCSV(
      exportData,
      `relatorio-contratos-${filters.dateFrom}-ate-${filters.dateTo}.csv`
    );
    notify.success("Relatório de contratos exportado com sucesso");
  };

  const exportAuthorizationsReport = () => {
    if (!reportData) return;

    const exportData = reportData.authorizations.map((auth) => ({
      "Código da Autorização": auth.authorization_code,
      Paciente: auth.patient_name,
      Médico: auth.doctor_name,
      Serviço: auth.service_name,
      Status: auth.status,
      Urgência: auth.urgency_level,
      "Data da Autorização": auth.authorization_date,
      "Válida de": auth.valid_from,
      "Válida até": auth.valid_until,
      "Sessões Autorizadas": auth.sessions_authorized || 0,
      "Sessões Restantes": auth.sessions_remaining || 0,
    }));

    exportToCSV(
      exportData,
      `relatorio-autorizacoes-${filters.dateFrom}-ate-${filters.dateTo}.csv`
    );
    notify.success("Relatório de autorizações exportado com sucesso");
  };

  const exportFinancialReport = () => {
    if (!reportData) return;

    const exportData = [
      {
        Período: `${filters.dateFrom} até ${filters.dateTo}`,
        "Total de Contratos": reportData.summary.totalContracts,
        "Contratos Ativos": reportData.summary.activeContracts,
        "Receita Total Mensal": reportData.summary.totalRevenue,
        "Vidas Contratadas": reportData.summary.totalLives,
        "Receita Média por Contrato":
          reportData.summary.totalContracts > 0
            ? (
                reportData.summary.totalRevenue /
                reportData.summary.totalContracts
              ).toFixed(2)
            : 0,
        "Total de Autorizações": reportData.summary.totalAuthorizations,
        "Autorizações Ativas": reportData.summary.activeAuthorizations,
      },
    ];

    exportToCSV(
      exportData,
      `relatorio-financeiro-${filters.dateFrom}-ate-${filters.dateTo}.csv`
    );
    notify.success("Relatório financeiro exportado com sucesso");
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="w-6 h-6 mr-2" />
            Relatórios e Análises
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Geração de relatórios customizados e exportação de dados
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Inicial
              </label>
              <Input
                type="date"
                value={filters.dateFrom}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateFrom: e.target.value }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Final
              </label>
              <Input
                type="date"
                value={filters.dateTo}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateTo: e.target.value }))
                }
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Contrato
              </label>
              <select
                value={filters.contractType}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    contractType: e.target.value,
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="todos">Todos os Tipos</option>
                <option value="INDIVIDUAL">Individual</option>
                <option value="CORPORATIVO">Corporativo</option>
                <option value="EMPRESARIAL">Empresarial</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, status: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="todos">Todos os Status</option>
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
                <option value="suspended">Suspenso</option>
                <option value="terminated">Terminado</option>
                <option value="draft">Rascunho</option>
              </select>
            </div>
          </div>

          {/* Report Type Selection */}
          <div className="flex flex-wrap gap-2 mb-4">
            <Button
              variant={reportType === "comprehensive" ? "default" : "outline"}
              onClick={() => setReportType("comprehensive")}
              size="sm"
            >
              <FileText className="w-4 h-4 mr-2" />
              Relatório Completo
            </Button>
            <Button
              variant={reportType === "contracts" ? "default" : "outline"}
              onClick={() => setReportType("contracts")}
              size="sm"
            >
              <Users className="w-4 h-4 mr-2" />
              Contratos
            </Button>
            <Button
              variant={reportType === "authorizations" ? "default" : "outline"}
              onClick={() => setReportType("authorizations")}
              size="sm"
            >
              <FileText className="w-4 h-4 mr-2" />
              Autorizações
            </Button>
            <Button
              variant={reportType === "financial" ? "default" : "outline"}
              onClick={() => setReportType("financial")}
              size="sm"
            >
              <DollarSign className="w-4 h-4 mr-2" />
              Financeiro
            </Button>
          </div>

          {/* Generate Report Button */}
          <div className="flex justify-end">
            <Button onClick={generateReport} disabled={loading}>
              <RefreshCw
                className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
              />
              {loading ? "Gerando..." : "Gerar Relatório"}
            </Button>
          </div>
        </div>
      </Card>

      {/* Report Summary */}
      {reportData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="p-4">
              <div className="flex items-center">
                <FileText className="w-8 h-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">
                    Total Contratos
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {reportData.summary.totalContracts}
                  </p>
                </div>
              </div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">
                    Contratos Ativos
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {reportData.summary.activeContracts}
                  </p>
                </div>
              </div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="flex items-center">
                <DollarSign className="w-8 h-8 text-purple-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">
                    Receita Total
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(reportData.summary.totalRevenue)}
                  </p>
                </div>
              </div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="flex items-center">
                <FileText className="w-8 h-8 text-orange-500" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-500">
                    Total Autorizações
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {reportData.summary.totalAuthorizations}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Export Options */}
      {reportData && (
        <Card>
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <Download className="w-5 h-5 mr-2" />
              Exportar Relatórios
            </h3>
            <div className="flex flex-wrap gap-3">
              <Button onClick={exportContractsReport} variant="outline">
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Exportar Contratos (CSV)
              </Button>
              <Button onClick={exportAuthorizationsReport} variant="outline">
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Exportar Autorizações (CSV)
              </Button>
              <Button onClick={exportFinancialReport} variant="outline">
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Exportar Financeiro (CSV)
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Report Content */}
      {reportData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Contracts Summary */}
          {(reportType === "comprehensive" || reportType === "contracts") && (
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Resumo de Contratos
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total de Contratos:</span>
                    <span className="font-medium">
                      {reportData.summary.totalContracts}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Contratos Ativos:</span>
                    <span className="font-medium">
                      {reportData.summary.activeContracts}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Vidas Contratadas:</span>
                    <span className="font-medium">
                      {reportData.summary.totalLives}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Receita Mensal Total:</span>
                    <span className="font-medium">
                      {formatCurrency(reportData.summary.totalRevenue)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Authorizations Summary */}
          {(reportType === "comprehensive" ||
            reportType === "authorizations") && (
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Resumo de Autorizações
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">
                      Total de Autorizações:
                    </span>
                    <span className="font-medium">
                      {reportData.summary.totalAuthorizations}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Autorizações Ativas:</span>
                    <span className="font-medium">
                      {reportData.summary.activeAuthorizations}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Taxa de Ativação:</span>
                    <span className="font-medium">
                      {reportData.summary.totalAuthorizations > 0
                        ? `${(
                            (reportData.summary.activeAuthorizations /
                              reportData.summary.totalAuthorizations) *
                            100
                          ).toFixed(1)}%`
                        : "0%"}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Financial Summary */}
          {(reportType === "comprehensive" || reportType === "financial") && (
            <Card className="lg:col-span-2">
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 mr-2" />
                  Análise Financeira
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(reportData.summary.totalRevenue)}
                    </p>
                    <p className="text-sm text-blue-600">Receita Total</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {reportData.summary.totalContracts > 0
                        ? formatCurrency(
                            reportData.summary.totalRevenue /
                              reportData.summary.totalContracts
                          )
                        : formatCurrency(0)}
                    </p>
                    <p className="text-sm text-green-600">
                      Receita Média por Contrato
                    </p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {reportData.summary.totalLives}
                    </p>
                    <p className="text-sm text-purple-600">Total de Vidas</p>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Gerando relatório...</p>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !reportData && (
        <Card>
          <div className="p-8 text-center">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Nenhum relatório gerado
            </h3>
            <p className="text-gray-500 mb-4">
              Configure os filtros e clique em "Gerar Relatório" para visualizar
              os dados.
            </p>
            <Button onClick={generateReport}>Gerar Primeiro Relatório</Button>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ReportsPage;
