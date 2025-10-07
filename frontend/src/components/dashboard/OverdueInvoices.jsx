import React from "react";

const OverdueInvoices = ({ invoices }) => {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value || 0);
  };

  if (!invoices || invoices.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">✅ Faturas Vencidas</h3>
        </div>
        <div className="card-content">
          <div className="text-center py-8 text-green-600 dark:text-green-400">
            <div className="text-5xl mb-3">✅</div>
            <p className="text-lg font-medium">Nenhuma fatura vencida!</p>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Todos os pagamentos em dia
            </p>
          </div>
        </div>
      </div>
    );
  }

  const totalOverdue = invoices.reduce((sum, inv) => sum + inv.amount, 0);

  return (
    <div className="card border-l-4 border-red-500 dark:border-red-600">
      <div className="card-header flex items-center justify-between">
        <h3 className="card-title text-red-700 dark:text-red-400">
          🔴 Faturas Vencidas - ATENÇÃO!
        </h3>
        <div className="text-right">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Total em Atraso
          </p>
          <p className="text-xl font-bold text-red-700 dark:text-red-400">
            {formatCurrency(totalOverdue)}
          </p>
        </div>
      </div>
      <div className="card-content">
        <div className="space-y-3">
          {invoices.map((invoice) => (
            <div
              key={invoice.id}
              className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-bold text-gray-900 dark:text-white">
                    {invoice.company_name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Fatura #{invoice.invoice_number}
                  </p>
                  <p className="text-xs text-red-700 dark:text-red-400 mt-2 font-medium">
                    ⚠️ Vencida há {invoice.days_overdue} dias
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-red-700 dark:text-red-400">
                    {formatCurrency(invoice.amount)}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Vencimento:{" "}
                    {new Date(invoice.due_date).toLocaleDateString("pt-BR")}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OverdueInvoices;
