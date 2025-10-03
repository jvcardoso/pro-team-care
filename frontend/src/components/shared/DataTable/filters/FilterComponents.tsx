/**
 * Filter Components - Componentes específicos para diferentes tipos de filtros
 */

import React from "react";
import { DataTableFilter } from "../../../../types/dataTable.types";
import { Select2Filter, Select2MultiFilter } from "./Select2Filter";

interface FilterComponentProps {
  filter: DataTableFilter;
  value: any;
  onChange: (value: any) => void;
  className?: string;
}

/**
 * Filtro Select Simples
 */
export const SelectFilter: React.FC<FilterComponentProps> = ({
  filter,
  value,
  onChange,
  className = "",
}) => (
  <select
    value={value || "all"}
    onChange={(e) => onChange(e.target.value)}
    className={`bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white ${className}`}
    aria-label={`Filtrar por ${filter.label}`}
  >
    {filter.options?.map((option) => (
      <option key={option.value} value={option.value}>
        {option.label}
      </option>
    ))}
  </select>
);

/**
 * Filtro MultiSelect com Checkboxes
 */
export const MultiSelectFilter: React.FC<FilterComponentProps> = ({
  filter,
  value = [],
  onChange,
  className = "",
}) => {
  const selectedValues = Array.isArray(value) ? value : [];

  const handleChange = (optionValue: string, checked: boolean) => {
    const newValues = checked
      ? [...selectedValues, optionValue]
      : selectedValues.filter((v) => v !== optionValue);
    onChange(newValues);
  };

  return (
    <div className={`relative inline-block text-left ${className}`}>
      <div className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus-within:ring-blue-500 focus-within:border-blue-500 p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
        <div className="max-h-32 overflow-y-auto space-y-1">
          {filter.options?.map((option) => (
            <label
              key={option.value}
              className="flex items-center space-x-2 text-xs cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 p-1 rounded"
            >
              <input
                type="checkbox"
                checked={selectedValues.includes(option.value)}
                onChange={(e) => handleChange(option.value, e.target.checked)}
                className="w-3 h-3 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-1 dark:bg-gray-700 dark:border-gray-600"
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
        {selectedValues.length > 0 && (
          <div className="mt-1 text-xs text-blue-600 dark:text-blue-400">
            {selectedValues.length} selecionado(s)
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Filtro de Busca/Pesquisa
 */
export const SearchFilter: React.FC<FilterComponentProps> = ({
  filter,
  value,
  onChange,
  className = "",
}) => (
  <input
    type="text"
    value={value || ""}
    onChange={(e) => onChange(e.target.value)}
    placeholder={
      filter.placeholder || `Buscar ${filter.label.toLowerCase()}...`
    }
    className={`bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white ${className}`}
    aria-label={`Buscar por ${filter.label}`}
  />
);

/**
 * Filtro de Data
 */
export const DateFilter: React.FC<FilterComponentProps> = ({
  filter,
  value,
  onChange,
  className = "",
}) => (
  <input
    type="date"
    value={value || ""}
    onChange={(e) => onChange(e.target.value)}
    className={`bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white ${className}`}
    aria-label={`Filtrar por ${filter.label}`}
  />
);

/**
 * Filtro de Intervalo de Datas
 */
export const DateRangeFilter: React.FC<FilterComponentProps> = ({
  filter,
  value = {},
  onChange,
  className = "",
}) => {
  const { start = "", end = "" } = value;

  const handleStartChange = (newStart: string) => {
    onChange({ ...value, start: newStart });
  };

  const handleEndChange = (newEnd: string) => {
    onChange({ ...value, end: newEnd });
  };

  return (
    <div className={`flex space-x-2 ${className}`}>
      <input
        type="date"
        value={start}
        onChange={(e) => handleStartChange(e.target.value)}
        placeholder="Data inicial"
        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
        aria-label={`${filter.label} - Data inicial`}
      />
      <span className="flex items-center text-gray-500 dark:text-gray-400">
        até
      </span>
      <input
        type="date"
        value={end}
        onChange={(e) => handleEndChange(e.target.value)}
        placeholder="Data final"
        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
        aria-label={`${filter.label} - Data final`}
      />
    </div>
  );
};

/**
 * Filtro Numérico
 */
export const NumberFilter: React.FC<FilterComponentProps> = ({
  filter,
  value,
  onChange,
  className = "",
}) => (
  <input
    type="number"
    value={value || ""}
    onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
    placeholder={filter.placeholder || `${filter.label}...`}
    min={filter.min}
    max={filter.max}
    step={filter.step || 1}
    className={`bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white ${className}`}
    aria-label={`Filtrar por ${filter.label}`}
  />
);

/**
 * Filtro de Intervalo Numérico
 */
export const RangeFilter: React.FC<FilterComponentProps> = ({
  filter,
  value = {},
  onChange,
  className = "",
}) => {
  const { min = "", max = "" } = value;

  const handleMinChange = (newMin: string) => {
    const numValue = newMin ? Number(newMin) : null;
    onChange({ ...value, min: numValue });
  };

  const handleMaxChange = (newMax: string) => {
    const numValue = newMax ? Number(newMax) : null;
    onChange({ ...value, max: numValue });
  };

  return (
    <div className={`flex space-x-2 ${className}`}>
      <input
        type="number"
        value={min || ""}
        onChange={(e) => handleMinChange(e.target.value)}
        placeholder="Mín"
        min={filter.min}
        max={filter.max}
        step={filter.step || 1}
        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white w-20"
        aria-label={`${filter.label} - Valor mínimo`}
      />
      <span className="flex items-center text-gray-500 dark:text-gray-400">
        -
      </span>
      <input
        type="number"
        value={max || ""}
        onChange={(e) => handleMaxChange(e.target.value)}
        placeholder="Máx"
        min={filter.min}
        max={filter.max}
        step={filter.step || 1}
        className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white w-20"
        aria-label={`${filter.label} - Valor máximo`}
      />
    </div>
  );
};

/**
 * Componente principal que renderiza o filtro correto baseado no tipo
 */
export const FilterRenderer: React.FC<FilterComponentProps> = (props) => {
  const { filter } = props;

  switch (filter.type) {
    case "select":
      // Use Select2 para melhor UX
      return <Select2Filter {...props} />;
    case "multiselect":
      // Use Select2Multi para multi-seleção
      return <Select2MultiFilter {...props} />;
    case "search":
      return <SearchFilter {...props} />;
    case "date":
      return <DateFilter {...props} />;
    case "daterange":
      return <DateRangeFilter {...props} />;
    case "number":
      return <NumberFilter {...props} />;
    case "range":
      return <RangeFilter {...props} />;
    default:
      // Fallback para Select2
      return <Select2Filter {...props} />;
  }
};

export default FilterRenderer;
