/**
 * InvoicesPage
 * Complete invoice management page with filtering and CRUD operations
 */

import React, { useState, useEffect } from "react";
import { useInvoices } from "../hooks/useInvoices";
import { useAuth } from "../contexts/AuthContext";
import InvoiceTable from "../components/billing/InvoiceTable";
import InvoiceStatusBadge from "../components/billing/InvoiceStatusBadge";
import PaymentMethodBadge from "../components/billing/PaymentMethodBadge";
import {
  Invoice,
  InvoiceStatus,
  PaymentMethod,
  InvoiceListParams,
} from "../types/billing.types";

const InvoicesPage: React.FC = () => {
  const { user } = useAuth();
  const [showFilters, setShowFilters] = useState(false);
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);

  const {
    invoices,
    selectedInvoice,
    total,
    page,
    size,
    pages,
    loading,
    error,
    filters,
    fetchInvoices,
    fetchInvoice,
    updateInvoiceStatus,
    setFilters,
    resetFilters,
    setPage,
    setPageSize,
    refresh,
    clearError,
    overdueInvoices,
    pendingInvoices,
    paidInvoices,
  } = useInvoices();

  const handleFilterChange = (newFilters: Partial<InvoiceListParams>) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    resetFilters();
    setShowFilters(false);
  };

  const handleInvoiceSelect = (invoice: Invoice) => {
    fetchInvoice(invoice.id);
  };

  const handleStatusUpdate = async (
    invoiceId: number,
    status: InvoiceStatus
  ) => {
    try {
      await updateInvoiceStatus(invoiceId, status, {
        paid_date:
          status === InvoiceStatus.PAGA
            ? new Date().toISOString().split("T")[0]
            : undefined,
        payment_method:
          status === InvoiceStatus.PAGA ? PaymentMethod.PIX : undefined,
      });
    } catch (error) {
      console.error("Error updating invoice status:", error);
    }
  };

  const handleBulkAction = async (
    action: "mark_paid" | "mark_sent" | "export"
  ) => {
    if (selectedInvoices.length === 0) return;

    switch (action) {
      case "mark_paid":
        for (const invoiceId of selectedInvoices) {
          try {
            await updateInvoiceStatus(invoiceId, InvoiceStatus.PAGA, {
              paid_date: new Date().toISOString().split("T")[0],
              payment_method: PaymentMethod.PIX,
            });
          } catch (error) {
            console.error(`Error updating invoice ${invoiceId}:`, error);
          }
        }
        setSelectedInvoices([]);
        break;
      case "mark_sent":
        for (const invoiceId of selectedInvoices) {
          try {
            await updateInvoiceStatus(invoiceId, InvoiceStatus.ENVIADA);
          } catch (error) {
            console.error(`Error updating invoice ${invoiceId}:`, error);
          }
        }
        setSelectedInvoices([]);
        break;
      case "export":
        // TODO: Implement export functionality
        console.log("Exporting invoices:", selectedInvoices);
        break;
    }
  };

  const statusOptions = [
    { value: "", label: "Todos os status" },
    { value: InvoiceStatus.PENDENTE, label: "Pendente" },
    { value: InvoiceStatus.ENVIADA, label: "Enviada" },
    { value: InvoiceStatus.PAGA, label: "Paga" },
    { value: InvoiceStatus.VENCIDA, label: "Vencida" },
    { value: InvoiceStatus.EM_ATRASO, label: "Em Atraso" },
    { value: InvoiceStatus.CANCELADA, label: "Cancelada" },
  ];

  // Enhanced invoice data with computed fields
  const enhancedInvoices = invoices.map((invoice) => ({
    ...invoice,
    client_name: invoice.contract?.client_name || "N/A",
    contract_number: invoice.contract?.contract_number || "N/A",
    is_overdue:
      new Date(invoice.due_date) < new Date() &&
      ![InvoiceStatus.PAGA, InvoiceStatus.CANCELADA].includes(invoice.status),
    days_overdue:
      new Date(invoice.due_date) < new Date()
        ? Math.ceil(
            (new Date().getTime() - new Date(invoice.due_date).getTime()) /
              (1000 * 60 * 60 * 24)
          )
        : 0,
  }));

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Erro ao carregar faturas
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="space-x-3">
              <button
                onClick={refresh}
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
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Faturas</h1>
                <p className="text-gray-600">
                  Gerencie faturas, pagamentos e cobranças
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`px-4 py-2 rounded-lg border ${
                    showFilters
                      ? "bg-blue-50 border-blue-200 text-blue-700"
                      : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  🔍 Filtros
                </button>
                <button
                  onClick={refresh}
                  disabled={loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? "⏳" : "🔄"} Atualizar
                </button>
                <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
                  ➕ Nova Fatura
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                <p className="text-2xl font-bold text-gray-900">{total}</p>
              </div>
              <div className="text-2xl">📄</div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pendentes</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {pendingInvoices.length}
                </p>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Em Atraso</p>
                <p className="text-2xl font-bold text-red-600">
                  {overdueInvoices.length}
                </p>
              </div>
              <div className="text-2xl">⚠️</div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pagas</p>
                <p className="text-2xl font-bold text-green-600">
                  {paidInvoices.length}
                </p>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={filters.status || ""}
                  onChange={(e) =>
                    handleFilterChange({
                      status: (e.target.value as InvoiceStatus) || undefined,
                    })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Inicial
                </label>
                <input
                  type="date"
                  value={filters.start_date || ""}
                  onChange={(e) =>
                    handleFilterChange({
                      start_date: e.target.value || undefined,
                    })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Final
                </label>
                <input
                  type="date"
                  value={filters.end_date || ""}
                  onChange={(e) =>
                    handleFilterChange({
                      end_date: e.target.value || undefined,
                    })
                  }
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex items-end space-x-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.overdue_only || false}
                    onChange={(e) =>
                      handleFilterChange({
                        overdue_only: e.target.checked || undefined,
                      })
                    }
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Apenas em atraso
                  </span>
                </label>
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-4">
              <button
                onClick={handleResetFilters}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Limpar
              </button>
              <button
                onClick={() => fetchInvoices(filters)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Aplicar Filtros
              </button>
            </div>
          </div>
        )}

        {/* Bulk Actions */}
        {selectedInvoices.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-700">
                {selectedInvoices.length} fatura(s) selecionada(s)
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleBulkAction("mark_paid")}
                  className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700"
                >
                  Marcar como Paga
                </button>
                <button
                  onClick={() => handleBulkAction("mark_sent")}
                  className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                >
                  Marcar como Enviada
                </button>
                <button
                  onClick={() => handleBulkAction("export")}
                  className="text-sm bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700"
                >
                  Exportar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Invoice Table */}
        <InvoiceTable
          invoices={enhancedInvoices}
          loading={loading}
          onInvoiceSelect={handleInvoiceSelect}
          onStatusUpdate={handleStatusUpdate}
          showActions={true}
        />

        {/* Pagination */}
        {pages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6 mt-6 rounded-lg shadow">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                onClick={() => setPage(Math.min(pages, page + 1))}
                disabled={page >= pages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Próximo
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando{" "}
                  <span className="font-medium">{(page - 1) * size + 1}</span> a{" "}
                  <span className="font-medium">
                    {Math.min(page * size, total)}
                  </span>{" "}
                  de <span className="font-medium">{total}</span> resultados
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page <= 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    ‹
                  </button>
                  {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                    const pageNum = i + 1;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          page === pageNum
                            ? "z-10 bg-blue-50 border-blue-500 text-blue-600"
                            : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setPage(Math.min(pages, page + 1))}
                    disabled={page >= pages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    ›
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InvoicesPage;
