/**
 * Hook para gerenciar dados da tabela de empresas
 * Implementa toda a lógica de filtros, paginação, busca e métricas
 */

import { useState, useEffect, useMemo } from "react";
import { Company } from "../types/company.types";
import {
  UseDataTableReturn,
  DataTableState,
  DataTableCallbacks,
} from "../types/dataTable.types";

export interface UseCompaniesDataTableProps {
  initialPageSize?: number;
}

export function useCompaniesDataTable({
  initialPageSize = 10,
}: UseCompaniesDataTableProps = {}): UseDataTableReturn<Company> {
  // State
  const [data, setData] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Table state
  const [searchTerm, setSearchTerm] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({});
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [showDetailedMetrics, setShowDetailedMetrics] = useState(false);

  // Fetch data
  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const { companiesService } = await import("../services/api");
      const response = await companiesService.getCompanies({
        skip: (currentPage - 1) * pageSize,
        limit: 1000, // Buscar mais dados para filtrar localmente
        search: searchTerm || undefined,
        status:
          activeFilters.status !== "all" ? activeFilters.status : undefined,
      });

      // A resposta agora tem o formato { companies: [...], total: X, page: Y, ... }
      setData(response?.companies || []);
    } catch (err: any) {
      setError(err.message || "Erro ao carregar empresas");
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  // Filtrar dados localmente
  const filteredData = useMemo(() => {
    let filtered = [...data];

    // Aplicar busca
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (company) =>
          company.name?.toLowerCase().includes(searchLower) ||
          company.trade_name?.toLowerCase().includes(searchLower) ||
          company.tax_id?.includes(searchTerm)
      );
    }

    // Aplicar filtros
    Object.entries(activeFilters).forEach(([key, value]) => {
      if (!value || value === "all") return;

      if (key === "status") {
        filtered = filtered.filter((company) => company.status === value);
      }
    });

    return filtered;
  }, [data, searchTerm, activeFilters]);

  // Dados paginados
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredData.slice(startIndex, endIndex);
  }, [filteredData, currentPage, pageSize]);

  // Calcular métricas
  const metrics = useMemo(() => {
    const activeCompanies = filteredData.filter(
      (c) => c.status === "active"
    ).length;
    const inactiveCompanies = filteredData.filter(
      (c) => c.status === "inactive"
    ).length;
    const suspendedCompanies = filteredData.filter(
      (c) => c.status === "suspended"
    ).length;

    return [
      {
        id: "total_companies",
        title: "Total de Empresas",
        value: filteredData.length,
        subtitle: "Cadastradas",
        icon: null,
        color: "blue" as const,
      },
      {
        id: "active_companies",
        title: "Empresas Ativas",
        value: activeCompanies,
        subtitle: `${
          filteredData.length > 0
            ? Math.round((activeCompanies / filteredData.length) * 100)
            : 0
        }%`,
        icon: null,
        color: "green" as const,
      },
      {
        id: "inactive_companies",
        title: "Empresas Inativas",
        value: inactiveCompanies,
        subtitle: `${
          filteredData.length > 0
            ? Math.round((inactiveCompanies / filteredData.length) * 100)
            : 0
        }%`,
        icon: null,
        color: "gray" as const,
      },
      {
        id: "suspended_companies",
        title: "Empresas Suspensas",
        value: suspendedCompanies,
        subtitle: `${
          filteredData.length > 0
            ? Math.round((suspendedCompanies / filteredData.length) * 100)
            : 0
        }%`,
        icon: null,
        color: "yellow" as const,
      },
    ];
  }, [filteredData]);

  // Métricas detalhadas
  const detailedMetrics = useMemo(() => {
    const statusBreakdown = {
      active: filteredData.filter((c) => c.status === "active").length,
      inactive: filteredData.filter((c) => c.status === "inactive").length,
      suspended: filteredData.filter((c) => c.status === "suspended").length,
    };

    return {
      title: "📊 Métricas Detalhadas de Empresas",
      sections: [
        {
          title: "📊 Status das Empresas",
          items: [
            {
              id: "status_active",
              title: "✅ Ativas",
              value: statusBreakdown.active,
              icon: null,
              color: "green" as const,
            },
            {
              id: "status_inactive",
              title: "⏸️ Inativas",
              value: statusBreakdown.inactive,
              icon: null,
              color: "gray" as const,
            },
            {
              id: "status_suspended",
              title: "⏳ Suspensas",
              value: statusBreakdown.suspended,
              icon: null,
              color: "yellow" as const,
            },
          ],
        },
      ],
      quickActions: [
        {
          label: "🔍 Ver Empresas Ativas",
          action: () => {
            setActiveFilters((prev) => ({ ...prev, status: "active" }));
          },
          color: "green" as const,
        },
        {
          label: "📄 Exportar Ativas",
          action: () => {
            const activeCompanies = filteredData.filter(
              (c) => c.status === "active"
            );
            exportToCSV(activeCompanies, "empresas_ativas");
          },
          color: "blue" as const,
        },
      ],
    };
  }, [filteredData]);

  // Callbacks
  const callbacks: DataTableCallbacks<Company> = {
    onSearch: (term: string) => {
      setSearchTerm(term);
      setCurrentPage(1);
    },

    onFilter: (key: string, value: any) => {
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

    onExport: (format: string, selectedData?: Company[]) => {
      const dataToExport = selectedData || filteredData;

      switch (format) {
        case "csv":
          exportToCSV(dataToExport, "empresas");
          break;
        case "json":
          exportToJSON(dataToExport, "empresas");
          break;
        case "print":
          printData(dataToExport);
          break;
      }
    },

    onToggleDetailedMetrics: () => {
      setShowDetailedMetrics((prev) => !prev);
    },
  };

  // State object
  const state: DataTableState = {
    data: paginatedData,
    filteredData,
    searchTerm,
    activeFilters,
    selectedItems,
    currentPage,
    pageSize,
    totalPages: Math.ceil(filteredData.length / pageSize),
    showDetailedMetrics,
  };

  // Load data on mount and when dependencies change
  useEffect(() => {
    fetchData();
  }, [currentPage, pageSize]); // Remover searchTerm e activeFilters pois fazemos filtro local

  return {
    state,
    callbacks,
    metrics,
    detailedMetrics,
    loading,
    error,
    refetch: fetchData,
  };
}

