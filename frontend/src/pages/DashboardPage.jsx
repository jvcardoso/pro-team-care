import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import ContextSwitcher from '../components/security/ContextSwitcher';
import MetricCard from '../components/dashboard/MetricCard';
import RevenueCard from '../components/dashboard/RevenueCard';
import CompaniesWithoutSubscription from '../components/dashboard/CompaniesWithoutSubscription';
import OverdueInvoices from '../components/dashboard/OverdueInvoices';
import RecentActivities from '../components/dashboard/RecentActivities';

const DashboardPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const { data } = await api.get('/api/v1/dashboard/admin');
        setDashboardData(data);
        setError(null);
      } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
        setError('Erro ao carregar dados do dashboard. Tente novamente.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();

    // Atualizar dashboard a cada 5 minutos
    const interval = setInterval(fetchDashboard, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="animate-fade-in">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Visão geral das atividades e métricas do sistema</p>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Carregando dados...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="animate-fade-in">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Visão geral das atividades e métricas do sistema</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button
            className="btn btn-primary mt-4"
            onClick={() => window.location.reload()}
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const { summary, revenue, companies_without_subscription, overdue_invoices, recent_activities, growth } = dashboardData;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard Administrativo</h1>
            <p className="text-gray-600">
              Visão geral do sistema Pro Team Care
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <ContextSwitcher />
          </div>
        </div>
      </div>

      {/* Metric Cards - Resumo Principal */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <MetricCard
          icon="🏢"
          title="Empresas Ativas"
          value={summary.total_companies}
          subtitle="Total de empresas cadastradas"
          trend={growth?.new_companies_month}
          color="blue"
        />
        <MetricCard
          icon="🏬"
          title="Estabelecimentos"
          value={summary.total_establishments}
          subtitle="Estabelecimentos ativos"
          color="green"
        />
        <MetricCard
          icon="🤝"
          title="Clientes"
          value={summary.total_clients}
          subtitle="Clientes cadastrados"
          trend={growth?.new_clients_month}
          color="purple"
        />
        <MetricCard
          icon="👥"
          title="Usuários Ativos"
          value={summary.total_users}
          subtitle="Usuários do sistema"
          color="orange"
        />
      </div>

      {/* Revenue Card */}
      <div className="mb-6">
        <RevenueCard revenue={revenue} />
      </div>

      {/* Grid de 2 colunas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Empresas Sem Assinatura */}
        <CompaniesWithoutSubscription companies={companies_without_subscription} />

        {/* Atividades Recentes */}
        <RecentActivities activities={recent_activities} />
      </div>

      {/* Faturas Vencidas - Full Width */}
      {overdue_invoices && overdue_invoices.length > 0 && (
        <div className="mb-6">
          <OverdueInvoices invoices={overdue_invoices} />
        </div>
      )}

      {/* Footer com timestamp */}
      <div className="mt-6 text-center text-xs text-gray-500">
        Última atualização: {new Date(dashboardData.generated_at).toLocaleString('pt-BR')}
      </div>
    </div>
  );
};

export default DashboardPage;
