import React, { useState, useEffect } from "react";
import { Mail, Check, X, Star } from "lucide-react";
import { validateEmail } from "../../utils/validators";

const InputEmail = ({
  label = "E-mail",
  value = "",
  onChange,
  placeholder = "usuario@exemplo.com",
  required = false,
  disabled = false,
  error = "",
  className = "",
  showValidation = true,
  showIcon = true,
  type = "email",
  ...props
}) => {
  const [inputValue, setInputValue] = useState("");
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      setInputValue(value);

      // Só validar se tiver valor ou se for required
      if (showValidation && (value || required)) {
        validateInput(value);
      }
    }
  }, [value, showValidation, required]);

  const validateInput = (inputValue) => {
    const trimmedValue = inputValue.trim();

    if (!trimmedValue && required) {
      setIsValid(false);
      setValidationMessage("E-mail é obrigatório");
      return false;
    }

    if (trimmedValue && !validateEmail(trimmedValue)) {
      setIsValid(false);
      setValidationMessage("E-mail inválido");
      return false;
    }

    setIsValid(true);
    setValidationMessage("");
    return true;
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsDirty(true);

    // Validação em tempo real apenas após o primeiro blur
    if (showValidation && isDirty) {
      validateInput(newValue);
    }

    // Callback para o componente pai
    if (onChange) {
      onChange({
        target: {
          name: e.target.name,
          value: newValue.trim(), // Email limpo para o backend
        },
        isValid: validateInput(newValue),
        rawValue: newValue,
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
      validateInput(inputValue);
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
    } else if (isValid && inputValue && showValidation && isDirty) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }

    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";

    return `${baseClasses} ${paddingClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const getDomainSuggestion = (email) => {
    const commonDomains = [
      "gmail.com",
      "hotmail.com",
      "outlook.com",
      "yahoo.com",
      "uol.com.br",
      "globo.com",
      "terra.com.br",
      "ig.com.br",
    ];

    const atIndex = email.indexOf("@");
    if (atIndex === -1) return null;

    const domain = email.substring(atIndex + 1).toLowerCase();
    if (!domain) return null;

    // Buscar domínios similares
    const suggestion = commonDomains.find(
      (commonDomain) =>
        commonDomain.startsWith(domain) && commonDomain !== domain
    );

    return suggestion ? email.substring(0, atIndex + 1) + suggestion : null;
  };

  const displayError =
    error || (showValidation && !isValid && isDirty ? validationMessage : "");
  const domainSuggestion =
    inputValue && !isValid ? getDomainSuggestion(inputValue) : null;

  return (
    <div className="space-y-1">
      <label className="flex items-center text-sm font-medium text-foreground">
        {label}
        {required && (
          <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />
        )}
      </label>

      <div className="relative">
        {/* Ícone de e-mail */}
        {showIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3">
            <Mail className="h-4 w-4 text-muted-foreground" />
          </div>
        )}

        <input
          type={type}
          value={inputValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={getInputClasses()}
          autoComplete="email"
          spellCheck="false"
          {...props}
        />

        {/* Indicador de validação visual */}
        {showValidation && inputValue && isDirty && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {isValid ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <X className="h-4 w-4 text-red-500" />
            )}
          </div>
        )}
      </div>

      {/* Mensagens de erro */}
      {displayError && <p className="text-sm text-red-600">{displayError}</p>}

      {/* Sugestão de domínio */}
      {domainSuggestion && !displayError && (
        <div className="text-xs text-blue-600">
          <button
            type="button"
            onClick={() => {
              setInputValue(domainSuggestion);
              validateInput(domainSuggestion);
              if (onChange) {
                onChange({
                  target: {
                    name: props.name,
                    value: domainSuggestion,
                  },
                  isValid: true,
                  rawValue: domainSuggestion,
                });
              }
            }}
            className="hover:underline"
          >
            Você quis dizer: <strong>{domainSuggestion}</strong>?
          </button>
        </div>
      )}

      {/* Mensagem de ajuda */}
      {!displayError &&
        !domainSuggestion &&
        inputValue &&
        showValidation &&
        isValid &&
        isDirty && (
          <p className="text-xs text-muted-foreground">E-mail válido</p>
        )}

      {!displayError && !inputValue && isFocused && (
        <p className="text-xs text-muted-foreground">
          Digite um endereço de e-mail válido
        </p>
      )}
    </div>
  );
};

export default InputEmail;
