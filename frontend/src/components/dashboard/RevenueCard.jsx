import React from "react";

const RevenueCard = ({ revenue }) => {
  if (!revenue) return null;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value || 0);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">💰 Receita e Assinaturas B2B</h3>
      </div>
      <div className="card-content">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/20 p-4 rounded-lg">
            <p className="text-sm text-green-700 dark:text-green-400 font-medium">
              MRR (Receita Mensal)
            </p>
            <p className="text-2xl font-bold text-green-900 dark:text-green-300 mt-1">
              {formatCurrency(revenue.mrr)}
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20 p-4 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-400 font-medium">
              Assinaturas Ativas
            </p>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-300 mt-1">
              {revenue.active_subscriptions} / {revenue.total_companies}
            </p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              Taxa: {revenue.conversion_rate}%
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/20 p-4 rounded-lg">
            <p className="text-sm text-purple-700 dark:text-purple-400 font-medium">
              Faturas Pagas
            </p>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-300 mt-1">
              {formatCurrency(revenue.paid_invoices?.total || 0)}
            </p>
            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              {revenue.paid_invoices?.count || 0} faturas
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-700 dark:text-yellow-400 font-medium">
                  Faturas Pendentes
                </p>
                <p className="text-xl font-bold text-yellow-900 dark:text-yellow-300 mt-1">
                  {formatCurrency(revenue.pending_invoices?.total || 0)}
                </p>
              </div>
              <div className="text-3xl">⏳</div>
            </div>
            <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-2">
              {revenue.pending_invoices?.count || 0} faturas aguardando
              pagamento
            </p>
          </div>

          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 dark:text-green-400 font-medium">
                  Recebido
                </p>
                <p className="text-xl font-bold text-green-900 dark:text-green-300 mt-1">
                  {formatCurrency(revenue.paid_invoices?.total || 0)}
                </p>
              </div>
              <div className="text-3xl">✅</div>
            </div>
            <p className="text-xs text-green-600 dark:text-green-400 mt-2">
              {revenue.paid_invoices?.count || 0} faturas pagas
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RevenueCard;
