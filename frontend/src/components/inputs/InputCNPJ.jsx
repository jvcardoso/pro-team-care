import React, { useState, useEffect } from 'react';
import { Building2, Check, X, Search, Loader2 } from 'lucide-react';
import { formatCNPJ } from '../../utils/formatters';
import { removeNonNumeric, validateCNPJ } from '../../utils/validators';
import { consultarCNPJ } from '../../services/cnpjService';

const InputCNPJ = ({
  label = "CNPJ",
  value = '',
  onChange,
  onCompanyFound,
  placeholder = "00.000.000/0000-00",
  required = false,
  disabled = false,
  error = '',
  className = '',
  showValidation = true,
  showIcon = true,
  showConsultButton = true,
  autoConsult = false,
  ...props
}) => {
  const [formattedValue, setFormattedValue] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [companyData, setCompanyData] = useState(null);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      const formatted = formatCNPJ(value);
      setFormattedValue(formatted);
      
      if (showValidation && value) {
        validateInput(value);
      }
    }
  }, [value, showValidation]);

  // Auto-consulta quando CNPJ estiver válido (desabilitado por padrão para evitar loops)
  useEffect(() => {
    if (autoConsult && isValid && formattedValue.length === 18 && !isLoading) {
      const cleanCNPJ = removeNonNumeric(formattedValue);
      if (cleanCNPJ.length === 14) {
        // Pequeno delay para evitar múltiplas chamadas
        const timeoutId = setTimeout(() => {
          consultCompany(cleanCNPJ);
        }, 500);

        return () => clearTimeout(timeoutId);
      }
    }
  }, [autoConsult, isValid, formattedValue, isLoading]);

  const consultCompany = async (cnpj) => {
    if (!cnpj || cnpj.length !== 14) return;

    setIsLoading(true);

    try {
      const result = await consultarCNPJ(cnpj);
      
      setCompanyData(result);
      setValidationMessage('');
      setIsValid(true);

      // Callback para o componente pai com dados da empresa
      if (onCompanyFound) {
        onCompanyFound(result);
      }
    } catch (error) {
      console.error('Erro ao consultar CNPJ:', error);
      setValidationMessage(error.message || 'Erro ao consultar CNPJ');
      setIsValid(false);
      setCompanyData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const validateInput = (inputValue) => {
    const cleanValue = removeNonNumeric(inputValue);
    
    if (!cleanValue && required) {
      setIsValid(false);
      setValidationMessage('CNPJ é obrigatório');
      return false;
    }
    
    if (cleanValue && cleanValue.length < 14) {
      setIsValid(false);
      setValidationMessage('CNPJ deve ter 14 dígitos');
      return false;
    }
    
    if (cleanValue && !validateCNPJ(cleanValue)) {
      setIsValid(false);
      setValidationMessage('CNPJ inválido');
      return false;
    }
    
    setIsValid(true);
    setValidationMessage('');
    return true;
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbersOnly = removeNonNumeric(inputValue);
    
    // Limitar a 14 dígitos
    const limitedNumbers = numbersOnly.slice(0, 14);
    const formatted = formatCNPJ(limitedNumbers);
    
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

  const handleConsult = () => {
    const cleanCNPJ = removeNonNumeric(formattedValue);
    if (cleanCNPJ.length === 14) {
      consultCompany(cleanCNPJ);
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
    } else if (isValid && formattedValue && showValidation && isDirty && formattedValue.length === 18) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }
    
    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";
    
    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError = error || (showValidation && !isValid && isDirty ? validationMessage : '');
  const isComplete = formattedValue.length === 18; // 00.000.000/0000-00
  const canConsult = isValid && removeNonNumeric(formattedValue).length === 14 && !isLoading;

  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-foreground">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="flex gap-2">
        <div className="relative flex-1">
          {/* Ícone de empresa */}
          {showIcon && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3">
              <Building2 className="h-4 w-4 text-muted-foreground" />
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
              {isLoading ? (
                <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
              ) : isValid && isComplete && companyData ? (
                <Building2 className="h-4 w-4 text-green-500" />
              ) : isValid && isComplete ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : !isValid ? (
                <X className="h-4 w-4 text-red-500" />
              ) : null}
            </div>
          )}
        </div>
        
        {/* Botão Consultar */}
        {showConsultButton && (
          <button
            type="button"
            onClick={handleConsult}
            disabled={!canConsult || disabled}
            className={`px-4 py-2 border rounded-md font-medium transition-colors flex items-center gap-2 ${
              canConsult && !disabled
                ? 'border-border bg-secondary text-secondary-foreground hover:bg-secondary/80'
                : 'border-border bg-muted text-muted-foreground cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Consultar
          </button>
        )}
      </div>
      
      {/* Mensagens de erro */}
      {displayError && (
        <p className="text-sm text-red-600">{displayError}</p>
      )}
      
      {/* Dados da empresa encontrada */}
      {companyData && !displayError && (
        <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded border">
          <div className="flex items-start gap-2">
            <Building2 className="h-4 w-4 mt-0.5 text-green-600" />
            <div className="flex-1">
              <p className="font-medium text-foreground">{companyData.people.name}</p>
              {companyData.people.trade_name && companyData.people.trade_name !== companyData.people.name && (
                <p className="text-xs opacity-75">Nome Fantasia: {companyData.people.trade_name}</p>
              )}
              <div className="mt-1 space-y-1">
                <p>Status: <span className="capitalize">{companyData.people.status}</span></p>
                {companyData.people.metadata?.situacao && (
                  <p>Situação: {companyData.people.metadata.situacao}</p>
                )}
                {companyData.people.metadata?.porte && (
                  <p>Porte: {companyData.people.metadata.porte}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Mensagem de ajuda */}
      {!displayError && !companyData && formattedValue && showValidation && isValid && isDirty && isComplete && (
        <p className="text-xs text-muted-foreground">
          CNPJ válido • Clique em "Consultar" para buscar dados da empresa
        </p>
      )}
      
      {!displayError && !formattedValue && isFocused && (
        <p className="text-xs text-muted-foreground">
          Digite o CNPJ com 14 dígitos
        </p>
      )}
      
      {!displayError && formattedValue && !isComplete && isDirty && (
        <p className="text-xs text-muted-foreground">
          {14 - removeNonNumeric(formattedValue).length} dígitos restantes
        </p>
      )}
    </div>
  );
};

export default InputCNPJ;