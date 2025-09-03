import React, { useState, useEffect } from "react";
import { Calendar, Check, X, Star } from "lucide-react";
import { formatDate, parseDate } from "../../utils/formatters";
import { removeNonNumeric } from "../../utils/validators";

const InputDate = ({
  label = "Data",
  value = "",
  onChange,
  placeholder = "dd/mm/aaaa",
  required = false,
  disabled = false,
  error = "",
  className = "",
  showValidation = true,
  showIcon = true,
  minDate = null,
  maxDate = null,
  allowFuture = true,
  allowPast = true,
  ...props
}) => {
  const [formattedValue, setFormattedValue] = useState("");
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      let formatted = "";

      if (value) {
        // Se valor é string no formato YYYY-MM-DD, converter para DD/MM/YYYY
        if (typeof value === "string" && value.includes("-")) {
          const parts = value.split("-");
          if (parts.length === 3) {
            formatted = `${parts[2]}/${parts[1]}/${parts[0]}`;
          }
        } else {
          // Se já está em formato brasileiro ou é apenas números
          formatted = formatDate(value);
        }
      }

      setFormattedValue(formatted);

      if (showValidation && formatted) {
        validateInput(formatted);
      }
    }
  }, [value, showValidation]);

  const validateInput = (inputValue) => {
    const cleanValue = removeNonNumeric(inputValue);

    if (!cleanValue && required) {
      setIsValid(false);
      setValidationMessage("Data é obrigatória");
      return false;
    }

    if (cleanValue && cleanValue.length < 8) {
      setIsValid(false);
      setValidationMessage("Data deve ter 8 dígitos");
      return false;
    }

    if (cleanValue && cleanValue.length === 8) {
      // Validar formato DD/MM/YYYY
      const day = parseInt(cleanValue.substring(0, 2));
      const month = parseInt(cleanValue.substring(2, 4));
      const year = parseInt(cleanValue.substring(4, 8));

      // Validações básicas
      if (day < 1 || day > 31) {
        setIsValid(false);
        setValidationMessage("Dia inválido (1-31)");
        return false;
      }

      if (month < 1 || month > 12) {
        setIsValid(false);
        setValidationMessage("Mês inválido (1-12)");
        return false;
      }

      if (year < 1900 || year > 2100) {
        setIsValid(false);
        setValidationMessage("Ano inválido (1900-2100)");
        return false;
      }

      // Criar data e verificar se é válida
      const date = new Date(year, month - 1, day);
      if (
        date.getDate() !== day ||
        date.getMonth() !== month - 1 ||
        date.getFullYear() !== year
      ) {
        setIsValid(false);
        setValidationMessage("Data inválida");
        return false;
      }

      // Validar se permite datas passadas
      if (!allowPast) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (date < today) {
          setIsValid(false);
          setValidationMessage("Data não pode ser no passado");
          return false;
        }
      }

      // Validar se permite datas futuras
      if (!allowFuture) {
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        if (date > today) {
          setIsValid(false);
          setValidationMessage("Data não pode ser no futuro");
          return false;
        }
      }

      // Validar data mínima
      if (minDate) {
        const minDateObj = new Date(minDate);
        if (date < minDateObj) {
          setIsValid(false);
          setValidationMessage(
            `Data mínima: ${minDateObj.toLocaleDateString("pt-BR")}`
          );
          return false;
        }
      }

      // Validar data máxima
      if (maxDate) {
        const maxDateObj = new Date(maxDate);
        if (date > maxDateObj) {
          setIsValid(false);
          setValidationMessage(
            `Data máxima: ${maxDateObj.toLocaleDateString("pt-BR")}`
          );
          return false;
        }
      }
    }

    setIsValid(true);
    setValidationMessage("");
    return true;
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbersOnly = removeNonNumeric(inputValue);

    // Limitar a 8 dígitos
    const limitedNumbers = numbersOnly.slice(0, 8);
    const formatted = formatDate(limitedNumbers);

    setFormattedValue(formatted);
    setIsDirty(true);

    // Validação em tempo real apenas após o primeiro blur ou quando completo
    if (showValidation && (isDirty || limitedNumbers.length === 8)) {
      validateInput(formatted);
    }

    // Callback para o componente pai
    if (onChange) {
      const isoDate = limitedNumbers.length === 8 ? parseDate(formatted) : "";

      onChange({
        target: {
          name: e.target.name,
          value: isoDate, // Valor ISO para o backend (YYYY-MM-DD)
        },
        formatted: formatted,
        isoDate: isoDate,
        isValid: validateInput(formatted),
        rawValue: limitedNumbers,
      });
    }
  };

  const handleFocus = (e) => {
    setIsFocused(true);
    if (props.onFocus) {
      props.onFocus(e);
    }
  };

  const handleBlur = (e) => {
    setIsFocused(false);
    setIsDirty(true);

    // Validação final no blur
    if (showValidation) {
      validateInput(formattedValue);
    }

    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const getInputClasses = () => {
    const baseClasses =
      "w-full px-3 py-2 border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors";

    // Ajustar padding se houver ícone
    const paddingClasses = showIcon ? "pl-10" : "px-3";

    let borderColor = "border-border";

    if (error || (!isValid && showValidation && isDirty)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (
      isValid &&
      formattedValue &&
      showValidation &&
      formattedValue.length === 10
    ) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }

    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";

    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError =
    error || (showValidation && !isValid && isDirty ? validationMessage : "");
  const isComplete = formattedValue.length === 10; // dd/mm/aaaa

  return (
    <div className="space-y-1">
      <label className="flex items-center text-sm font-medium text-foreground">
        {label}
        {required && (
          <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />
        )}
      </label>

      <div className="relative">
        {/* Ícone de calendário */}
        {showIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3">
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </div>
        )}

        <input
          type="text"
          value={formattedValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={getInputClasses()}
          autoComplete="bday"
          inputMode="numeric"
          {...props}
        />

        {/* Indicador de validação visual */}
        {showValidation && formattedValue && isDirty && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {isValid && isComplete ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : !isValid ? (
              <X className="h-4 w-4 text-red-500" />
            ) : null}
          </div>
        )}
      </div>

      {/* Mensagens de erro */}
      {displayError && <p className="text-sm text-red-600">{displayError}</p>}

      {/* Mensagem de ajuda */}
      {!displayError &&
        formattedValue &&
        showValidation &&
        isValid &&
        isDirty &&
        isComplete && (
          <p className="text-xs text-muted-foreground">Data válida</p>
        )}

      {!displayError && !formattedValue && isFocused && (
        <p className="text-xs text-muted-foreground">
          Digite a data no formato dd/mm/aaaa
        </p>
      )}

      {!displayError && formattedValue && !isComplete && isDirty && (
        <p className="text-xs text-muted-foreground">
          {8 - removeNonNumeric(formattedValue).length} dígitos restantes
        </p>
      )}

      {/* Dicas de range */}
      {!displayError &&
        !formattedValue &&
        !isFocused &&
        (minDate || maxDate) && (
          <p className="text-xs text-muted-foreground">
            {minDate && maxDate
              ? `Data entre ${new Date(minDate).toLocaleDateString(
                  "pt-BR"
                )} e ${new Date(maxDate).toLocaleDateString("pt-BR")}`
              : minDate
              ? `Data mínima: ${new Date(minDate).toLocaleDateString("pt-BR")}`
              : `Data máxima: ${new Date(maxDate).toLocaleDateString("pt-BR")}`}
          </p>
        )}
    </div>
  );
};

export default InputDate;
