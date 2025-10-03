/**
 * Select2Filter - Componente avançado de seleção usando react-select
 * Oferece funcionalidades como busca, multi-seleção, e interface moderna
 */

import React from "react";
import Select, { MultiValue, SingleValue, StylesConfig } from "react-select";
import { DataTableFilter } from "../../../../types/dataTable.types";
import "./select2-overrides.css";

interface FilterComponentProps {
  filter: DataTableFilter;
  value: any;
  onChange: (value: any) => void;
  className?: string;
}

interface OptionType {
  value: string;
  label: string;
}

/**
 * Estilos simplificados que funcionam bem em ambos os temas
 */
const getCustomStyles = (
  isDark: boolean = false
): StylesConfig<OptionType> => ({
  control: (provided, state) => ({
    ...provided,
    backgroundColor: isDark ? "#374151" : "#f9fafb",
    borderColor: state.isFocused ? "#3b82f6" : isDark ? "#4b5563" : "#d1d5db",
    borderRadius: "0.5rem",
    boxShadow: state.isFocused ? "0 0 0 1px #3b82f6" : "none",
    fontSize: "14px",
    minHeight: "40px",
    "&:hover": {
      borderColor: "#3b82f6",
    },
  }),
  menu: (provided) => ({
    ...provided,
    backgroundColor: isDark ? "#374151" : "#ffffff",
    border: `1px solid ${isDark ? "#4b5563" : "#e5e7eb"}`,
    borderRadius: "0.5rem",
    zIndex: 999999, // Valor muito alto para ficar acima de qualquer modal
    position: "absolute",
    boxShadow:
      "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    maxHeight: "130px", // Altura para ~3 itens + padding
  }),
  menuList: (provided) => ({
    ...provided,
    maxHeight: "120px", // Altura máxima para exatamente 3 itens (40px cada)
    overflowY: "auto", // Scroll vertical quando necessário
    padding: "4px 0",
    "&::-webkit-scrollbar": {
      width: "4px", // Scrollbar mais fina para dropdown pequeno
    },
    "&::-webkit-scrollbar-track": {
      backgroundColor: isDark ? "#4b5563" : "#f1f5f9",
      borderRadius: "2px",
    },
    "&::-webkit-scrollbar-thumb": {
      backgroundColor: isDark ? "#6b7280" : "#cbd5e1",
      borderRadius: "2px",
      "&:hover": {
        backgroundColor: isDark ? "#9ca3af" : "#94a3b8",
      },
    },
  }),
  option: (provided, state) => ({
    ...provided,
    backgroundColor: state.isSelected
      ? "#3b82f6"
      : state.isFocused
      ? isDark
        ? "#4b5563"
        : "#eff6ff"
      : "transparent",
    color: state.isSelected
      ? "#ffffff"
      : state.isFocused
      ? isDark
        ? "#ffffff"
        : "#1d4ed8"
      : isDark
      ? "#e5e7eb"
      : "#374151",
    fontSize: "14px",
    padding: "8px 12px",
    cursor: "pointer",
  }),
  placeholder: (provided) => ({
    ...provided,
    color: isDark ? "#9ca3af" : "#6b7280",
    fontSize: "14px",
  }),
  singleValue: (provided) => ({
    ...provided,
    color: isDark ? "#ffffff" : "#111827",
    fontSize: "14px",
  }),
  multiValue: (provided) => ({
    ...provided,
    backgroundColor: "#3b82f6",
    borderRadius: "6px",
  }),
  multiValueLabel: (provided) => ({
    ...provided,
    color: "#ffffff",
    fontSize: "12px",
    padding: "2px 8px",
  }),
  multiValueRemove: (provided) => ({
    ...provided,
    color: "#ffffff",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: "#dc2626",
    },
  }),
  input: (provided) => ({
    ...provided,
    color: isDark ? "#ffffff" : "#111827",
  }),
  indicatorSeparator: (provided) => ({
    ...provided,
    backgroundColor: isDark ? "#4b5563" : "#d1d5db",
  }),
  dropdownIndicator: (provided) => ({
    ...provided,
    color: isDark ? "#9ca3af" : "#6b7280",
    "&:hover": {
      color: isDark ? "#ffffff" : "#374151",
    },
  }),
  clearIndicator: (provided) => ({
    ...provided,
    color: isDark ? "#9ca3af" : "#6b7280",
    "&:hover": {
      color: "#dc2626",
    },
  }),
});

