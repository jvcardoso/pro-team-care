/**
 * useBillingDashboard Hook
 * Manages billing dashboard data and state
 */

import { useState, useEffect, useCallback } from "react";
import billingService from "../services/billingService";
import {
  BillingDashboardResponse,
  BillingMetrics,
  Invoice,
  ContractBillingStatus,
  BillingSchedule,
} from "../types/billing.types";

interface UseBillingDashboardState {
  dashboard: BillingDashboardResponse | null;
  metrics: BillingMetrics | null;
  recentInvoices: Invoice[];
  contractsStatus: ContractBillingStatus[];
  upcomingBillings: BillingSchedule[];
  loading: boolean;
  error: string | null;
}

interface UseBillingDashboardActions {
  fetchDashboard: () => Promise<void>;
  fetchMetrics: (companyId?: number) => Promise<void>;
  refresh: () => Promise<void>;
  clearError: () => void;
}

type UseBillingDashboardReturn = UseBillingDashboardState &
  UseBillingDashboardActions;

export const useBillingDashboard = (
  companyId?: number
): UseBillingDashboardReturn => {
  const [state, setState] = useState<UseBillingDashboardState>({
    dashboard: null,
    metrics: null,
    recentInvoices: [],
    contractsStatus: [],
    upcomingBillings: [],
    loading: false,
    error: null,
  });

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const fetchDashboard = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const dashboard = await billingService.getBillingDashboard();

      setState((prev) => ({
        ...prev,
        dashboard,
        metrics: dashboard.metrics,
        recentInvoices: dashboard.recent_invoices,
        contractsStatus: dashboard.contracts_status,
        upcomingBillings: dashboard.upcoming_billings,
        loading: false,
      }));
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || "Erro ao carregar dashboard";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, []);

  const fetchMetrics = useCallback(
    async (targetCompanyId?: number) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const metrics = await billingService.getBillingMetrics(
          targetCompanyId || companyId
        );

        setState((prev) => ({
          ...prev,
          metrics,
          loading: false,
        }));
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "Erro ao carregar métricas";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
      }
    },
    [companyId]
  );

  const refresh = useCallback(async () => {
    await Promise.all([fetchDashboard(), fetchMetrics(companyId)]);
  }, [fetchDashboard, fetchMetrics, companyId]);

  // Initial load
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    ...state,
    fetchDashboard,
    fetchMetrics,
    refresh,
    clearError,
  };
};
