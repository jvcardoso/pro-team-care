/**
 * DataTableTemplate Component
 * Generic reusable data table template
 */

import React, { useEffect, useState } from "react";
import {
  DataTableConfig,
  BaseEntity,
  UseDataTableReturn,
} from "../../../types/dataTable.types";
import DataTableMetrics from "./DataTableMetrics";
import DataTableDetailedMetrics from "./DataTableDetailedMetrics";
import "./table-responsive.css";
import FiltersModal from "./FiltersModal";
import { FilterRenderer } from "./filters/FilterComponents";
import { getThemeClasses } from "../../../utils/tableThemes";
import ActionDropdown from "../../ui/ActionDropdown";

interface DataTableTemplateProps<T extends BaseEntity = any> {
  config: DataTableConfig<T>;
  tableData: UseDataTableReturn<T>;
  loading?: boolean;
}

export function DataTableTemplate<T extends BaseEntity = any>({
  config,
  tableData,
  loading = false,
}: DataTableTemplateProps<T>) {
  const { state, callbacks, metrics, detailedMetrics } = tableData;
  const [showFiltersModal, setShowFiltersModal] = useState(false);

  // Get theme classes
  const themeClasses = getThemeClasses(config.theme);

  // Mapeamento de entidades para português
  const getEntityLabel = (
    entity: string
  ): { singular: string; gender: "M" | "F" } => {
    const entityMap: Record<string, { singular: string; gender: "M" | "F" }> = {
      empresa: { singular: "Empresa", gender: "F" },
      clients: { singular: "Cliente", gender: "M" },
      clientes: { singular: "Cliente", gender: "M" },
      "establishment-clients": { singular: "Cliente", gender: "M" },
      estabelecimentos: { singular: "Estabelecimento", gender: "M" },
      profissionais: { singular: "Profissional", gender: "M" },
      usuarios: { singular: "Usuário", gender: "M" },
      pacientes: { singular: "Paciente", gender: "M" },
      contratos: { singular: "Contrato", gender: "M" },
      contracts: { singular: "Contrato", gender: "M" },
      users: { singular: "Usuário", gender: "M" },
      roles: { singular: "Perfil", gender: "M" },
      menus: { singular: "Menu", gender: "M" },
      services: { singular: "Serviço", gender: "M" },
      authorizations: { singular: "Autorização", gender: "F" },
      "medical-authorizations": { singular: "Autorização", gender: "F" },
      companies: { singular: "Empresa", gender: "F" },
      establishments: { singular: "Estabelecimento", gender: "M" },
      patients: { singular: "Paciente", gender: "M" },
      professionals: { singular: "Profissional", gender: "M" },
    };

    return entityMap[entity.toLowerCase()] || { singular: entity, gender: "M" };
  };

  const entityInfo = getEntityLabel(config.entity);
  const addButtonText =
    entityInfo.gender === "F"
      ? `Nova ${entityInfo.singular}`
      : `Novo ${entityInfo.singular}`;

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest(".relative")) {
        // Close all dropdowns
        document
          .querySelectorAll('[id^="dropdown-"], #export-dropdown')
          .forEach((dropdown) => {
            dropdown.classList.add("hidden");
          });
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  if (loading) {
    return (
      <>
        {/* Header Skeleton */}
        <div className="mb-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded dark:bg-gray-700 w-96 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-64"></div>
        </div>

        {/* Metrics Skeleton */}
        <div className="grid grid-cols-1 gap-4 mb-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm dark:bg-gray-800 dark:border-gray-700 animate-pulse"
            >
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gray-200 rounded-full dark:bg-gray-700"></div>
                <div className="ml-4 flex-1">
                  <div className="h-6 bg-gray-200 rounded dark:bg-gray-700 w-16 mb-1"></div>
                  <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-24"></div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Table Skeleton */}
        <div className="bg-white dark:bg-gray-800 relative shadow-md sm:rounded-lg overflow-hidden">
          {/* Table Header Skeleton */}
          <div className="flex flex-col md:flex-row items-center justify-between space-y-3 md:space-y-0 md:space-x-4 p-4 animate-pulse">
            <div className="w-full md:w-1/2">
              <div className="h-10 bg-gray-200 rounded-lg dark:bg-gray-700 w-full"></div>
            </div>
            <div className="w-full md:w-auto flex space-x-3">
              <div className="h-10 bg-gray-200 rounded-lg dark:bg-gray-700 w-32"></div>
              <div className="h-10 bg-gray-200 rounded-lg dark:bg-gray-700 w-24"></div>
              <div className="h-10 bg-gray-200 rounded-lg dark:bg-gray-700 w-24"></div>
            </div>
          </div>

          {/* Table Content Skeleton */}
          <div className="overflow-x-auto">
            <table className="w-full table-auto text-sm text-left text-gray-500 dark:text-gray-400">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                <tr>
                  <th className="p-4 w-12">
                    <div className="w-4 h-4 bg-gray-200 rounded dark:bg-gray-700"></div>
                  </th>
                  {config.columns.map((_, index) => (
                    <th key={index} className="px-3 py-3">
                      <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-20"></div>
                    </th>
                  ))}
                  <th className="px-4 py-3 w-16">
                    <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-12"></div>
                  </th>
                </tr>
              </thead>
              <tbody className="animate-pulse">
                {[1, 2, 3, 4, 5].map((row) => (
                  <tr
                    key={row}
                    className="bg-white border-b dark:bg-gray-800 dark:border-gray-700"
                  >
                    <td className="w-4 p-4">
                      <div className="w-4 h-4 bg-gray-200 rounded dark:bg-gray-700"></div>
                    </td>
                    {config.columns.map((_, index) => (
                      <td key={index} className="px-3 py-4">
                        <div
                          className={`h-4 bg-gray-200 rounded dark:bg-gray-700 ${
                            index === 0
                              ? "w-24" // Contrato
                              : index === 1
                              ? "w-32" // Cliente
                              : index === 2
                              ? "w-20" // Tipo
                              : index === 3
                              ? "w-12" // Vidas
                              : index === 4
                              ? "w-24" // Valor
                              : index === 5
                              ? "w-28" // Período
                              : "w-16" // Status
                          }`}
                        ></div>
                      </td>
                    ))}
                    <td className="px-4 py-4">
                      <div className="w-8 h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Skeleton */}
          <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 dark:bg-gray-800 dark:border-gray-700 animate-pulse">
            <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-32"></div>
            <div className="flex space-x-2">
              <div className="w-8 h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
              <div className="w-8 h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
              <div className="w-8 h-8 bg-gray-200 rounded dark:bg-gray-700"></div>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white sm:text-2xl">
          {config.title}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">{config.description}</p>
      </div>

      {/* Primary Metrics */}
      <DataTableMetrics metrics={metrics} />

      {/* Detailed Metrics */}
      <DataTableDetailedMetrics
        detailedMetrics={detailedMetrics}
        showDetailedMetrics={state.showDetailedMetrics}
        onToggle={callbacks.onToggleDetailedMetrics}
      />

      {/* Main Table Container */}
      <div
        className={`${themeClasses.container} ${themeClasses.tableContainer}`}
      >
        {/* Table Header - Search and Filters */}
        <div className="flex flex-col md:flex-row items-center justify-between space-y-3 md:space-y-0 md:space-x-4 p-4">
          {/* Search */}
          <div className="w-full md:w-1/2">
            <form className="flex items-center">
              <label htmlFor="simple-search" className="sr-only">
                Search
              </label>
              <div className="relative w-full">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <svg
                    className="w-5 h-5 text-gray-500 dark:text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <input
                  type="text"
                  id="simple-search"
                  className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                  placeholder="Buscar por contrato, cliente, tipo ou status..."
                  value={state.searchTerm}
                  onChange={(e) => callbacks.onSearch(e.target.value)}
                  aria-label="Campo de busca para filtrar dados da tabela"
                  aria-describedby="search-description"
                />
                <span id="search-description" className="sr-only">
                  Digite para filtrar por número do contrato, nome do cliente,
                  tipo de contrato ou status
                </span>
              </div>
            </form>
          </div>

          {/* Actions and Filters */}
          <div className="w-full md:w-auto flex flex-col md:flex-row space-y-2 md:space-y-0 items-stretch md:items-center justify-end md:space-x-3 flex-shrink-0">
            {/* Toolbar Actions */}
            {config.actions?.toolbar?.map((action) => (
              <button
                key={action.key}
                type="button"
                onClick={() => action.action()}
                className={`flex items-center justify-center font-medium rounded-lg text-sm px-4 py-2 focus:outline-none focus:ring-4 ${
                  action.variant === "primary"
                    ? "text-white bg-blue-700 hover:bg-blue-800 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
                    : action.variant === "secondary"
                    ? "text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-gray-200 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                    : action.variant === "danger"
                    ? "text-white bg-red-700 hover:bg-red-800 focus:ring-red-300 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-900"
                    : "text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-gray-200 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                } ${action.outline ? "border" : ""}`}
              >
                {action.icon}
                <span className="ml-2">{action.label}</span>
              </button>
            ))}

            {/* Add Button */}
            {config.showAddButton !== false && (
              <button
                type="button"
                onClick={config.onAdd}
                className="flex items-center justify-center text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800"
              >
                <svg
                  className="h-3.5 w-3.5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
                {addButtonText}
              </button>
            )}

            {/* Export Dropdown */}
            <div className="relative inline-block text-left">
              <button
                onClick={() => {
                  const dropdown = document.getElementById("export-dropdown");
                  if (dropdown) {
                    dropdown.classList.toggle("hidden");
                  }
                }}
                className="flex items-center justify-center text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                type="button"
              >
                <svg
                  className="h-3.5 w-3.5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Exportar
                <svg
                  className="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              {/* Export Dropdown Menu */}
              <div
                id="export-dropdown"
                className="hidden absolute right-0 z-50 mt-2 w-44 bg-white rounded-lg shadow-lg dark:bg-gray-700 border border-gray-200 dark:border-gray-600"
              >
                <ul className="py-2 text-sm text-gray-700 dark:text-gray-200">
                  {config.export.formats.map((format) => (
                    <li key={format}>
                      <button
                        onClick={() => {
                          callbacks.onExport(format);
                          // Close dropdown
                          document
                            .getElementById("export-dropdown")
                            ?.classList.add("hidden");
                        }}
                        className="flex items-center w-full px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600"
                      >
                        {format === "csv" && (
                          <>
                            <svg
                              className="w-4 h-4 mr-2"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                              />
                            </svg>
                            Exportar CSV
                          </>
                        )}
                        {format === "json" && (
                          <>
                            <svg
                              className="w-4 h-4 mr-2"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                              />
                            </svg>
                            Exportar JSON
                          </>
                        )}
                        {format === "print" && (
                          <>
                            <svg
                              className="w-4 h-4 mr-2"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
                              />
                            </svg>
                            Imprimir
                          </>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Filters Button */}
            {config.filters && config.filters.length > 0 && (
              <button
                onClick={() => setShowFiltersModal(true)}
                className="flex items-center justify-center text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700"
                type="button"
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                Filtros
                {Object.values(state.activeFilters).some(
                  (value) =>
                    value &&
                    value !== "all" &&
                    (Array.isArray(value) ? value.length > 0 : true)
                ) && (
                  <span className="ml-2 inline-flex items-center justify-center w-4 h-4 text-xs font-bold text-white bg-red-500 rounded-full">
                    {
                      Object.values(state.activeFilters).filter(
                        (value) =>
                          value &&
                          value !== "all" &&
                          (Array.isArray(value) ? value.length > 0 : true)
                      ).length
                    }
                  </span>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Active Filters Indicator */}
        {(state as any).hasActiveFilters && (
          <div className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-sm text-blue-700 dark:text-blue-300">
                <span>🔍 Filtros ativos:</span>
                {state.searchTerm && (
                  <span className="bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded text-xs">
                    Busca: "{state.searchTerm}"
                  </span>
                )}
                {Object.entries(state.activeFilters).map(([key, value]) => {
                  if (!value || value === "all") return null;
                  const filter = config.filters.find((f) => f.key === key);
                  const option = filter?.options?.find(
                    (o) => o.value === value
                  );
                  return (
                    <span
                      key={key}
                      className="bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded text-xs"
                    >
                      {filter?.label}: {option?.label || value}
                    </span>
                  );
                })}
              </div>
              <span className="text-xs text-blue-600 dark:text-blue-400">
                {state.filteredData.length} resultado(s) encontrado(s)
              </span>
            </div>
          </div>
        )}

        {/* Selection Info */}
        {state.selectedItems.length > 0 && (
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-700 dark:text-blue-300">
                {state.selectedItems.length} item(s) selecionado(s)
              </span>
              <button
                onClick={() =>
                  callbacks.onExport(
                    "csv",
                    state.data.filter((item: any) =>
                      state.selectedItems.includes(item.id)
                    )
                  )
                }
                className="flex items-center text-sm text-blue-700 hover:text-blue-800 dark:text-blue-300"
              >
                <svg
                  className="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Exportar Selecionados (CSV)
              </button>
            </div>
          </div>
        )}

        {/* Table Content */}
        <div className="w-full">
          {/* Mobile Card View */}
          <div className="block md:hidden space-y-4">
            {state.data.map((item: any) => (
              <div
                key={item.id}
                className="mobile-card bg-white dark:bg-gray-800 p-4 rounded-lg shadow border dark:border-gray-700"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center">
                    <input
                      id={`checkbox-mobile-${item.id}`}
                      type="checkbox"
                      checked={state.selectedItems.includes(item.id)}
                      onChange={(e) =>
                        callbacks.onSelectItem(item.id, e.target.checked)
                      }
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 mr-3"
                    />
                    <span className="font-medium text-gray-900 dark:text-white">
                      {config.columns[0]?.render
                        ? config.columns[0].render(
                            item[config.columns[0].key],
                            item
                          )
                        : item[config.columns[0].key]}
                    </span>
                  </div>
                  <ActionDropdown actions={config.actions} item={item} />
                </div>
                <div className="space-y-2">
                  {config.columns.slice(1).map((column) => (
                    <div
                      key={String(column.key)}
                      className="flex justify-between items-center py-1"
                    >
                      <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                        {column.label}:
                      </span>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {column.render
                          ? column.render(item[column.key], item)
                          : item[column.key]}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Desktop Table View */}
          <div className="hidden md:block overflow-x-auto table-responsive">
            <table
              className={themeClasses.table}
              role="table"
              aria-label={`Tabela de ${config.title}`}
              aria-rowcount={state.filteredData.length}
            >
              <thead className={themeClasses.thead}>
                <tr role="row">
                  <th
                    scope="col"
                    className={`${themeClasses.headerCell} w-12`}
                    role="columnheader"
                  >
                    <div className="flex items-center">
                      <input
                        id="checkbox-all-desktop"
                        type="checkbox"
                        checked={
                          state.selectedItems.length === state.data.length &&
                          state.data.length > 0
                        }
                        onChange={(e) =>
                          callbacks.onSelectAll(e.target.checked)
                        }
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        aria-label={
                          state.selectedItems.length === state.data.length &&
                          state.data.length > 0
                            ? "Desmarcar todos os itens"
                            : "Selecionar todos os itens"
                        }
                        aria-describedby="select-all-description"
                      />
                      <span id="select-all-description" className="sr-only">
                        {state.selectedItems.length === state.data.length &&
                        state.data.length > 0
                          ? `Todos os ${state.data.length} itens estão selecionados`
                          : `Selecionar todos os ${state.data.length} itens visíveis`}
                      </span>
                      <label htmlFor="checkbox-all-desktop" className="sr-only">
                        checkbox
                      </label>
                    </div>
                  </th>
                  {config.columns.map((column, index) => (
                    <th
                      key={String(column.key)}
                      scope="col"
                      role="columnheader"
                      aria-sort={column.sortable ? "none" : undefined}
                      className={`${themeClasses.headerCell} ${
                        index === 0
                          ? "w-32" // Contrato
                          : index === 1
                          ? "w-40" // Cliente
                          : index === 2
                          ? "w-24" // Tipo
                          : index === 3
                          ? "w-20" // Vidas
                          : index === 4
                          ? "w-32" // Valor
                          : index === 5
                          ? "w-36" // Período
                          : index === 6
                          ? "w-24" // Status
                          : "w-24"
                      }`}
                    >
                      {column.label}
                    </th>
                  ))}
                  <th
                    scope="col"
                    role="columnheader"
                    className={`${themeClasses.headerCell} w-16`}
                  >
                    <span className="sr-only">
                      Ações disponíveis para cada item
                    </span>
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className={themeClasses.tbody}>
                {state.data.map((item: any) => (
                  <tr
                    key={item.id}
                    className={`${themeClasses.bodyRow} ${themeClasses.hover}`}
                  >
                    <td className={`${themeClasses.cell} w-4`}>
                      <div className="flex items-center">
                        <input
                          id={`checkbox-table-desktop-${item.id}`}
                          type="checkbox"
                          checked={state.selectedItems.includes(item.id)}
                          onChange={(e) =>
                            callbacks.onSelectItem(item.id, e.target.checked)
                          }
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 dark:focus:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        />
                        <label
                          htmlFor={`checkbox-table-desktop-${item.id}`}
                          className="sr-only"
                        >
                          checkbox
                        </label>
                      </div>
                    </td>
                    {config.columns.map((column, index) => (
                      <td
                        key={String(column.key)}
                        className={`${themeClasses.cell} ${
                          index === 0
                            ? "w-32" // Contrato
                            : index === 1
                            ? "w-40" // Cliente
                            : index === 2
                            ? "w-24" // Tipo
                            : index === 3
                            ? "w-20" // Vidas
                            : index === 4
                            ? "w-32" // Valor
                            : index === 5
                            ? "w-36" // Período
                            : index === 6
                            ? "w-24" // Status
                            : "w-24"
                        }`}
                      >
                        {column.render
                          ? column.render(item[column.key], item)
                          : item[column.key]}
                      </td>
                    ))}
                    <td className={`${themeClasses.cell} w-16`}>
                      <ActionDropdown actions={config.actions} item={item} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* No Results Message */}
            {state.filteredData.length === 0 && (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full mb-4">
                  <svg
                    className="w-8 h-8 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Nenhum{entityInfo.gender === "F" ? "a" : ""}{" "}
                  {entityInfo.singular} encontrad
                  {entityInfo.gender === "F" ? "a" : "o"}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {(state as any).hasActiveFilters
                    ? `Nenhum${
                        entityInfo.gender === "F" ? "a" : ""
                      } ${entityInfo.singular.toLowerCase()} corresponde aos filtros aplicados.`
                    : `Não há ${entityInfo.singular.toLowerCase()}s cadastrados no sistema.`}
                </p>
                {(state as any).hasActiveFilters && (
                  <button
                    onClick={callbacks.onClearFilters}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-lg hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
                  >
                    Limpar filtros
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Pagination */}
          {state.filteredData.length > 0 && (
            <nav
              className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-3 md:space-y-0 p-4"
              aria-label="Table navigation"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
                <div className="flex flex-col space-y-1">
                  <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
                    Mostrando{" "}
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {(state.currentPage - 1) * state.pageSize + 1}-
                      {Math.min(
                        state.currentPage * state.pageSize,
                        state.filteredData.length
                      )}
                    </span>{" "}
                    de{" "}
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {state.filteredData.length}
                    </span>{" "}
                    registros
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">
                    📄 Página {state.currentPage} de {state.totalPages}
                  </span>
                </div>

                {/* Page Size Selector */}
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    📄 Itens por página:
                  </span>
                  <select
                    value={state.pageSize}
                    onChange={(e) =>
                      callbacks.onPageSizeChange(Number(e.target.value))
                    }
                    className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-1.5 pr-8 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                    title="Selecionar quantidade de itens por página"
                  >
                    {(
                      config.pageSizeOptions ||
                      config.pagination?.pageSizeOptions || [10, 25, 50, 100]
                    ).map((size) => (
                      <option key={size} value={size}>
                        {size} itens
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <ul className="inline-flex items-stretch -space-x-px">
                <li>
                  <button
                    onClick={() =>
                      callbacks.onPageChange(Math.max(1, state.currentPage - 1))
                    }
                    disabled={state.currentPage === 1}
                    className="flex items-center justify-center h-full py-1.5 px-3 ml-0 text-gray-500 bg-white rounded-l-lg border border-gray-300 hover:bg-gray-100 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>
                </li>
                {Array.from({ length: state.totalPages }, (_, i) => i + 1).map(
                  (page) => (
                    <li key={page}>
                      <button
                        onClick={() => callbacks.onPageChange(page)}
                        className={`flex items-center justify-center text-sm py-2 px-3 leading-tight ${
                          state.currentPage === page
                            ? "text-blue-600 bg-blue-50 border border-gray-300 hover:bg-blue-100 hover:text-blue-700 dark:border-gray-700 dark:bg-gray-700 dark:text-white"
                            : "text-gray-500 bg-white border border-gray-300 hover:bg-gray-100 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white"
                        }`}
                      >
                        {page}
                      </button>
                    </li>
                  )
                )}
                <li>
                  <button
                    onClick={() =>
                      callbacks.onPageChange(
                        Math.min(state.totalPages, state.currentPage + 1)
                      )
                    }
                    disabled={state.currentPage === state.totalPages}
                    className="flex items-center justify-center h-full py-1.5 px-3 text-gray-500 bg-white rounded-r-lg border border-gray-300 hover:bg-gray-100 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </li>
              </ul>
            </nav>
          )}
        </div>
      </div>

      {/* Filters Modal */}
      <FiltersModal
        config={config}
        state={state}
        callbacks={callbacks}
        isOpen={showFiltersModal}
        onClose={() => setShowFiltersModal(false)}
      />
    </>
  );
}

export default DataTableTemplate;
