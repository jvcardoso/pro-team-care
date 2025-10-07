import React, { useState, useEffect, useRef } from "react";
import { DollarSign, Check, AlertCircle } from "lucide-react";
import {
  formatCurrencyDisplay,
  parseCurrencyRobust,
  validateCurrency,
} from "../../utils/formatters";

interface CurrencyInputProps {
  label?: string;
  value?: number | string | null;
  onChange?: (event: {
    target: { name?: string; value: number | null };
    formatted: string;
    numericValue: number | null;
    isValid: boolean;
  }) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  className?: string;
  name?: string;
  min?: number;
  max?: number;
  allowNegative?: boolean;
  showValidation?: boolean;
  showIcon?: boolean;
  leftIcon?: React.ReactNode;
  autoFocus?: boolean;
  id?: string;
}

const CurrencyInput: React.FC<CurrencyInputProps> = ({
  label = "Valor",
  value = null,
  onChange,
  onBlur,
  onFocus,
  placeholder = "R$ 0,00",
  required = false,
  disabled = false,
  error = "",
  className = "",
  name,
  min = 0,
  max = null,
  allowNegative = false,
  showValidation = true,
  showIcon = true,
  leftIcon,
  autoFocus = false,
  id,
  ...props
}) => {
  const [displayValue, setDisplayValue] = useState<string>("");
  const [internalError, setInternalError] = useState<string>("");
  const [isValid, setIsValid] = useState<boolean>(true);
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const [isDirty, setIsDirty] = useState<boolean>(false);

  const inputRef = useRef<HTMLInputElement>(null);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== null && value !== undefined && value !== "") {
      const numValue =
        typeof value === "string" ? parseCurrencyRobust(value) : value;
      setDisplayValue(formatCurrencyDisplay(numValue));
    } else {
      setDisplayValue("");
    }
  }, [value]);

  // Auto-focus se solicitado
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  const validateValue = (numericValue: number) => {
    const validation = validateCurrency(numericValue, {
      min,
      max,
      required,
      allowNegative,
    });

    setIsValid(validation.isValid);
    setInternalError(validation.error);
    return validation.isValid;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    setIsDirty(true);

    // Se o campo estiver vazio
    if (!inputValue || inputValue === "") {
      setDisplayValue("");
      const isValidEmpty = !required; // Campo vazio é válido se não for obrigatório

      if (onChange) {
        onChange({
          target: { name, value: null },
          formatted: "",
          numericValue: null,
          isValid: isValidEmpty,
        });
      }
      return;
    }

    // Permitir apenas números, vírgula e ponto
    const cleanInput = inputValue.replace(/[^0-9,.]/g, "");

    // Se não há números, limpar
    if (!/\d/.test(cleanInput)) {
      setDisplayValue("");
      const isValidEmpty = !required; // Campo vazio é válido se não for obrigatório

      if (onChange) {
        onChange({
          target: { name, value: null },
          formatted: "",
          numericValue: null,
          isValid: isValidEmpty,
        });
      }
      return;
    }

    // Parse do valor numérico
    const numericValue = parseCurrencyRobust(cleanInput);

    // Formatar para exibição
    const formatted = formatCurrencyDisplay(numericValue);
    setDisplayValue(formatted);

    // Validação
    const isValidValue = showValidation ? validateValue(numericValue) : true;

    // Callback para o componente pai
    if (onChange) {
      onChange({
        target: { name, value: numericValue },
        formatted,
        numericValue,
        isValid: isValidValue,
      });
    }
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true);
    if (onFocus) {
      onFocus(e);
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false);
    setIsDirty(true);

    // Validação final no blur
    if (showValidation && displayValue) {
      const numericValue = parseCurrencyRobust(displayValue);
      validateValue(numericValue);
    }

    if (onBlur) {
      onBlur(e);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Permitir teclas de controle
    const controlKeys = [
      "Backspace",
      "Delete",
      "Tab",
      "Escape",
      "Enter",
      "Home",
      "End",
      "ArrowLeft",
      "ArrowRight",
      "ArrowUp",
      "ArrowDown",
    ];

    if (controlKeys.includes(e.key)) {
      return;
    }

    // Permitir Ctrl+A, Ctrl+C, Ctrl+V, etc.
    if (e.ctrlKey || e.metaKey) {
      return;
    }

    // Permitir números, vírgula e ponto
    if (!/[0-9,.]/.test(e.key)) {
      e.preventDefault();
    }
  };

  // Classes CSS
  const getInputClasses = () => {
    const baseClasses =
      "w-full py-2 border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors";

    // Padding baseado na presença de ícones
    const iconToShow =
      leftIcon || (showIcon ? <DollarSign className="h-4 w-4" /> : null);
    const paddingClasses = iconToShow ? "pl-10 pr-3" : "px-3";

    // Cores da borda baseadas no estado
    let borderColor = "border-border";

    if (error || (showValidation && !isValid && isDirty && internalError)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (showValidation && isValid && displayValue && isDirty) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }

    const disabledClasses = disabled
      ? "opacity-50 cursor-not-allowed bg-muted"
      : "";

    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError =
    error || (showValidation && !isValid && isDirty ? internalError : "");
  const hasIcon = leftIcon || showIcon;

  return (
    <div className="space-y-1">
      {/* Label */}
      {label && (
        <label
          htmlFor={id || name}
          className="block text-sm font-medium text-foreground"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        {/* Ícone à esquerda */}
        {hasIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <div className="text-muted-foreground">
              {leftIcon || <DollarSign className="h-4 w-4" />}
            </div>
          </div>
        )}

        <input
          ref={inputRef}
          type="text"
          id={id || name}
          name={name}
          value={displayValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={getInputClasses()}
          autoComplete="off"
          inputMode="decimal"
          {...props}
        />

        {/* Indicador de validação */}
        {showValidation && displayValue && isDirty && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            {isValid ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-500" />
            )}
          </div>
        )}
      </div>

      {/* Mensagem de erro */}
      {displayError && <p className="text-sm text-red-600">{displayError}</p>}

      {/* Dicas de ajuda */}
      {!displayError && (
        <>
          {/* Valor válido */}
          {showValidation && isValid && displayValue && isDirty && (
            <p className="text-xs text-green-600">
              Valor válido: {displayValue}
            </p>
          )}

          {/* Dicas durante o foco */}
          {isFocused && !displayValue && (
            <p className="text-xs text-muted-foreground">
              Digite o valor em reais. Ex: 1234,56 ou 1.234,56
            </p>
          )}

          {/* Limites quando não focado e vazio */}
          {!isFocused && !displayValue && (min !== null || max !== null) && (
            <p className="text-xs text-muted-foreground">
              {min !== null && max !== null
                ? `Valor entre ${formatCurrencyDisplay(
                    min
                  )} e ${formatCurrencyDisplay(max)}`
                : min !== null
                ? `Valor mínimo: ${formatCurrencyDisplay(min)}`
                : `Valor máximo: ${formatCurrencyDisplay(max)}`}
            </p>
          )}
        </>
      )}
    </div>
  );
};

export default CurrencyInput;
