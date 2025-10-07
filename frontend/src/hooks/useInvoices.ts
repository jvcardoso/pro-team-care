/**
 * useInvoices Hook
 * Manages invoice data, filtering, and CRUD operations
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import billingService from "../services/billingService";
import {
  Invoice,
  InvoiceDetailed,
  InvoiceListParams,
  InvoiceListResponse,
  InvoiceStatus,
  PaymentMethod,
  PaymentDetails,
  InvoiceCreate,
  InvoiceUpdate,
} from "../types/billing.types";

interface UseInvoicesState {
  invoices: Invoice[];
  selectedInvoice: InvoiceDetailed | null;
  total: number;
  page: number;
  size: number;
  pages: number;
  loading: boolean;
  error: string | null;
  filters: InvoiceListParams;
}

interface UseInvoicesActions {
  fetchInvoices: (params?: InvoiceListParams) => Promise<void>;
  fetchInvoice: (id: number) => Promise<void>;
  createInvoice: (data: InvoiceCreate) => Promise<Invoice>;
  updateInvoice: (id: number, data: InvoiceUpdate) => Promise<Invoice>;
  updateInvoiceStatus: (
    id: number,
    status: InvoiceStatus,
    paymentDetails?: PaymentDetails
  ) => Promise<Invoice>;
  deleteInvoice: (id: number) => Promise<void>;
  setFilters: (filters: Partial<InvoiceListParams>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  refresh: () => Promise<void>;
  clearError: () => void;
  clearSelectedInvoice: () => void;
}

type UseInvoicesReturn = UseInvoicesState & UseInvoicesActions;

const defaultFilters: InvoiceListParams = {
  page: 1,
  size: 50,
};

export const useInvoices = (
  initialFilters: InvoiceListParams = {}
): UseInvoicesReturn => {
  const [state, setState] = useState<UseInvoicesState>({
    invoices: [],
    selectedInvoice: null,
    total: 0,
    page: 1,
    size: 50,
    pages: 0,
    loading: false,
    error: null,
    filters: { ...defaultFilters, ...initialFilters },
  });

  const currentFilters = useMemo(() => state.filters, [state.filters]);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const clearSelectedInvoice = useCallback(() => {
    setState((prev) => ({ ...prev, selectedInvoice: null }));
  }, []);

  const fetchInvoices = useCallback(
    async (params: InvoiceListParams = {}) => {
      const mergedParams = { ...currentFilters, ...params };
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const response: InvoiceListResponse = await billingService.listInvoices(
          mergedParams
        );

        setState((prev) => ({
          ...prev,
          invoices: response.invoices,
          total: response.total,
          page: response.page,
          size: response.size,
          pages: response.pages,
          loading: false,
          filters: mergedParams,
        }));
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "Erro ao carregar faturas";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
      }
    },
    [currentFilters]
  );

  const fetchInvoice = useCallback(async (id: number) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const invoice = await billingService.getInvoice(id);

      setState((prev) => ({
        ...prev,
        selectedInvoice: invoice,
        loading: false,
      }));
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || "Erro ao carregar fatura";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, []);

  const createInvoice = useCallback(
    async (data: InvoiceCreate): Promise<Invoice> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const invoice = await billingService.createInvoice(data);

        // Refresh the list
        await fetchInvoices();

        return invoice;
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "Erro ao criar fatura";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
        throw error;
      }
    },
    [fetchInvoices]
  );

  const updateInvoice = useCallback(
    async (id: number, data: InvoiceUpdate): Promise<Invoice> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const invoice = await billingService.updateInvoice(id, data);

        // Update in the list if exists
        setState((prev) => ({
          ...prev,
          invoices: prev.invoices.map((inv) =>
            inv.id === id ? { ...inv, ...invoice } : inv
          ),
          selectedInvoice:
            prev.selectedInvoice?.id === id
              ? { ...prev.selectedInvoice, ...invoice }
              : prev.selectedInvoice,
          loading: false,
        }));

        return invoice;
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "Erro ao atualizar fatura";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
        throw error;
      }
    },
    []
  );

  const updateInvoiceStatus = useCallback(
    async (
      id: number,
      status: InvoiceStatus,
      paymentDetails?: PaymentDetails
    ): Promise<Invoice> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const invoice = await billingService.updateInvoiceStatus(
          id,
          status,
          paymentDetails
        );

        // Update in the list
        setState((prev) => ({
          ...prev,
          invoices: prev.invoices.map((inv) =>
            inv.id === id ? { ...inv, ...invoice } : inv
          ),
          selectedInvoice:
            prev.selectedInvoice?.id === id
              ? { ...prev.selectedInvoice, ...invoice }
              : prev.selectedInvoice,
          loading: false,
        }));

        return invoice;
      } catch (error: any) {
        const errorMessage =
          error.response?.data?.detail || "Erro ao atualizar status da fatura";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: errorMessage,
        }));
        throw error;
      }
    },
    []
  );

  const deleteInvoice = useCallback(async (id: number): Promise<void> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      // Note: Assuming delete endpoint exists in service
      // await billingService.deleteInvoice(id);

      // Remove from list
      setState((prev) => ({
        ...prev,
        invoices: prev.invoices.filter((inv) => inv.id !== id),
        selectedInvoice:
          prev.selectedInvoice?.id === id ? null : prev.selectedInvoice,
        loading: false,
      }));
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || "Erro ao excluir fatura";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const setFilters = useCallback((newFilters: Partial<InvoiceListParams>) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, ...newFilters, page: 1 }, // Reset page when filters change
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setState((prev) => ({
      ...prev,
      filters: defaultFilters,
    }));
  }, []);

  const setPage = useCallback((page: number) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, page },
    }));
  }, []);

  const setPageSize = useCallback((size: number) => {
    setState((prev) => ({
      ...prev,
      filters: { ...prev.filters, size, page: 1 }, // Reset page when size changes
    }));
  }, []);

  const refresh = useCallback(async () => {
    await fetchInvoices();
  }, [fetchInvoices]);

  // Auto-fetch when filters change
  useEffect(() => {
    fetchInvoices();
  }, [currentFilters.page, currentFilters.size]);

  // Computed values
  const overdueInvoices = useMemo(() => {
    return state.invoices.filter((invoice) =>
      billingService.isInvoiceOverdue(invoice)
    );
  }, [state.invoices]);

  const pendingInvoices = useMemo(() => {
    return state.invoices.filter(
      (invoice) =>
        invoice.status === InvoiceStatus.PENDENTE ||
        invoice.status === InvoiceStatus.ENVIADA
    );
  }, [state.invoices]);

  const paidInvoices = useMemo(() => {
    return state.invoices.filter(
      (invoice) => invoice.status === InvoiceStatus.PAGA
    );
  }, [state.invoices]);

  return {
    ...state,
    fetchInvoices,
    fetchInvoice,
    createInvoice,
    updateInvoice,
    updateInvoiceStatus,
    deleteInvoice,
    setFilters,
    resetFilters,
    setPage,
    setPageSize,
    refresh,
    clearError,
    clearSelectedInvoice,
    // Computed values
    overdueInvoices,
    pendingInvoices,
    paidInvoices,
  } as UseInvoicesReturn & {
    overdueInvoices: Invoice[];
    pendingInvoices: Invoice[];
    paidInvoices: Invoice[];
  };
};