/**
 * Hook para detectar tema escuro
 */
const useDarkMode = () => {
  const [isDark, setIsDark] = React.useState(false);

  React.useEffect(() => {
    const checkDarkMode = () => {
      const htmlElement = document.documentElement;
      setIsDark(htmlElement.classList.contains("dark"));
    };

    // Verificar inicialmente
    checkDarkMode();

    // Observer para mudanças na classe dark
    const observer = new MutationObserver(checkDarkMode);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => observer.disconnect();
  }, []);

  return isDark;
};

/**
 * Select2 Filter para seleção simples
 */
export const Select2Filter: React.FC<FilterComponentProps> = ({
  filter,
  value,
  onChange,
  className = "",
}) => {
  const isDark = useDarkMode();
  const options: OptionType[] =
    filter.options?.map((option) => ({
      value: option.value,
      label: option.label,
    })) || [];

  const selectedOption =
    options.find((option) => option.value === value) || null;

  // Debug logs
  React.useEffect(() => {
    console.log("Select2Filter Debug:", {
      filterLabel: filter.label,
      filterType: filter.type,
      options: options,
      currentValue: value,
      selectedOption: selectedOption,
      isDark: isDark,
    });
  }, [filter, value, selectedOption, isDark, options]);

  const handleChange = (selectedOption: SingleValue<OptionType>) => {
    console.log("Select2Filter onChange:", selectedOption);
    onChange(selectedOption ? selectedOption.value : null);
  };

  return (
    <div className={className}>
      <Select<OptionType>
        options={options}
        value={selectedOption}
        onChange={handleChange}
        placeholder={
          filter.placeholder || `Selecionar ${filter.label.toLowerCase()}...`
        }
        isSearchable={true}
        isClearable={true}
        styles={getCustomStyles(isDark)}
        className="react-select-container"
        classNamePrefix="react-select"
        menuPortalTarget={null} // Renderizar dentro do container pai
        menuPlacement="bottom"
        menuShouldScrollIntoView={true}
        menuPosition="absolute"
        maxMenuHeight={120} // Altura máxima para 3 itens
        noOptionsMessage={() => "Nenhuma opção encontrada"}
        loadingMessage={() => "Carregando..."}
        aria-label={`Filtrar por ${filter.label}`}
      />
    </div>
  );
};

/**
 * Select2 Filter para multi-seleção
 */
export const Select2MultiFilter: React.FC<FilterComponentProps> = ({
  filter,
  value = [],
  onChange,
  className = "",
}) => {
  const isDark = useDarkMode();
  const options: OptionType[] =
    filter.options?.map((option) => ({
      value: option.value,
      label: option.label,
    })) || [];

  const selectedValues = Array.isArray(value) ? value : [];
  const selectedOptions = options.filter((option) =>
    selectedValues.includes(option.value)
  );

  const handleChange = (selectedOptions: MultiValue<OptionType>) => {
    const values = selectedOptions.map((option) => option.value);
    onChange(values);
  };

  return (
    <div className={className}>
      <Select<OptionType, true>
        options={options}
        value={selectedOptions}
        onChange={handleChange}
        placeholder={
          filter.placeholder || `Selecionar ${filter.label.toLowerCase()}...`
        }
        isSearchable={true}
        isMulti={true}
        isClearable={true}
        closeMenuOnSelect={false}
        styles={getCustomStyles(isDark)}
        className="react-select-container"
        classNamePrefix="react-select"
        menuPortalTarget={null} // Renderizar dentro do container pai
        menuPlacement="bottom"
        menuShouldScrollIntoView={true}
        menuPosition="absolute"
        maxMenuHeight={120} // Altura máxima para 3 itens
        noOptionsMessage={() => "Nenhuma opção encontrada"}
        loadingMessage={() => "Carregando..."}
        aria-label={`Filtrar por ${filter.label} (múltipla seleção)`}
      />
      {selectedOptions.length > 0 && (
        <div className="mt-1 text-xs text-blue-600 dark:text-blue-400">
          {selectedOptions.length} item(s) selecionado(s)
        </div>
      )}
    </div>
  );
};

export default { Select2Filter, Select2MultiFilter };
