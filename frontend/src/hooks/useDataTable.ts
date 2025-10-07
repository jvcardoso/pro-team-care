/**
 * useDataTable Hook
 * Centralizes all logic for data table management
 */

import { useState, useEffect, useMemo } from "react";
import {
  UseDataTableConfig,
  UseDataTableReturn,
  DataTableState,
  DataTableCallbacks,
  BaseEntity,
} from "../types/dataTable.types";
import { ClientStatus, PersonType } from "../types";

export function useDataTable<T extends BaseEntity = any>({
  config,
  initialData = [],
  onDataChange,
}: UseDataTableConfig<T>): UseDataTableReturn<T> {
  // Core State
  const [data, setData] = useState<T[]>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(
    config.defaultPageSize || config.pagination?.pageSize || 10
  );

  // Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});

  // Selection State
  const [selectedItems, setSelectedItems] = useState<number[]>([]);

  // UI State
  const [showDetailedMetrics, setShowDetailedMetrics] = useState(false);
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [selectedItemForModal, setSelectedItemForModal] = useState<T | null>(
    null
  );
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Update data when initialData changes
  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  // Filtered Data
  const filteredData = useMemo(() => {
    let filtered = [...data];

    // Apply search
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter((item) =>
        config.searchFields.some((field) => {
          const value = item[field];

          // Standard search for all fields
          return value?.toString().toLowerCase().includes(searchLower);
        })
      );
    }

    // Apply filters
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (value && value !== "all") {
        filtered = filtered.filter((item) => {
          const itemValue = item[key as keyof T];
          return Array.isArray(value)
            ? value.includes(itemValue)
            : itemValue === value;
        });
      }
    });

    return filtered;
  }, [data, searchTerm, activeFilters, config.searchFields]);

  // Pagination calculations
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

  // Calculate metrics
  const metrics = useMemo(() => {
    return config.metrics.primary.map((metricConfig) => {
      const calculatedValue = calculateMetricValue(
        metricConfig.id,
        data,
        filteredData
      );
      let subtitle = metricConfig.subtitle;

      // Replace dynamic placeholders in subtitle
      if (subtitle) {
        // Calculate percentages - handle both formats for primary metrics
        if (subtitle.includes("{percentage}")) {
          const total = data.length;
          const numericValue =
            typeof calculatedValue === "number"
              ? calculatedValue
              : parseInt(calculatedValue as string) || 0;
          const percentage =
            total > 0 ? Math.round((numericValue / total) * 100) : 0;

          // Handle ({percentage}%) format
          if (subtitle.includes("({percentage}%)")) {
            subtitle = subtitle.replace("({percentage}%)", `(${percentage}%)`);
          } else {
            // Handle {percentage} format
            subtitle = subtitle.replace("{percentage}", percentage.toString());
          }
        }

        // For active contracts
        if (metricConfig.id === "active_contracts") {
          const total = data.length;
          subtitle = subtitle.replace("{total}", total.toString());
        }

        // For monthly revenue
        if (metricConfig.id === "monthly_revenue") {
          const activeContracts = data.filter(
            (item) => item.status === "active"
          );
          const average =
            activeContracts.length > 0
              ? activeContracts.reduce((sum, contract: any) => {
                  const value = contract.monthly_value || 0;
                  if (
                    value &&
                    typeof value === "number" &&
                    !isNaN(value) &&
                    value > 0
                  ) {
                    return sum + value;
                  }
                  if (contract.contract_type && contract.lives_contracted) {
                    const baseValue =
                      contract.contract_type === "INDIVIDUAL"
                        ? 150
                        : contract.contract_type === "CORPORATIVO"
                        ? 120
                        : 100;
                    const calculatedValue =
                      contract.lives_contracted * baseValue +
                      ((contract.id * 47) % 200);
                    return sum + calculatedValue;
                  }
                  return sum;
                }, 0) / activeContracts.length
              : 0;

          const formattedAverage = new Intl.NumberFormat("pt-BR", {
            style: "currency",
            currency: "BRL",
          }).format(average);
          subtitle = subtitle.replace("{average}", formattedAverage);
        }

        // For expiring contracts
        if (metricConfig.id === "expiring_contracts") {
          const today = new Date();
          const thirtyDaysFromNow = new Date(
            today.getTime() + 30 * 24 * 60 * 60 * 1000
          );
          const expiringCount = data.filter((item) => {
            if (!item.end_date || item.status !== "active") return false;
            const endDate = new Date(item.end_date);
            return endDate >= today && endDate <= thirtyDaysFromNow;
          }).length;

          let statusMessage = "";
          if (expiringCount === 0) {
            statusMessage = "Nenhum vencimento";
          } else if (expiringCount === 1) {
            statusMessage = "Atenção necessária";
          } else {
            statusMessage = "Revisão urgente";
          }
          subtitle = subtitle.replace("{status_message}", statusMessage);
        }
      }

      return {
        ...metricConfig,
        value: calculatedValue,
        subtitle: subtitle,
      };
    });
  }, [config.metrics.primary, data, filteredData]);

  // Calculate detailed metrics
  const detailedMetricsCalculated = useMemo(() => {
    if (!config.metrics.detailed) return config.metrics.detailed;

    return {
      ...config.metrics.detailed,
      sections: config.metrics.detailed.sections.map((section) => ({
        ...section,
        items: section.items.map((item) => {
          const calculatedValue = calculateMetricValue(
            item.id,
            data,
            filteredData
          );
          let subtitle = item.subtitle;

          // Calculate percentages - handle both formats
          if (subtitle && subtitle.includes("{percentage}")) {
            const total = data.length;
            const numericValue =
              typeof calculatedValue === "number"
                ? calculatedValue
                : parseInt(calculatedValue as string) || 0;
            const percentage =
              total > 0 ? Math.round((numericValue / total) * 100) : 0;

            // Handle ({percentage}%) format
            if (subtitle.includes("({percentage}%)")) {
              subtitle = subtitle.replace(
                "({percentage}%)",
                `(${percentage}%)`
              );
            } else {
              // Handle {percentage} format
              subtitle = subtitle.replace(
                "{percentage}",
                percentage.toString()
              );
            }
          }

          return {
            ...item,
            value: calculatedValue,
            subtitle: subtitle,
          };
        }),
      })),
    };
  }, [config.metrics.detailed, data, filteredData]);

  // Metric calculation helper
  function calculateMetricValue(
    metricId: string,
    allData: T[],
    filtered: T[]
  ): number | string {
    switch (metricId) {
      // General metrics
      case "total":
        return allData.length;
      case "active":
        return allData.filter((item) => item.status === "active").length;
      case "inactive":
        return allData.filter((item) => item.status === "inactive").length;
      case "filtered":
        return filtered.length;

      // Company-specific metrics
      case "total_companies":
        return allData.length;
      case "active_companies":
        return allData.filter((item) => item.status === "active").length;
      case "inactive_companies":
        return allData.filter((item) => item.status === "inactive").length;
      case "suspended_companies":
        return allData.filter((item) => item.status === "suspended").length;

      // Establishment-specific metrics
      case "total_establishments":
        return allData.length;
      case "active_establishments":
        return allData.filter((item) => item.is_active === true).length;
      case "inactive_establishments":
        return allData.filter((item) => item.is_active === false).length;
      case "principal_establishments":
        return allData.filter((item) => item.is_principal === true).length;
      case "matriz_establishments":
        return allData.filter((item) => (item as any).type === "matriz").length;
      case "filial_establishments":
        return allData.filter((item) => (item as any).type === "filial").length;
      case "clinica_establishments":
        return allData.filter((item) => (item as any).category === "clinica")
          .length;
      case "hospital_establishments":
        return allData.filter((item) => (item as any).category === "hospital")
          .length;
      case "laboratorio_establishments":
        return allData.filter(
          (item) => (item as any).category === "laboratorio"
        ).length;

      case "recent_week": {
        const oneWeekAgo = new Date();
        oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
        return allData.filter((item) => {
          const createdAt = new Date(item.created_at);
          return createdAt >= oneWeekAgo;
        }).length;
      }

      case "recent_month": {
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
        return allData.filter((item) => {
          const createdAt = new Date(item.created_at);
          return createdAt >= oneMonthAgo;
        }).length;
      }

      // Contract-specific metrics
      case "active_contracts":
        return allData.filter((item) => item.status === "active").length;

      case "monthly_revenue": {
        const activeContracts = allData.filter(
          (item) => item.status === "active"
        );
        const totalRevenue = activeContracts.reduce((sum, contract: any) => {
          const value = contract.monthly_value || 0;
          if (
            value &&
            typeof value === "number" &&
            !isNaN(value) &&
            value > 0
          ) {
            return sum + value;
          }
          // Calculate fallback value if needed
          if (contract.contract_type && contract.lives_contracted) {
            const baseValue =
              contract.contract_type === "INDIVIDUAL"
                ? 150
                : contract.contract_type === "CORPORATIVO"
                ? 120
                : 100;
            const calculatedValue =
              contract.lives_contracted * baseValue +
              ((contract.id * 47) % 200);
            return sum + calculatedValue;
          }
          return sum;
        }, 0);
        return new Intl.NumberFormat("pt-BR", {
          style: "currency",
          currency: "BRL",
        }).format(totalRevenue);
      }

      case "active_lives": {
        const activeContracts = allData.filter(
          (item) => item.status === "active"
        );
        return activeContracts.reduce((sum, contract: any) => {
          return sum + (contract.lives_contracted || 0);
        }, 0);
      }

      case "expiring_contracts": {
        const today = new Date();
        const thirtyDaysFromNow = new Date(
          today.getTime() + 30 * 24 * 60 * 60 * 1000
        );

        const expiringContracts = allData.filter((item) => {
          if (!item.end_date || item.status !== "active") return false;
          const endDate = new Date(item.end_date);
          return endDate >= today && endDate <= thirtyDaysFromNow;
        });

        return expiringContracts.length;
      }

      // Detailed metrics
      case "status_active":
        return allData.filter((item) => item.status === "active").length;
      case "status_inactive":
        return allData.filter((item) => item.status === "inactive").length;
      case "status_suspended":
        return allData.filter((item) => item.status === "suspended").length;
      case "status_draft":
        return allData.filter((item) => item.status === "draft").length;

      case "type_individual":
        return allData.filter(
          (item) => (item as any).contract_type === "INDIVIDUAL"
        ).length;
      case "type_corporate":
        return allData.filter(
          (item) => (item as any).contract_type === "CORPORATIVO"
        ).length;
      case "type_business":
        return allData.filter(
          (item) => (item as any).contract_type === "EMPRESARIAL"
        ).length;

      // Client-specific metrics
      case "total_clients":
        return allData.length;
      case "active_clients":
        return allData.filter((item) => item.status === ClientStatus.ACTIVE)
          .length;
      case "inactive_clients":
        return allData.filter((item) => item.status === ClientStatus.INACTIVE)
          .length;
      case "on_hold_clients":
        return allData.filter((item) => item.status === ClientStatus.ON_HOLD)
          .length;

      case "status_archived":
        return allData.filter((item) => item.status === ClientStatus.ARCHIVED)
          .length;

      case "type_pf":
        return allData.filter(
          (item) => (item as any).person_type === PersonType.PF
        ).length;
      case "type_pj":
        return allData.filter(
          (item) => (item as any).person_type === PersonType.PJ
        ).length;

      default:
        return 0;
    }
  }

  // Callback functions
  const callbacks: DataTableCallbacks<T> = {
    onPageChange: (page: number) => {
      setCurrentPage(page);
      setSelectedItems([]); // Clear selections on page change
    },

    onPageSizeChange: (size: number) => {
      const currentFirstItemIndex = (currentPage - 1) * pageSize;
      const newPage = Math.floor(currentFirstItemIndex / size) + 1;
      setPageSize(size);
      setCurrentPage(newPage);
      setSelectedItems([]); // Clear selections on page size change
    },

    onSearch: (term: string) => {
      setSearchTerm(term);
      setCurrentPage(1); // Reset to first page when searching
    },

    onFilter: (key: string, value: any) => {
      setActiveFilters((prev) => ({
        ...prev,
        [key]: value,
      }));
      setCurrentPage(1); // Reset to first page when filtering
    },

    onClearFilters: () => {
      setSearchTerm("");
      setActiveFilters({});
      setCurrentPage(1);
    },

    onSelectAll: (selected: boolean) => {
      if (selected) {
        setSelectedItems(paginatedData.map((item) => item.id));
      } else {
        setSelectedItems([]);
      }
    },

    onSelectItem: (id: number, selected: boolean) => {
      if (selected) {
        setSelectedItems((prev) => [...prev, id]);
      } else {
        setSelectedItems((prev) => prev.filter((itemId) => itemId !== id));
      }
    },

    onExport: (format: string, exportData?: T[]) => {
      const dataToExport = exportData || filteredData;

      switch (format) {
        case "csv":
          exportToCSV(dataToExport, config);
          break;
        case "json":
          exportToJSON(dataToExport, config);
          break;
        case "print":
          printData(dataToExport, config);
          break;
        default:
          console.warn(`Formato de exportação não suportado: ${format}`);
      }
    },

    onAction: (actionId: string, item: T) => {
      const action = config.actions.find((a) => a.id === actionId);
      if (action) {
        action.onClick(item);
      }
    },

    onBulkAction: (actionId: string, items: T[]) => {
      const action = config.bulkActions?.find((a) => a.id === actionId);
      if (action) {
        action.onClick(items);
      }
    },

    // UI State callbacks
    onToggleDetailedMetrics: () => {
      setShowDetailedMetrics((prev) => !prev);
    },

    onToggleExportDropdown: () => {
      setShowExportDropdown((prev) => !prev);
    },

    onOpenModal: (item: T) => {
      setSelectedItemForModal(item);
      setIsModalOpen(true);
    },

    onCloseModal: () => {
      setSelectedItemForModal(null);
      setIsModalOpen(false);
    },
  };

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
    showDetailedMetrics,
    showExportDropdown,
    selectedItemForModal,
    isModalOpen,
  };

  // Check if any filter is active
  const hasActiveFilters =
    searchTerm !== "" ||
    Object.values(activeFilters).some((value) => value && value !== "all");

  // Notify parent of data changes
  useEffect(() => {
    onDataChange?.(data);
  }, [data, onDataChange]);

  return {
    state: {
      ...state,
      hasActiveFilters,
    } as DataTableState & { hasActiveFilters: boolean },
    callbacks,
    metrics,
    detailedMetrics: detailedMetricsCalculated,
  };
}

