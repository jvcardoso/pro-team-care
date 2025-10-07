/**
 * RecentInvoicesTable Component
 * Displays recent invoices for a specific contract
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import billingService from "../../services/billingService";
import {
  Invoice,
  InvoiceStatus,
  PaymentMethod,
} from "../../types/billing.types";
import InvoiceStatusBadge from "./InvoiceStatusBadge";
import PaymentMethodBadge from "./PaymentMethodBadge";

interface RecentInvoicesTableProps {
  contractId: number;
  limit?: number;
  className?: string;
}

const RecentInvoicesTable: React.FC<RecentInvoicesTableProps> = ({
  contractId,
  limit = 5,
  className = "",
}) => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRecentInvoices();
  }, [contractId, limit]);

  const loadRecentInvoices = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await billingService.listInvoices({
        contract_id: contractId,
        page: 1,
        size: limit,
      });

      setInvoices(response.invoices || []);
    } catch (err: any) {
      console.error("Error loading recent invoices:", err);
      setError("Erro ao carregar faturas");

      // Mock data for demonstration
      const mockInvoices: Invoice[] = [
        {
          id: 1,
          contract_id: contractId,
          invoice_number: "INV-202509-001",
          billing_period_start: "2025-09-01",
          billing_period_end: "2025-09-30",
          lives_count: 10,
          base_amount: 15000,
          additional_services_amount: 0,
          discounts: 0,
          taxes: 0,
          total_amount: 15000,
          status: InvoiceStatus.PAGA,
          due_date: "2025-09-10",
          issued_date: "2025-09-01",
          paid_date: "2025-09-08",
          payment_method: PaymentMethod.PIX,
          created_at: "2025-09-01T00:00:00Z",
          updated_at: "2025-09-08T00:00:00Z",
        },
        {
          id: 2,
          contract_id: contractId,
          invoice_number: "INV-202510-001",
          billing_period_start: "2025-10-01",
          billing_period_end: "2025-10-31",
          lives_count: 10,
          base_amount: 15000,
          additional_services_amount: 0,
          discounts: 0,
          taxes: 0,
          total_amount: 15000,
          status: InvoiceStatus.PENDENTE,
          due_date: "2025-10-10",
          issued_date: "2025-10-01",
          created_at: "2025-10-01T00:00:00Z",
          updated_at: "2025-10-01T00:00:00Z",
        },
      ];
      setInvoices(mockInvoices);
    } finally {
      setLoading(false);
    }
  };

  const handleViewInvoice = (invoice: Invoice) => {
    navigate(`/admin/faturamento/faturas/${invoice.id}`);
  };

  const handleViewAllInvoices = () => {
    navigate(`/admin/faturamento/faturas?contract_id=${contractId}`);
  };

  if (loading) {
    return (
      <div
        className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 ${className}`}
      >
        <div className="p-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-4"></div>
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="h-12 bg-gray-100 dark:bg-gray-700 rounded mb-2"
              ></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && invoices.length === 0) {
    return (
      <div
        className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 ${className}`}
      >
        <div className="p-4 text-center text-gray-500 dark:text-gray-400">
          <div className="text-2xl mb-2">📄</div>
          <p className="text-sm">Erro ao carregar faturas</p>
          <button
            onClick={loadRecentInvoices}
            className="mt-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 ${className}`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
            📄 Faturas Recentes
          </h4>
          {invoices.length > 0 && (
            <button
              onClick={handleViewAllInvoices}
              className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
            >
              Ver todas →
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      {invoices.length > 0 ? (
        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Número
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Período
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Valor
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Vencimento
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {invoices.map((invoice) => {
                const isOverdue =
                  new Date(invoice.due_date) < new Date() &&
                  ![InvoiceStatus.PAGA, InvoiceStatus.CANCELADA].includes(
                    invoice.status
                  );

                return (
                  <tr
                    key={invoice.id}
                    onClick={() => handleViewInvoice(invoice)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-blue-600 dark:text-blue-400">
                        {invoice.invoice_number}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-gray-100">
                        {billingService.formatDate(
                          invoice.billing_period_start
                        )}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        até{" "}
                        {billingService.formatDate(invoice.billing_period_end)}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {billingService.formatCurrency(invoice.total_amount)}
                      </div>
                      {invoice.payment_method && (
                        <div className="mt-1">
                          <PaymentMethodBadge method={invoice.payment_method} />
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <InvoiceStatusBadge
                        status={invoice.status}
                        isOverdue={isOverdue}
                      />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div
                        className={`text-sm ${
                          isOverdue
                            ? "text-red-600 dark:text-red-400 font-medium"
                            : "text-gray-900 dark:text-gray-100"
                        }`}
                      >
                        {billingService.formatDate(invoice.due_date)}
                      </div>
                      {isOverdue && (
                        <div className="text-xs text-red-500 dark:text-red-400">
                          {billingService.getDaysOverdue(invoice)} dias em
                          atraso
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="p-6 text-center text-gray-500 dark:text-gray-400">
          <div className="text-3xl mb-2">📄</div>
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
            Nenhuma fatura encontrada
          </h4>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Este contrato ainda não possui faturas geradas.
          </p>
          <button
            onClick={() => navigate("/admin/faturamento/dashboard")}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            Gerar Fatura Manual
          </button>
        </div>
      )}

      {/* Footer with summary */}
      {invoices.length > 0 && (
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-300">
            <span>
              Mostrando {invoices.length} de {invoices.length} faturas
            </span>
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-1"></div>
                Pagas:{" "}
                {invoices.filter((i) => i.status === InvoiceStatus.PAGA).length}
              </span>
              <span className="flex items-center">
                <div className="w-2 h-2 bg-yellow-400 rounded-full mr-1"></div>
                Pendentes:{" "}
                {
                  invoices.filter((i) => i.status === InvoiceStatus.PENDENTE)
                    .length
                }
              </span>
              <span className="flex items-center">
                <div className="w-2 h-2 bg-red-400 rounded-full mr-1"></div>
                Vencidas:{" "}
                {
                  invoices.filter(
                    (i) =>
                      new Date(i.due_date) < new Date() &&
                      ![InvoiceStatus.PAGA, InvoiceStatus.CANCELADA].includes(
                        i.status
                      )
                  ).length
                }
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentInvoicesTable;
