/**
 * BillingDashboardPage
 * Main dashboard for billing overview and metrics
 */

import React, { useState } from "react";
import { useBillingDashboard } from "../hooks/useBillingDashboard";
import { useAuth } from "../contexts/AuthContext";
import BillingMetricsCards from "../components/billing/BillingMetricsCards";
import InvoiceTable from "../components/billing/InvoiceTable";
import { Invoice, InvoiceStatus } from "../types/billing.types";

const BillingDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [selectedTimeframe, setSelectedTimeframe] = useState<
    "7d" | "30d" | "90d"
  >("30d");

  const {
    dashboard,
    metrics,
    recentInvoices,
    contractsStatus,
    upcomingBillings,
    loading,
    error,
    fetchDashboard,
    refresh,
    clearError,
  } = useBillingDashboard(user?.company_id);

  const handleInvoiceSelect = (invoice: Invoice) => {
    // Navigate to invoice details or open modal
    console.log("Selected invoice:", invoice);
  };

  const handleRefresh = async () => {
    await refresh();
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-700 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Erro ao carregar dashboard
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="space-x-3">
              <button
                onClick={handleRefresh}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Tentar Novamente
              </button>
              <button
                onClick={clearError}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Dashboard de Faturamento
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Acompanhe métricas financeiras e status de cobrança
                </p>
              </div>
              <div className="flex items-center space-x-3">
                {/* Timeframe selector */}
                <div className="flex bg-gray-100 rounded-lg p-1">
                  {[
                    { key: "7d", label: "7 dias" },
                    { key: "30d", label: "30 dias" },
                    { key: "90d", label: "90 dias" },
                  ].map((timeframe) => (
                    <button
                      key={timeframe.key}
                      onClick={() => setSelectedTimeframe(timeframe.key as any)}
                      className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                        selectedTimeframe === timeframe.key
                          ? "bg-white dark:bg-gray-800 text-gray-900 shadow-sm"
                          : "text-gray-500 hover:text-gray-700"
                      }`}
                    >
                      {timeframe.label}
                    </button>
                  ))}
                </div>
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                >
                  <span className={loading ? "animate-spin" : ""}>🔄</span>
                  <span>Atualizar</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Metrics Cards */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Métricas Gerais
            </h2>
            <BillingMetricsCards
              metrics={
                metrics || {
                  total_pending_invoices: 0,
                  total_pending_amount: 0,
                  total_overdue_invoices: 0,
                  total_overdue_amount: 0,
                  total_paid_this_month: 0,
                  total_expected_this_month: 0,
                  collection_rate_percentage: 0,
                }
              }
              loading={loading}
            />
          </section>

          {/* Quick Actions */}
          <section>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Ações Rápidas
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-2 border-dashed border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-center">
                <div className="text-2xl mb-2">📄</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  Nova Fatura
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Criar fatura manual
                </div>
              </button>

              <button className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-2 border-dashed border-gray-200 hover:border-green-300 hover:bg-green-50 transition-colors text-center">
                <div className="text-2xl mb-2">⚡</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  Faturamento Automático
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Executar cobrança em lote
                </div>
              </button>

              <button className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-2 border-dashed border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-colors text-center">
                <div className="text-2xl mb-2">📊</div>
                <div className="font-medium text-gray-900 dark:text-white">
                  Relatórios
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Exportar dados financeiros
                </div>
              </button>
            </div>
          </section>

          {/* Recent Invoices */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                Faturas Recentes
              </h2>
              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                Ver todas →
              </button>
            </div>
            <InvoiceTable
              invoices={recentInvoices.map((invoice) => ({
                ...invoice,
                client_name: invoice.contract?.client_name || "N/A",
                contract_number: invoice.contract?.contract_number || "N/A",
                is_overdue:
                  new Date(invoice.due_date) < new Date() &&
                  ![InvoiceStatus.PAGA, InvoiceStatus.CANCELADA].includes(
                    invoice.status
                  ),
                days_overdue:
                  new Date(invoice.due_date) < new Date()
                    ? Math.ceil(
                        (new Date().getTime() -
                          new Date(invoice.due_date).getTime()) /
                          (1000 * 60 * 60 * 24)
                      )
                    : 0,
              }))}
              loading={loading}
              onInvoiceSelect={handleInvoiceSelect}
              showActions={true}
            />
          </section>

          {/* Status Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Contracts Status */}
            <section>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Status dos Contratos
              </h2>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                {loading ? (
                  <div className="p-6">
                    <div className="animate-pulse space-y-4">
                      {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-4 bg-gray-200 rounded"></div>
                      ))}
                    </div>
                  </div>
                ) : contractsStatus.length > 0 ? (
                  <div className="divide-y divide-gray-200">
                    {contractsStatus.slice(0, 5).map((contract) => (
                      <div
                        key={contract.contract_id}
                        className="p-4 hover:bg-gray-50"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {contract.client_name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {contract.contract_number}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium text-gray-900 dark:text-white">
                              R${" "}
                              {contract.monthly_value.toLocaleString("pt-BR", {
                                minimumFractionDigits: 2,
                              })}
                            </div>
                            {contract.overdue_invoices > 0 && (
                              <div className="text-sm text-red-600">
                                {contract.overdue_invoices} em atraso
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                    Nenhum contrato encontrado
                  </div>
                )}
              </div>
            </section>

            {/* Upcoming Billings */}
            <section>
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Próximos Faturamentos
              </h2>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                {loading ? (
                  <div className="p-6">
                    <div className="animate-pulse space-y-4">
                      {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-4 bg-gray-200 rounded"></div>
                      ))}
                    </div>
                  </div>
                ) : upcomingBillings.length > 0 ? (
                  <div className="divide-y divide-gray-200">
                    {upcomingBillings.slice(0, 5).map((billing) => (
                      <div key={billing.id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900 dark:text-white">
                              {billing.contract?.client_name || "N/A"}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {new Date(
                                billing.next_billing_date
                              ).toLocaleDateString("pt-BR")}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium text-gray-900 dark:text-white">
                              R${" "}
                              {billing.amount_per_cycle.toLocaleString(
                                "pt-BR",
                                { minimumFractionDigits: 2 }
                              )}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {billing.billing_cycle}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                    Nenhum faturamento programado
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BillingDashboardPage;