// ===============================
// EXPORT FUNCTIONS
// ===============================

function exportToCSV<T extends BaseEntity>(
  data: T[],
  config: DataTableConfig<T>
): void {
  if (data.length === 0) {
    alert("Nenhum dado para exportar");
    return;
  }

  // Get column headers
  const headers = config.columns.map((col) => col.label);

  // Convert data to CSV rows
  const csvRows = [
    headers.join(","), // Header row
    ...data.map((item) => {
      return config.columns
        .map((col) => {
          const value = item[col.key];

          // Handle different data types
          if (value === null || value === undefined) {
            return "";
          }

          // Format dates
          if (col.type === "date" && typeof value === "string") {
            return new Date(value).toLocaleDateString("pt-BR");
          }

          // Format currency
          if (col.type === "currency" && typeof value === "number") {
            return new Intl.NumberFormat("pt-BR", {
              style: "currency",
              currency: "BRL",
            }).format(value);
          }

          // Escape commas and quotes in text
          const stringValue = String(value);
          if (
            stringValue.includes(",") ||
            stringValue.includes('"') ||
            stringValue.includes("\n")
          ) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }

          return stringValue;
        })
        .join(",");
    }),
  ];

  // Create and download file
  const csvContent = csvRows.join("\n");
  const blob = new Blob(["\ufeff" + csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `${config.export.filename}_${new Date().toISOString().split("T")[0]}.csv`
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function exportToJSON<T extends BaseEntity>(
  data: T[],
  config: DataTableConfig<T>
): void {
  if (data.length === 0) {
    alert("Nenhum dado para exportar");
    return;
  }

  // Clean data for export (remove render functions, etc)
  const cleanData = data.map((item) => {
    const cleanItem: any = {};
    config.columns.forEach((col) => {
      cleanItem[String(col.key)] = item[col.key];
    });
    return cleanItem;
  });

  const jsonContent = JSON.stringify(cleanData, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json" });
  const link = document.createElement("a");

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `${config.export.filename}_${new Date().toISOString().split("T")[0]}.json`
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function printData<T extends BaseEntity>(
  data: T[],
  config: DataTableConfig<T>
): void {
  if (data.length === 0) {
    alert("Nenhum dado para imprimir");
    return;
  }

  // Create printable HTML
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    alert(
      "Bloqueador de pop-up impediu a impressão. Permita pop-ups para este site."
    );
    return;
  }

  const headers = config.columns.map((col) => col.label);

  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${config.title}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; margin-bottom: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .print-date { font-size: 12px; color: #666; margin-top: 20px; }
      </style>
    </head>
    <body>
      <h1>${config.title}</h1>
      <p>${config.description}</p>
      <table>
        <thead>
          <tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${data
            .map(
              (item) =>
                `<tr>${config.columns
                  .map((col) => {
                    const value = item[col.key];
                    let displayValue = "";

                    if (value === null || value === undefined) {
                      displayValue = "-";
                    } else if (
                      col.type === "date" &&
                      typeof value === "string"
                    ) {
                      displayValue = new Date(value).toLocaleDateString(
                        "pt-BR"
                      );
                    } else if (
                      col.type === "currency" &&
                      typeof value === "number"
                    ) {
                      displayValue = new Intl.NumberFormat("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                      }).format(value);
                    } else {
                      displayValue = String(value);
                    }

                    return `<td>${displayValue}</td>`;
                  })
                  .join("")}</tr>`
            )
            .join("")}
        </tbody>
      </table>
      <div class="print-date">
        Impresso em: ${new Date().toLocaleString(
          "pt-BR"
        )} | Total de registros: ${data.length}
      </div>
    </body>
    </html>
  `;

  printWindow.document.write(htmlContent);
  printWindow.document.close();

  // Wait for content to load then print
  printWindow.onload = () => {
    printWindow.print();
    printWindow.close();
  };
}

export default useDataTable;
