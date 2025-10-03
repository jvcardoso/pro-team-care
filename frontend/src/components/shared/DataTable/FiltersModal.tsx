/**
 * Filters Modal - Modal para organizar todos os filtros da tabela
 */

import React from "react";
import {
  DataTableConfig,
  BaseEntity,
  DataTableState,
  DataTableCallbacks,
} from "../../../types/dataTable.types";
import { FilterRenderer } from "./filters/FilterComponents";

interface FiltersModalProps<T extends BaseEntity = any> {
  config: DataTableConfig<T>;
  state: DataTableState;
  callbacks: DataTableCallbacks<T>;
  isOpen: boolean;
  onClose: () => void;
}

export function FiltersModal<T extends BaseEntity = any>({
  config,
  state,
  callbacks,
  isOpen,
  onClose,
}: FiltersModalProps<T>) {
  const modalRef = React.useRef<HTMLDivElement>(null);

  if (!isOpen) return null;

  const hasActiveFilters =
    state.searchTerm !== "" ||
    Object.values(state.activeFilters).some(
      (value) =>
        value &&
        value !== "all" &&
        (Array.isArray(value) ? value.length > 0 : true)
    );

  const handleClearAll = () => {
    callbacks.onClearFilters();
  };

  const handleApplyAndClose = () => {
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        {/* Modal */}
        <div
          ref={modalRef}
          className="filters-modal inline-block align-bottom bg-white rounded-lg text-left shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full dark:bg-gray-800"
          style={{ overflow: "visible" }}
        >
          {/* Header */}
          <div className="bg-white px-6 pt-6 pb-4 border-b border-gray-200 dark:bg-gray-800 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg leading-6 font-semibold text-gray-900 dark:text-white">
                  🔍 Filtros Avançados
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  Configure os filtros para refinar sua busca
                </p>
              </div>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Fechar modal de filtros"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Body */}
          <div
            className="bg-white px-6 py-6 dark:bg-gray-800"
            style={{
              maxHeight: "24rem",
              overflowY: "auto",
              overflowX: "visible",
            }}
          >
            {/* Search Section */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                🔎 Busca Geral
              </label>
              <div className="relative">
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
                  value={state.searchTerm}
                  onChange={(e) => callbacks.onSearch(e.target.value)}
                  className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-3 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                  placeholder="Buscar por contrato, cliente, tipo ou status..."
                />
              </div>
              {state.searchTerm && (
                <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                  Buscando por: "{state.searchTerm}"
                </p>
              )}
            </div>

            {/* Filters Grid */}
            {config.filters.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                  🎛️ Filtros Específicos
                </h4>
                <div
                  className="filters-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                  style={{ overflow: "visible" }}
                >
                  {config.filters.map((filter) => (
                    <div key={filter.key} className="space-y-2">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        {filter.label}
                      </label>
                      <FilterRenderer
                        filter={filter}
                        value={state.activeFilters[filter.key]}
                        onChange={(value) =>
                          callbacks.onFilter(filter.key, value)
                        }
                        className="w-full"
                      />
                      {/* Show active filter indicator */}
                      {state.activeFilters[filter.key] &&
                        state.activeFilters[filter.key] !== "all" && (
                          <div className="flex items-center space-x-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-xs text-green-600 dark:text-green-400">
                              Filtro ativo
                            </span>
                          </div>
                        )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Active Filters Summary */}
            {hasActiveFilters && (
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                  📋 Filtros Ativos
                </h4>
                <div className="space-y-1">
                  {state.searchTerm && (
                    <div className="text-xs text-blue-700 dark:text-blue-300">
                      • Busca: "{state.searchTerm}"
                    </div>
                  )}
                  {Object.entries(state.activeFilters).map(([key, value]) => {
                    if (!value || value === "all") return null;

                    const filter = config.filters.find((f) => f.key === key);
                    if (!filter) return null;

                    let displayValue = "";
                    if (Array.isArray(value)) {
                      displayValue = `${value.length} selecionado(s)`;
                    } else if (typeof value === "object" && value !== null) {
                      const objValue = value as any;
                      if (
                        objValue.min !== undefined ||
                        objValue.max !== undefined
                      ) {
                        displayValue = `${objValue.min || "Min"} - ${
                          objValue.max || "Max"
                        }`;
                      } else if (objValue.start || objValue.end) {
                        displayValue = `${objValue.start || "Início"} até ${
                          objValue.end || "Fim"
                        }`;
                      }
                    } else {
                      displayValue = String(value);
                    }

                    return (
                      <div
                        key={key}
                        className="text-xs text-blue-700 dark:text-blue-300 flex items-center justify-between"
                      >
                        <span>
                          • {filter.label}: {displayValue}
                        </span>
                        <button
                          onClick={() => callbacks.onFilter(key, null)}
                          className="ml-2 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-200"
                          title="Remover filtro"
                        >
                          ✕
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 sm:flex sm:flex-row-reverse sm:space-x-reverse sm:space-x-3 dark:bg-gray-700">
            <button
              onClick={handleApplyAndClose}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm transition-colors"
            >
              ✅ Aplicar Filtros
            </button>

            {hasActiveFilters && (
              <button
                onClick={handleClearAll}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm transition-colors dark:bg-gray-600 dark:text-white dark:border-gray-500 dark:hover:bg-gray-500"
              >
                🧹 Limpar Todos
              </button>
            )}

            <button
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:mt-0 sm:w-auto sm:text-sm transition-colors dark:bg-gray-600 dark:text-white dark:border-gray-500 dark:hover:bg-gray-500"
            >
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FiltersModal;
