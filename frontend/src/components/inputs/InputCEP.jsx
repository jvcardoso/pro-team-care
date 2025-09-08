import React, { useState, useEffect } from "react";
import { Search, Loader2, MapPin, Star } from "lucide-react";
import { formatCEP } from "../../utils/formatters";
import { removeNonNumeric } from "../../utils/validators";
import { validateCEP } from "../../utils/validators";
import geocodingService from "../../services/geocodingService";

const InputCEP = ({
  label = "CEP",
  value = "",
  onChange,
  onAddressFound,
  placeholder = "12345-678",
  required = false,
  disabled = false,
  error = "",
  className = "",
  showValidation = true,
  showConsultButton = true,
  autoConsult = false,
  ...props
}) => {
  const [formattedValue, setFormattedValue] = useState("");
  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [addressData, setAddressData] = useState(null);

  // Sincronizar valor externo com estado interno
  useEffect(() => {
    if (value !== undefined) {
      const formatted = formatCEP(value);
      setFormattedValue(formatted);

      // Só validar se tiver valor ou se for required
      if (showValidation && (value || required)) {
        validateInput(value);
      }
    }
  }, [value, showValidation, required]);

  // Auto-consulta quando CEP estiver válido
  useEffect(() => {
    if (autoConsult && isValid && formattedValue.length === 9) {
      const cleanCEP = removeNonNumeric(formattedValue);
      if (cleanCEP.length === 8) {
        consultCEP(cleanCEP);
      }
    }
  }, [autoConsult, isValid, formattedValue]);

  const validateInput = (inputValue) => {
    const cleanValue = removeNonNumeric(inputValue);

    if (!cleanValue && required) {
      setIsValid(false);
      setValidationMessage("CEP é obrigatório");
      return false;
    }

    if (cleanValue && !validateCEP(cleanValue)) {
      setIsValid(false);

      if (cleanValue.length < 8) {
        setValidationMessage("CEP deve ter 8 dígitos");
      } else {
        setValidationMessage("CEP inválido");
      }
      return false;
    }

    setIsValid(true);
    setValidationMessage("");
    return true;
  };

  const consultCEP = async (cep) => {
    if (!cep || cep.length !== 8) return;

    setIsLoading(true);

    try {
      // 1. Consultar ViaCEP primeiro
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const viaCepData = await response.json();

      if (viaCepData.erro) {
        setValidationMessage("CEP não encontrado");
        setIsValid(false);
        setAddressData(null);
        return;
      }

      // 2. Enriquecer com dados geográficos usando Nominatim
      console.log("🔍 Enriquecendo endereço com coordenadas...");
      const enrichedData = await geocodingService.geocodeBrazilianAddress({
        // Dados básicos do endereço
        street: viaCepData.logradouro || "",
        number: "", // Deixar em branco - usuário deve informar manualmente
        neighborhood: viaCepData.bairro || "",
        city: viaCepData.localidade || "",
        state: viaCepData.uf || "",
        zip_code: cep,
        complement: viaCepData.complemento || "",

        // Códigos oficiais brasileiros
        ibge_city_code: viaCepData.ibge || null,
        gia_code: viaCepData.gia || null,
        siafi_code: viaCepData.siafi || null,
        area_code: viaCepData.ddd || null,

        // Campos da ViaCEP
        logradouro: viaCepData.logradouro,
        bairro: viaCepData.bairro,
        localidade: viaCepData.localidade,
        uf: viaCepData.uf,
      });

      setAddressData(enrichedData);
      setValidationMessage("");
      setIsValid(true);

      // Log para debug
      if (enrichedData?.latitude && enrichedData?.longitude) {
        console.log(
          `✅ Endereço enriquecido com coordenadas: ${enrichedData.latitude}, ${enrichedData.longitude}`
        );
        console.log(
          `📍 Fonte: ${enrichedData.geocoding_source} | Precisão: ${enrichedData.geocoding_accuracy}`
        );
      } else {
        console.log(
          "⚠️ Coordenadas não encontradas, usando apenas dados ViaCEP"
        );
      }

      // Callback para o componente pai com dados completos
      if (onAddressFound) {
        onAddressFound(enrichedData);
      }
    } catch (error) {
      console.error("❌ Erro ao consultar CEP:", error);
      setValidationMessage("Erro ao consultar CEP. Tente novamente.");
      setIsValid(false);
      setAddressData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const inputValue = e.target.value;
    const numbersOnly = removeNonNumeric(inputValue);

    // Limitar a 8 dígitos
    const limitedNumbers = numbersOnly.slice(0, 8);
    const formatted = formatCEP(limitedNumbers);

    setFormattedValue(formatted);

    // Limpar dados de endereço se CEP for alterado
    if (addressData) {
      setAddressData(null);
    }

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

    // Validação final no blur
    if (showValidation) {
      validateInput(removeNonNumeric(formattedValue));
    }

    if (props.onBlur) {
      props.onBlur(e);
    }
  };

  const handleConsultClick = () => {
    const cleanCEP = removeNonNumeric(formattedValue);
    if (cleanCEP.length === 8) {
      consultCEP(cleanCEP);
    }
  };

  const getInputClasses = () => {
    const baseClasses =
      "w-full px-3 py-2 border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none transition-colors";

    let borderColor = "border-border";

    if (error || (!isValid && showValidation)) {
      borderColor = "border-red-500 focus:ring-red-500";
    } else if (isValid && formattedValue && showValidation && addressData) {
      borderColor = "border-green-500 focus:ring-green-500";
    } else if (isFocused) {
      borderColor = "border-ring";
    }

    const disabledClasses = disabled ? "opacity-50 cursor-not-allowed" : "";

    return `${baseClasses} ${borderColor} ${disabledClasses} ${className}`;
  };

  const displayError =
    error || (showValidation && !isValid ? validationMessage : "");
  const canConsult =
    isValid && removeNonNumeric(formattedValue).length === 8 && !isLoading;

  return (
    <div className="space-y-1">
      <label className="flex items-center text-sm font-medium text-foreground">
        {label}
        {required && (
          <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />
        )}
      </label>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={formattedValue}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            className={getInputClasses()}
            autoComplete="postal-code"
            inputMode="numeric"
            {...props}
          />

          {/* Indicador de validação visual */}
          {showValidation && formattedValue && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              {isLoading ? (
                <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
              ) : isValid && addressData ? (
                <MapPin className="h-4 w-4 text-green-500" />
              ) : isValid && !addressData ? (
                <svg
                  className="h-4 w-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg
                  className="h-4 w-4 text-red-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
          )}
        </div>

        {/* Botão Consultar */}
        {showConsultButton && (
          <button
            type="button"
            onClick={handleConsultClick}
            disabled={!canConsult || disabled}
            className={`px-4 py-2 border rounded-md font-medium transition-colors flex items-center gap-2 ${
              canConsult && !disabled
                ? "border-border bg-secondary text-secondary-foreground hover:bg-secondary/80"
                : "border-border bg-muted text-muted-foreground cursor-not-allowed"
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

      {/* Mensagens de erro/ajuda */}
      {displayError && <p className="text-sm text-red-600">{displayError}</p>}

      {!displayError &&
        !addressData &&
        formattedValue &&
        showValidation &&
        isValid && (
          <p className="text-xs text-muted-foreground">
            CEP válido • Clique em "Consultar" para buscar endereço
          </p>
        )}
    </div>
  );
};

export default InputCEP;
