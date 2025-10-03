/**
 * useSubscriptionPlans Hook
 * Manages subscription plans data and operations for the data table
 */

import { useState, useEffect, useMemo } from "react";
import { createSubscriptionPlansConfig } from "../config/tables/subscription-plans.config";
import { B2BBillingService } from "../services/b2bBillingService";
import { SubscriptionPlan } from "../types/b2b-billing.types";
import { notify } from "../utils/notifications";
import {
  UseDataTableReturn,
  DataTableState,
  DataTableCallbacks,
  DataTableMetric,
} from "../types/dataTable.types";

interface UseSubscriptionPlansConfig {
  onCreatePlan?: () => void;
  onEditPlan?: (plan: SubscriptionPlan) => void;
  onViewPlan?: (plan: SubscriptionPlan) => void;
  onDeletePlan?: (plan: SubscriptionPlan) => void;
}

export function useSubscriptionPlans({
  onCreatePlan,
  onEditPlan,
  onViewPlan,
  onDeletePlan,
}: UseSubscriptionPlansConfig = {}): UseDataTableReturn<SubscriptionPlan> & { loading: boolean; error: string | null; refetch: () => void } {
  const [data, setData] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Table state
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, unknown>>({});
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);


  // Create config with callbacks
  const config = useMemo(() =>
    createSubscriptionPlansConfig(onCreatePlan, onEditPlan, onViewPlan, onDeletePlan),
    [onCreatePlan, onEditPlan, onViewPlan, onDeletePlan]
  );

  // Load subscription plans
  const loadPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const plansData = await B2BBillingService.getSubscriptionPlans(true); // Load all plans
      setData(plansData);
    } catch (err: unknown) {
      const errorMessage = 'Erro ao carregar planos: ' + (err instanceof Error ? err.message : String(err));
      setError(errorMessage);
      notify.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Filtered data
  const filteredData = useMemo(() => {
    let filtered = [...data];

    // Apply search
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((plan) =>
        config.searchFields.some((field) => {
          const value = plan[field as keyof SubscriptionPlan];
          return value?.toString().toLowerCase().includes(searchLower);
        })
      );
    }

    // Apply filters
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value && value !== "all") {
        filtered = filtered.filter((plan) => {
          const planValue = plan[key as keyof SubscriptionPlan];
          if (key === "monthly_price" && typeof value === "object" && value.min !== undefined && value.max !== undefined) {
            // Range filter for price
            return planValue >= value.min && planValue <= value.max;
          } else if (key === "max_users" && typeof value === "object" && value.min !== undefined && value.max !== undefined) {
            // Range filter for users
            const usersValue = planValue as number | null;
            return usersValue === null || (usersValue >= value.min && usersValue <= value.max);
          }
          return planValue === value;
        });
      }
    });

    return filtered;
  }, [data, searchTerm, activeFilters, config.searchFields]);

  // Pagination
  const totalPages = Math.ceil(filteredData.length / pageSize);
  const validCurrentPage = Math.min(currentPage, Math.max(1, totalPages));
  const startIndex = (validCurrentPage - 1) * pageSize;
  const paginatedData = filteredData.slice(startIndex, startIndex + pageSize);

  // Update current page if it becomes invalid
  useEffect(() => {
    if (validCurrentPage !== currentPage) {
      setCurrentPage(validCurrentPage);
    }
  }, [validCurrentPage, currentPage]);

  // Metrics disabled - only tables and filters needed
  const metrics: DataTableMetric[] = [];
  const detailedMetrics = undefined;

  // State object
  const state: DataTableState = {
    data: paginatedData,
    filteredData,
    loading,
    error,
    currentPage: validCurrentPage,
    pageSize,
    totalPages,
    searchTerm,
    activeFilters,
    selectedItems,
    showDetailedMetrics: false,
    showExportDropdown: false,
    selectedItemForModal: null,
    isModalOpen: false,
    hasActiveFilters: searchTerm !== "" || Object.values(activeFilters).some((value) => value && value !== "all"),
  };

  // Callbacks
  const callbacks: DataTableCallbacks<SubscriptionPlan> = {
    onSearch: (term: string) => {
      setSearchTerm(term);
      setCurrentPage(1);
    },

    onFilter: (key: string, value: unknown) => {
      setActiveFilters((prev) => ({ ...prev, [key]: value }));
      setCurrentPage(1);
    },

    onClearFilters: () => {
      setSearchTerm("");
      setActiveFilters({});
      setCurrentPage(1);
    },

    onSelectItem: (id: number, selected: boolean) => {
      setSelectedItems((prev) =>
        selected ? [...prev, id] : prev.filter((item) => item !== id)
      );
    },

    onSelectAll: (selected: boolean) => {
      setSelectedItems(selected ? paginatedData.map((item) => item.id) : []);
    },

    onPageChange: (page: number) => {
      setCurrentPage(page);
    },

    onPageSizeChange: (size: number) => {
      setPageSize(size);
      setCurrentPage(1);
    },

    onExport: (format: string, selectedData?: SubscriptionPlan[]) => {
      const dataToExport = selectedData || filteredData;

      switch (format) {
        case "csv":
          exportToCSV(dataToExport, "planos-assinatura");
          break;
        case "json":
          exportToJSON(dataToExport, "planos-assinatura");
          break;
        case "print":
          printData(dataToExport);
          break;
      }
    },
  };

  // Load data on mount
  useEffect(() => {
    loadPlans();
  }, []);

  return {
    state,
    callbacks,
    metrics,
    detailedMetrics,
    loading,
    error,
    refetch: loadPlans,
  };
}

// Helper functions for export
function exportToCSV(data: SubscriptionPlan[], filename: string) {
  const headers = [
    "ID",
    "Nome",
    "Descrição",
    "Valor Mensal",
    "Usuários Máximo",
    "Estabelecimentos Máximo",
    "Status",
    "Criado em",
  ];

  const csvContent = [
    headers.join(","),
    ...data.map((plan) => [
      plan.id,
      `"${plan.name}"`,
      `"${plan.description || ""}"`,
      plan.monthly_price,
      plan.max_users || "Ilimitado",
      plan.max_establishments || "Ilimitado",
      plan.is_active ? "Ativo" : "Inativo",
      plan.created_at,
    ].join(",")),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.csv`;
  link.click();
}

function exportToJSON(data: SubscriptionPlan[], filename: string) {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.json`;
  link.click();
}

function printData(data: SubscriptionPlan[]) {
  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  const htmlContent = `
    <html>
      <head>
        <title>Planos de Assinatura</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .currency { text-align: right; }
          .status { text-align: center; }
        </style>
      </head>
      <body>
        <h1>Planos de Assinatura</h1>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Valor Mensal</th>
              <th>Usuários</th>
              <th>Estabelecimentos</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${data.map(plan => `
              <tr>
                <td>${plan.id}</td>
                <td>${plan.name}</td>
                <td class="currency">R$ ${plan.monthly_price.toFixed(2)}</td>
                <td>${plan.max_users || "Ilimitado"}</td>
                <td>${plan.max_establishments || "Ilimitado"}</td>
                <td class="status">${plan.is_active ? "Ativo" : "Inativo"}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </body>
    </html>
  `;

  printWindow.document.write(htmlContent);
  printWindow.document.close();
  printWindow.print();
}