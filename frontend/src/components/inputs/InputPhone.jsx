import React, { useState, useEffect } from 'react';
import { Star } from 'lucide-react';
import { formatPhone } from '../../utils/formatters';
import { removeNonNumeric } from '../../utils/validators';
import { validatePhone, validateDDD } from '../../utils/validators';

const InputPhone = ({
  label = "Telefone",
  value = '',
  onChange,
  placeholder = "(11) 99999-9999",
  required = false,
  disabled = false,
  error = '',
  className = '',
  showValidation = true,
  countryCode = '55',
  ...props
}) => {
  const [formattedValue, setFormattedValue] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      const formatted = formatPhone(value);
      setFormattedValue(formatted);
      
      // Só validar se tiver valor ou se for required
      if (showValidation && (value || required)) {
        validateInput(value);
      }
    }
  }, [value, showValidation, required]);

  const validateInput = (inputValue) => {
    const cleanValue = removeNonNumeric(inputValue);
    
    if (!cleanValue && required) {
      setIsValid(false);
      setValidationMessage('Telefone é obrigatório');
      return false;
    }
    
    if (cleanValue && !validatePhone(cleanValue)) {
      setIsValid(false);
      
      if (cleanValue.length < 10) {
        setValidationMessage('Telefone deve ter pelo menos 10 dígitos');
      } else if (cleanValue.length > 11) {
        setValidationMessage('Telefone deve ter no máximo 11 dígitos');
      } else {
        const ddd = cleanValue.substring(0, 2);
        if (!validateDDD(ddd)) {
          setValidationMessage('DDD inválido');
        } else {
          setValidationMessage('Telefone inválido');
        }
      }
      return false;
    }
    
    setIsValid(true);
    setValidationMessage('');
    return true;
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbersOnly = removeNonNumeric(inputValue);
    
    // Limitar a 11 dígitos (DDD + 9 dígitos do celular)
    const limitedNumbers = numbersOnly.slice(0, 11);
    const formatted = formatPhone(limitedNumbers);
    
    setFormattedValue(formatted);
    
    // Validar se necessário
    if (showValidation) {
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
    
    let borderColor = "border-border";
    
    if (error || (!isValid && showValidation)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (isValid && formattedValue && showValidation) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }
    
    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";
    
    return `${baseClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const getPhoneType = (phoneNumber) => {
    const numbers = removeNonNumeric(phoneNumber);
    if (numbers.length === 11) {
      return 'Celular';
    } else if (numbers.length === 10) {
      return 'Fixo';
    }
    return '';
  };

  const displayError = error || (showValidation && !isValid ? validationMessage : '');
  const phoneType = getPhoneType(formattedValue);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="flex items-center text-sm font-medium text-foreground">
          {label}
          {required && <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />}
        </label>
        {phoneType && (
          <span className="text-xs text-muted-foreground">
            {phoneType}
          </span>
        )}
      </div>
      
      <div className="relative">
        <input
          type="tel"
          value={formattedValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={getInputClasses()}
          autoComplete="tel"
          inputMode="tel"
          {...props}
        />
        
        {/* Indicador de validação visual */}
        {showValidation && formattedValue && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {isValid ? (
              <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            )}
          </div>
        )}
      </div>
      
      {/* Mensagens de erro/ajuda */}
      {displayError && (
        <p className="text-sm text-red-600">{displayError}</p>
      )}
      
      {!displayError && formattedValue && showValidation && (
        <p className="text-xs text-muted-foreground">
          {phoneType && `${phoneType} • `}
          +{countryCode} {removeNonNumeric(formattedValue)}
        </p>
      )}
    </div>
  );
};

export default InputPhone;