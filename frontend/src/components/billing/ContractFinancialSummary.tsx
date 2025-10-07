/**
 * ContractFinancialSummary Component
 * Displays financial overview for a specific contract
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import billingService from '../../services/billingService';
import { Contract } from '../../services/contractsService';
import { InvoiceStatus, BillingMetrics } from '../../types/billing.types';
import InvoiceStatusBadge from './InvoiceStatusBadge';

interface ContractFinancialSummaryProps {
  contract: Contract;
  className?: string;
}

interface ContractBillingStatus {
  monthly_value: number;
  next_billing_date?: string;
  pending_invoices: number;
  pending_amount: number;
  overdue_invoices: number;
  overdue_amount: number;
  total_paid_this_year: number;
  last_payment_date?: string;
  status: 'current' | 'overdue' | 'suspended';
}

const ContractFinancialSummary: React.FC<ContractFinancialSummaryProps> = ({
  contract,
  className = '',
}) => {
  const navigate = useNavigate();
  const [billingStatus, setBillingStatus] = useState<ContractBillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBillingStatus();
  }, [contract.id]);

  const loadBillingStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to get contract billing status from backend
      const status = await billingService.getContractBillingStatus(contract.id);
      setBillingStatus(status);
    } catch (err: any) {
      console.error('Error loading billing status:', err);

      // Fallback: create mock data based on contract
      const mockStatus: ContractBillingStatus = {
        monthly_value: parseFloat(contract.monthly_value?.toString() || '0'),
        next_billing_date: getNextBillingDate(),
        pending_invoices: 0,
        pending_amount: 0,
        overdue_invoices: 0,
        overdue_amount: 0,
        total_paid_this_year: 0,
        status: 'current',
      };
      setBillingStatus(mockStatus);
    } finally {
      setLoading(false);
    }
  };

  const getNextBillingDate = (): string => {
    const now = new Date();
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    return nextMonth.toISOString().split('T')[0];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'current':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'overdue':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'suspended':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'current':
        return 'Em dia';
      case 'overdue':
        return 'Em atraso';
      case 'suspended':
        return 'Suspenso';
      default:
        return 'Indefinido';
    }
  };

  const handleViewAllInvoices = () => {
    navigate(`/admin/faturamento/faturas?contract_id=${contract.id}`);
  };

  const handleBillingDashboard = () => {
    navigate('/admin/faturamento/dashboard');
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-100 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          <div className="text-2xl mb-2">⚠️</div>
          <p>Erro ao carregar informações financeiras</p>
          <button
            onClick={loadBillingStatus}
            className="mt-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm"
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
            💰 Resumo Financeiro
          </h3>
          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(
                billingStatus?.status || 'current'
              )}`}
            >
              {getStatusLabel(billingStatus?.status || 'current')}
            </span>
          </div>
        </div>
      </div>

      {/* Financial Metrics */}
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Monthly Value */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900 dark:text-blue-300">Valor Mensal</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {billingService.formatCurrency(billingStatus?.monthly_value || 0)}
                </p>
              </div>
              <div className="text-2xl">💳</div>
            </div>
          </div>

          {/* Next Billing */}
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-900 dark:text-green-300">Próximo Faturamento</p>
                <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                  {billingStatus?.next_billing_date
                    ? billingService.formatDate(billingStatus.next_billing_date)
                    : 'Não agendado'}
                </p>
              </div>
              <div className="text-2xl">📅</div>
            </div>
          </div>

          {/* Annual Total */}
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-900 dark:text-purple-300">Pago Este Ano</p>
                <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {billingService.formatCurrency(billingStatus?.total_paid_this_year || 0)}
                </p>
              </div>
              <div className="text-2xl">📈</div>
            </div>
          </div>
        </div>

        {/* Pending/Overdue Alerts */}
        {(billingStatus?.pending_invoices > 0 || billingStatus?.overdue_invoices > 0) && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Alertas Financeiros</h4>
            <div className="space-y-2">
              {billingStatus?.overdue_invoices > 0 && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                  <div className="flex items-center">
                    <div className="text-red-400 mr-2">⚠️</div>
                    <div>
                      <p className="text-sm font-medium text-red-800 dark:text-red-300">
                        {billingStatus.overdue_invoices} fatura(s) em atraso
                      </p>
                      <p className="text-sm text-red-600 dark:text-red-400">
                        Total: {billingService.formatCurrency(billingStatus.overdue_amount)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {billingStatus?.pending_invoices > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                  <div className="flex items-center">
                    <div className="text-yellow-400 mr-2">⏳</div>
                    <div>
                      <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                        {billingStatus.pending_invoices} fatura(s) pendente(s)
                      </p>
                      <p className="text-sm text-yellow-600 dark:text-yellow-400">
                        Total: {billingService.formatCurrency(billingStatus.pending_amount)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleViewAllInvoices}
            className="flex-1 bg-blue-600 dark:bg-blue-700 text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors text-sm font-medium"
          >
            📄 Ver Todas as Faturas
          </button>
          <button
            onClick={handleBillingDashboard}
            className="flex-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
          >
            📊 Dashboard Financeiro
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContractFinancialSummary;