// Helper functions para export
function exportToCSV(data: Company[], filename: string) {
  const headers = [
    "ID",
    "Nome",
    "Nome Fantasia",
    "CNPJ",
    "Status",
    "Criado em",
  ];

  const csvContent = [
    headers.join(","),
    ...data.map((company) =>
      [
        company.id,
        `"${company.name}"`,
        `"${company.trade_name || ""}"`,
        company.tax_id,
        company.status,
        new Date(company.created_at).toLocaleDateString("pt-BR"),
      ].join(",")
    ),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function exportToJSON(data: Company[], filename: string) {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}.json`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function printData(data: Company[]) {
  const printContent = `
    <html>
      <head>
        <title>Relatório de Empresas</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .header { margin-bottom: 20px; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Relatório de Empresas</h1>
          <p>Gerado em: ${new Date().toLocaleDateString(
            "pt-BR"
          )} às ${new Date().toLocaleTimeString("pt-BR")}</p>
          <p>Total de empresas: ${data.length}</p>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>CNPJ/CPF</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Cidade</th>
            </tr>
          </thead>
          <tbody>
            ${data
              .map(
                (company) => `
              <tr>
                <td>${company.id}</td>
                <td>${company.name}</td>
                <td>${company.tax_id}</td>
                <td>${company.person_type}</td>
                <td>${company.status}</td>
                <td>${company.city || "N/A"}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
        </table>
      </body>
    </html>
  `;

  const printWindow = window.open("", "_blank");
  if (printWindow) {
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
  }
}

export default useCompaniesDataTable;
