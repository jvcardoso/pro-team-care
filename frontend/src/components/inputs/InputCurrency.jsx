import React, { useState, useEffect } from 'react';
import { DollarSign, Check, Star } from 'lucide-react';
import { formatCurrency, parseCurrency } from '../../utils/formatters';

const InputCurrency = ({
  label = "Valor",
  value = '',
  onChange,
  placeholder = "R$ 0,00",
  required = false,
  disabled = false,
  error = '',
  className = '',
  showValidation = false,
  showIcon = true,
  minValue = 0,
  maxValue = null,
  allowNegative = false,
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
      const numValue = typeof value === 'string' ? parseFloat(value) : value;
      if (!isNaN(numValue)) {
        // Converter número para centavos e formatar
        const formatted = formatCurrency((numValue * 100).toString());
        setFormattedValue(formatted);
        
        if (showValidation && value) {
          validateInput(numValue);
        }
      } else {
        setFormattedValue('');
      }
    }
  }, [value, showValidation]);

  const validateInput = (numValue) => {
    if (required && (!numValue || numValue === 0)) {
      setIsValid(false);
      setValidationMessage('Valor é obrigatório');
      return false;
    }
    
    if (!allowNegative && numValue < 0) {
      setIsValid(false);
      setValidationMessage('Valor não pode ser negativo');
      return false;
    }
    
    if (minValue !== null && numValue < minValue) {
      setIsValid(false);
      setValidationMessage(`Valor mínimo: ${formatCurrency((minValue * 100).toString())}`);
      return false;
    }
    
    if (maxValue !== null && numValue > maxValue) {
      setIsValid(false);
      setValidationMessage(`Valor máximo: ${formatCurrency((maxValue * 100).toString())}`);
      return false;
    }
    
    setIsValid(true);
    setValidationMessage('');
    return true;
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    
    // Permitir apenas números, vírgula e ponto
    const cleanedInput = inputValue.replace(/[^0-9,]/g, '');
    
    // Converter para centavos para processamento
    const numbersOnly = cleanedInput.replace(/\D/g, '');
    if (numbersOnly === '') {
      setFormattedValue('');
      setIsDirty(true);
      
      if (onChange) {
        onChange({
          target: {
            name: e.target.name,
            value: 0,
          },
          formatted: '',
          numericValue: 0,
          isValid: validateInput(0)
        });
      }
      return;
    }
    
    // Formatar valor
    const formatted = formatCurrency(numbersOnly);
    setFormattedValue(formatted);
    setIsDirty(true);
    
    // Converter para número decimal
    const numericValue = parseCurrency(formatted);
    
    // Validação
    if (showValidation) {
      validateInput(numericValue);
    }
    
    // Callback para o componente pai
    if (onChange) {
      onChange({
        target: {
          name: e.target.name,
          value: numericValue, // Valor numérico para o backend
        },
        formatted: formatted,
        numericValue: numericValue,
        isValid: validateInput(numericValue)
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
      const numericValue = parseCurrency(formattedValue);
      validateInput(numericValue);
    }
    
    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const handleKeyDown = (e) => {
    // Permitir teclas de controle
    const controlKeys = [
      'Backspace', 'Delete', 'Tab', 'Escape', 'Enter',
      'Home', 'End', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'
    ];
    
    if (controlKeys.includes(e.key)) {
      return;
    }
    
    // Permitir Ctrl+A, Ctrl+C, Ctrl+V, etc.
    if (e.ctrlKey || e.metaKey) {
      return;
    }
    
    // Permitir apenas números
    if (!/[0-9]/.test(e.key)) {
      e.preventDefault();
    }
  };

  const getInputClasses = () => {
    const baseClasses = "w-full px-3 py-2 border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors text-right";
    
    // Ajustar padding se houver ícone
    const paddingClasses = showIcon ? "pl-10" : "px-3";
    
    let borderColor = "border-border";
    
    if (error || (!isValid && showValidation && isDirty)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (isValid && formattedValue && showValidation && isDirty) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }
    
    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";
    
    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError = error || (showValidation && !isValid && isDirty ? validationMessage : '');
  const numericValue = parseCurrency(formattedValue);

  return (
    <div className="space-y-1">
      <label className="flex items-center text-sm font-medium text-foreground">
        {label}
        {required && <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />}
      </label>
      
      <div className="relative">
        {/* Ícone de moeda */}
        {showIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
        
        <input
          type="text"
          value={formattedValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
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
            {isValid ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <div className="h-4 w-4 text-red-500">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Mensagens de erro */}
      {displayError && (
        <p className="text-sm text-red-600">{displayError}</p>
      )}
      
      {/* Mensagem de ajuda */}
      {!displayError && formattedValue && showValidation && isValid && isDirty && (
        <p className="text-xs text-muted-foreground">
          Valor válido • {numericValue.toLocaleString('pt-BR', { 
            style: 'currency', 
            currency: 'BRL' 
          })}
        </p>
      )}
      
      {!displayError && !formattedValue && isFocused && (
        <p className="text-xs text-muted-foreground">
          Digite apenas números • Ex: 12345 = R$ 123,45
        </p>
      )}
      
      {/* Dicas de range */}
      {!displayError && !formattedValue && !isFocused && (minValue !== null || maxValue !== null) && (
        <p className="text-xs text-muted-foreground">
          {minValue !== null && maxValue !== null ? (
            `Valor entre ${formatCurrency((minValue * 100).toString())} e ${formatCurrency((maxValue * 100).toString())}`
          ) : minValue !== null ? (
            `Valor mínimo: ${formatCurrency((minValue * 100).toString())}`
          ) : (
            `Valor máximo: ${formatCurrency((maxValue * 100).toString())}`
          )}
        </p>
      )}
    </div>
  );
};

export default InputCurrency;