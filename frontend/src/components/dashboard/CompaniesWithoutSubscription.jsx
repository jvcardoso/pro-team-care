import React from 'react';
import { useNavigate } from 'react-router-dom';

const CompaniesWithoutSubscription = ({ companies }) => {
  const navigate = useNavigate();

  if (!companies || companies.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">✅ Empresas Sem Assinatura</h3>
        </div>
        <div className="card-content">
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="text-lg">🎉 Todas as empresas possuem assinatura ativa!</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header flex items-center justify-between">
        <h3 className="card-title">⚠️ Empresas Sem Assinatura ({companies.length})</h3>
        <span className="text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 px-2 py-1 rounded-full">
          Oportunidades de Venda
        </span>
      </div>
      <div className="card-content">
        <div className="space-y-3">
          {companies.map((company) => (
            <div
              key={company.id}
              className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors cursor-pointer"
              onClick={() => navigate(`/admin/empresas/${company.id}`)}
            >
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-white">{company.name}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  ID: {company.id} • Criada há {company.days_without_subscription} dias
                </p>
              </div>
              <button
                className="btn btn-sm btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/admin/empresas/${company.id}`);
                }}
              >
                Ver Detalhes
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CompaniesWithoutSubscription;
