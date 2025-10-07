/**
 * useCompanyBillingData Hook
 * Manages company billing data for the Company X Plans table
 */

import { useState, useEffect, useMemo } from "react";
import { companiesService } from "../services/api";
import { B2BBillingService } from "../services/b2bBillingService";
import { UseDataTableReturn, DataTableState, DataTableCallbacks } from "../types/dataTable.types";

export interface CompanyBillingData {
  id: number;
  name: string;
  cnpj: string;
  status: string;
  active_plan?: {
    name: string;
    monthly_price: number;
  };
  next_billing_date?: string;
  monthly_value: number;
  payment_method?: string;
  created_at: string;
}

export function useCompanyBillingData(): UseDataTableReturn<CompanyBillingData> & { loading: boolean; error: string | null; refetch: () => void } {
  const [data, setData] = useState<CompanyBillingData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Table state
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, unknown>>({});
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Load company billing data
  const loadCompanyBillingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch companies and plans in parallel
      const [companiesResponse, plans] = await Promise.all([
        companiesService.getCompanies(),
        B2BBillingService.getSubscriptionPlans(true)
      ]);

      const companies = Array.isArray(companiesResponse) ? companiesResponse : [];

      // Create a map of plans for quick lookup
      const plansMap = new Map(plans.map(plan => [plan.id, plan]));

      // 🚀 OTIMIZAÇÃO: Buscar subscriptions em batch (1 requisição em vez de N)
      const companyIds = companies.map((company: any) => company.id);
      const subscriptions = await B2BBillingService.getCompanySubscriptionsBatch(companyIds);

      // Criar mapa company_id -> subscription
      const subscriptionsMap = new Map(
        subscriptions
          .map((sub, index) => (sub ? [companyIds[index], sub] : null))
          .filter(Boolean) as [number, any][]
      );

      // Build company billing data with subscriptions
      const companyBillingData: CompanyBillingData[] = companies.map((company: any) => {
        const subscription = subscriptionsMap.get(company.id);
        let activePlan = undefined;
        let nextBillingDate = undefined;
        let monthlyValue = 0;
        let paymentMethod = undefined;

        if (subscription) {
          const plan = plansMap.get(subscription.plan_id);
          if (plan) {
            activePlan = {
              name: plan.name,
              monthly_price: plan.monthly_price
            };
            monthlyValue = Number(plan.monthly_price) || 0;
            nextBillingDate = subscription.next_billing_date;
            paymentMethod = subscription.payment_method || 'Não informado';
          }
        }

        return {
          id: company.id,
          name: company.name || company.company_name || 'Nome não informado',
          cnpj: company.tax_id || company.cnpj || company.document || 'CNPJ não informado',
          status: subscription ? 'Ativo' : 'Sem plano',
          active_plan: activePlan,
          next_billing_date: nextBillingDate,
          monthly_value: monthlyValue,
          payment_method: paymentMethod,
          created_at: company.created_at || new Date().toISOString(),
        };
      });

      setData(companyBillingData);
    } catch (err: unknown) {
      const errorMessage = 'Erro ao carregar dados de cobrança: ' + (err instanceof Error ? err.message : String(err));
      setError(errorMessage);
      // console.error('Error loading company billing data:', err);
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
      filtered = filtered.filter((company) =>
        ['name', 'cnpj', 'status'].some((field) => {
          const value = company[field as keyof CompanyBillingData];
          return value?.toString().toLowerCase().includes(searchLower);
        })
      );
    }

    // Apply filters
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value && value !== "all") {
        filtered = filtered.filter((company) => {
          const companyValue = company[key as keyof CompanyBillingData];
          if (key === "monthly_value" && typeof value === "object" && value.min !== undefined && value.max !== undefined) {
            return companyValue >= value.min && companyValue <= value.max;
          }
          return companyValue === value;
        });
      }
    });

    return filtered;
  }, [data, searchTerm, activeFilters]);

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
  const callbacks: DataTableCallbacks<CompanyBillingData> = {
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

    onExport: (format: string, selectedData?: CompanyBillingData[]) => {
      const dataToExport = selectedData || filteredData;

      switch (format) {
        case "csv":
          exportToCSV(dataToExport, "empresas-cobranca");
          break;
        case "json":
          exportToJSON(dataToExport, "empresas-cobranca");
          break;
        case "print":
          printData(dataToExport);
          break;
      }
    },
  };

  // Load data on mount
  useEffect(() => {
    loadCompanyBillingData();
  }, []);

  return {
    state,
    callbacks,
    metrics: [],
    detailedMetrics: undefined,
    loading,
    error,
    refetch: loadCompanyBillingData,
  };
}

// Helper functions for export
function exportToCSV(data: CompanyBillingData[], filename: string) {
  const headers = [
    "ID",
    "Empresa",
    "CNPJ",
    "Status",
    "Plano Ativo",
    "Próxima Cobrança",
    "Valor Mensal",
    "Método",
    "Criado em",
  ];

  const csvContent = [
    headers.join(","),
    ...data.map((company) => [
      company.id,
      `"${company.name}"`,
      `"${company.cnpj}"`,
      `"${company.status}"`,
      company.active_plan ? `"${company.active_plan.name}"` : "",
      company.next_billing_date || "",
      company.monthly_value,
      company.payment_method || "",
      company.created_at,
    ].join(",")),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.csv`;
  link.click();
}

function exportToJSON(data: CompanyBillingData[], filename: string) {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${filename}.json`;
  link.click();
}

function printData(data: CompanyBillingData[]) {
  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  const htmlContent = `
    <html>
      <head>
        <title>Empresas - Cobrança</title>
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
        <h1>Empresas - Cobrança</h1>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Empresa</th>
              <th>CNPJ</th>
              <th>Status</th>
              <th>Plano Ativo</th>
              <th>Valor Mensal</th>
              <th>Método</th>
            </tr>
          </thead>
          <tbody>
            ${data.map(company => `
              <tr>
                <td>${company.id}</td>
                <td>${company.name}</td>
                <td>${company.cnpj}</td>
                <td class="status">${company.status}</td>
                <td>${company.active_plan?.name || 'Nenhum'}</td>
                <td class="currency">R$ ${company.monthly_value.toFixed(2)}</td>
                <td>${company.payment_method || 'Não informado'}</td>
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
