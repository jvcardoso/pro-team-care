/**
 * InvoiceTable Component
 * DataTable for displaying and managing invoices
 */

import React, { useState } from "react";
import {
  Invoice,
  InvoiceTableRow,
  InvoiceListParams,
  PaymentMethod,
  InvoiceStatus,
} from "../../types/billing.types";
import { ColumnConfig } from "../../types/dataTable.types";
import billingService from "../../services/billingService";
import InvoiceStatusBadge from "./InvoiceStatusBadge";
import PaymentMethodBadge from "./PaymentMethodBadge";

interface InvoiceTableProps {
  invoices: InvoiceTableRow[];
  loading?: boolean;
  onInvoiceSelect?: (invoice: Invoice) => void;
  onStatusUpdate?: (invoiceId: number, status: InvoiceStatus) => void;
  onPaymentUpdate?: (
    invoiceId: number,
    method: PaymentMethod,
    reference?: string
  ) => void;
  showActions?: boolean;
  className?: string;
}

const InvoiceTable: React.FC<InvoiceTableProps> = ({
  invoices,
  loading = false,
  onInvoiceSelect,
  onStatusUpdate,
  onPaymentUpdate,
  showActions = true,
  className = "",
}) => {
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]);
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: "asc" | "desc";
  } | null>(null);

  const columns: ColumnConfig<InvoiceTableRow>[] = [
    {
      key: "invoice_number",
      label: "Número",
      sortable: true,
      render: (value, row) => (
        <div
          className="font-medium text-blue-600 cursor-pointer hover:text-blue-800"
          onClick={() => onInvoiceSelect?.(row)}
        >
          {value}
        </div>
      ),
    },
    {
      key: "contract_number",
      label: "Contrato",
      sortable: true,
      render: (value) => <span className="font-mono text-sm">{value}</span>,
    },
    {
      key: "client_name",
      label: "Cliente",
      sortable: true,
      render: (value) => <span className="text-gray-900">{value}</span>,
    },
    {
      key: "billing_period_start",
      label: "Período",
      render: (value, row) => (
        <div className="text-sm">
          <div>{billingService.formatDate(value)}</div>
          <div className="text-gray-500">
            até {billingService.formatDate(row.billing_period_end)}
          </div>
        </div>
      ),
    },
    {
      key: "lives_count",
      label: "Vidas",
      sortable: true,
      render: (value) => <span className="text-center block">{value}</span>,
    },
    {
      key: "total_amount",
      label: "Valor Total",
      sortable: true,
      render: (value) => (
        <span className="font-semibold text-gray-900">
          {billingService.formatCurrency(value)}
        </span>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (value, row) => (
        <InvoiceStatusBadge status={value} isOverdue={row.is_overdue} />
      ),
    },
    {
      key: "due_date",
      label: "Vencimento",
      sortable: true,
      render: (value, row) => (
        <div className="text-sm">
          <div className={row.is_overdue ? "text-red-600 font-medium" : ""}>
            {billingService.formatDate(value)}
          </div>
          {row.days_overdue > 0 && (
            <div className="text-xs text-red-500">
              {row.days_overdue} dias em atraso
            </div>
          )}
        </div>
      ),
    },
    {
      key: "payment_method",
      label: "Pagamento",
      render: (value) => (value ? <PaymentMethodBadge method={value} /> : "-"),
    },
  ];

  if (showActions) {
    columns.push({
      key: "actions",
      label: "Ações",
      render: (_, row) => (
        <div className="flex space-x-2">
          <button
            onClick={() => onInvoiceSelect?.(row)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Ver
          </button>
          {row.status !== InvoiceStatus.PAGA &&
            row.status !== InvoiceStatus.CANCELADA && (
              <button
                onClick={() => handleQuickPayment(row)}
                className="text-green-600 hover:text-green-800 text-sm font-medium"
              >
                Pagar
              </button>
            )}
        </div>
      ),
    });
  }

  const handleQuickPayment = (invoice: InvoiceTableRow) => {
    // Open quick payment modal or update status
    onStatusUpdate?.(invoice.id, InvoiceStatus.PAGA);
  };

  const handleSort = (key: string) => {
    let direction: "asc" | "desc" = "asc";

    if (
      sortConfig &&
      sortConfig.key === key &&
      sortConfig.direction === "asc"
    ) {
      direction = "desc";
    }

    setSortConfig({ key, direction });
  };

  const sortedInvoices = React.useMemo(() => {
    if (!sortConfig) return invoices;

    return [...invoices].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof InvoiceTableRow];
      const bValue = b[sortConfig.key as keyof InvoiceTableRow];

      if (aValue < bValue) {
        return sortConfig.direction === "asc" ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === "asc" ? 1 : -1;
      }
      return 0;
    });
  }, [invoices, sortConfig]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedInvoices(invoices.map((invoice) => invoice.id));
    } else {
      setSelectedInvoices([]);
    }
  };

  const handleSelectInvoice = (invoiceId: number, checked: boolean) => {
    if (checked) {
      setSelectedInvoices((prev) => [...prev, invoiceId]);
    } else {
      setSelectedInvoices((prev) => prev.filter((id) => id !== invoiceId));
    }
  };

  if (loading) {
    return (
      <div className={`bg-white shadow rounded-lg ${className}`}>
        <div className="animate-pulse">
          <div className="h-16 bg-gray-200 rounded-t-lg"></div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 border-t"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white shadow rounded-lg overflow-hidden ${className}`}>
      {/* Table header with bulk actions */}
      {selectedInvoices.length > 0 && (
        <div className="bg-blue-50 px-6 py-3 border-b border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-700">
              {selectedInvoices.length} fatura(s) selecionada(s)
            </span>
            <div className="flex space-x-2">
              <button className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                Marcar como Paga
              </button>
              <button className="text-sm bg-gray-600 text-white px-3 py-1 rounded hover:bg-gray-700">
                Exportar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={
                    selectedInvoices.length === invoices.length &&
                    invoices.length > 0
                  }
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </th>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    column.sortable ? "cursor-pointer hover:text-gray-700" : ""
                  }`}
                  onClick={
                    column.sortable ? () => handleSort(column.key) : undefined
                  }
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.label}</span>
                    {column.sortable && sortConfig?.key === column.key && (
                      <span className="text-blue-500">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedInvoices.map((invoice) => (
              <tr key={invoice.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={selectedInvoices.includes(invoice.id)}
                    onChange={(e) =>
                      handleSelectInvoice(invoice.id, e.target.checked)
                    }
                  />
                </td>
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="px-6 py-4 whitespace-nowrap text-sm"
                  >
                    {column.render
                      ? column.render(
                          invoice[column.key as keyof InvoiceTableRow],
                          invoice
                        )
                      : invoice[column.key as keyof InvoiceTableRow]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty state */}
      {invoices.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">📄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhuma fatura encontrada
          </h3>
          <p className="text-gray-500">
            Não há faturas para exibir com os filtros atuais.
          </p>
        </div>
      )}
    </div>
  );
};

export default InvoiceTable;
