import React, { useState, useEffect } from 'react';
import { User, Check, X } from 'lucide-react';
import { formatCPF } from '../../utils/formatters';
import { removeNonNumeric, validateCPF } from '../../utils/validators';

const InputCPF = ({
  label = "CPF",
  value = '',
  onChange,
  placeholder = "000.000.000-00",
  required = false,
  disabled = false,
  error = '',
  className = '',
  showValidation = true,
  showIcon = true,
  ...props
}) => {
  const [formattedValue, setFormattedValue] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      const formatted = formatCPF(value);
      setFormattedValue(formatted);
      
      if (showValidation && value) {
        validateInput(value);
      }
    }
  }, [value, showValidation]);

  const validateInput = (inputValue) => {
    const cleanValue = removeNonNumeric(inputValue);
    
    if (!cleanValue && required) {
      setIsValid(false);
      setValidationMessage('CPF é obrigatório');
      return false;
    }
    
    if (cleanValue && cleanValue.length < 11) {
      setIsValid(false);
      setValidationMessage('CPF deve ter 11 dígitos');
      return false;
    }
    
    if (cleanValue && !validateCPF(cleanValue)) {
      setIsValid(false);
      setValidationMessage('CPF inválido');
      return false;
    }
    
    setIsValid(true);
    setValidationMessage('');
    return true;
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbersOnly = removeNonNumeric(inputValue);
    
    // Limitar a 11 dígitos
    const limitedNumbers = numbersOnly.slice(0, 11);
    const formatted = formatCPF(limitedNumbers);
    
    setFormattedValue(formatted);
    setIsDirty(true);
    
    // Validação em tempo real apenas após o primeiro blur
    if (showValidation && isDirty) {
      validateInput(limitedNumbers);
    }
    
    // Callback para o componente pai
    if (onChange) {
      onChange({
        target: {
          name: e.target.name,
          value: limitedNumbers, // Valor limpo para o backend
        },
        formatted: formatted,
        isValid: validateInput(limitedNumbers),
        rawValue: limitedNumbers
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
      validateInput(removeNonNumeric(formattedValue));
    }
    
    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const getInputClasses = () => {
    const baseClasses = "w-full px-3 py-2 border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors";
    
    // Ajustar padding se houver ícone
    const paddingClasses = showIcon ? "pl-10" : "px-3";
    
    let borderColor = "border-border";
    
    if (error || (!isValid && showValidation && isDirty)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (isValid && formattedValue && showValidation && isDirty && formattedValue.length === 14) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }
    
    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";
    
    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError = error || (showValidation && !isValid && isDirty ? validationMessage : '');
  const isComplete = formattedValue.length === 14; // 000.000.000-00

  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-foreground">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        {/* Ícone de usuário */}
        {showIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3">
            <User className="h-4 w-4 text-muted-foreground" />
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
          autoComplete="off"
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
      {displayError && (
        <p className="text-sm text-red-600">{displayError}</p>
      )}
      
      {/* Mensagem de ajuda */}
      {!displayError && formattedValue && showValidation && isValid && isDirty && isComplete && (
        <p className="text-xs text-muted-foreground">
          CPF válido
        </p>
      )}
      
      {!displayError && !formattedValue && isFocused && (
        <p className="text-xs text-muted-foreground">
          Digite o CPF com 11 dígitos
        </p>
      )}
      
      {!displayError && formattedValue && !isComplete && isDirty && (
        <p className="text-xs text-muted-foreground">
          {11 - removeNonNumeric(formattedValue).length} dígitos restantes
        </p>
      )}
    </div>
  );
};

export default InputCPF;