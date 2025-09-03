import { useState, useCallback } from "react";
import { formatCEP } from "../utils/formatters";
import { removeNonNumeric, validateCEP } from "../utils/validators";

/**
 * Hook para gerenciar lógica de CEP com integração ViaCEP
 */
export const useCEP = (initialValue = "", options = {}) => {
  const {
    required = false,
    onChange,
    onAddressFound,
    autoConsult = false,
    showValidation = true,
  } = options;

  const [formattedValue, setFormattedValue] = useState(() => {
    return initialValue ? formatCEP(initialValue) : "";
  });

  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [addressData, setAddressData] = useState(null);

  const validateInput = useCallback(
    (inputValue) => {
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
    },
    [required]
  );

  const consultCEP = useCallback(
    async (cep) => {
      if (!cep || cep.length !== 8) return null;

      setIsLoading(true);

      try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const data = await response.json();

        if (data.erro) {
          setValidationMessage("CEP não encontrado");
          setIsValid(false);
          setAddressData(null);
          return null;
        } else {
          const addressInfo = {
            street: data.logradouro || "",
            neighborhood: data.bairro || "",
            city: data.localidade || "",
            state: data.uf || "",
            cep: cep,
            complement: data.complemento || "",
          };

          setAddressData(addressInfo);
          setValidationMessage("");
          setIsValid(true);

          // Callback para notificar endereço encontrado
          onAddressFound?.(addressInfo);

          return addressInfo;
        }
      } catch (error) {
        console.error("Erro ao consultar CEP:", error);
        setValidationMessage("Erro ao consultar CEP. Tente novamente.");
        setIsValid(false);
        setAddressData(null);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [onAddressFound]
  );

  const handleChange = useCallback(
    (value) => {
      const numbersOnly = removeNonNumeric(value);
      const limitedNumbers = numbersOnly.slice(0, 8);
      const formatted = formatCEP(limitedNumbers);

      setFormattedValue(formatted);
      setIsDirty(true);

      // Limpar dados de endereço se CEP for alterado
      if (addressData) {
        setAddressData(null);
      }

      const isCurrentlyValid = validateInput(limitedNumbers);

      // Auto-consulta se habilitado e CEP válido
      if (autoConsult && isCurrentlyValid && limitedNumbers.length === 8) {
        consultCEP(limitedNumbers);
      }

      // Callback externo
      onChange?.({
        value: limitedNumbers,
        formatted: formatted,
        isValid: isCurrentlyValid,
        addressData: null, // Reset quando mudando
      });
    },
    [onChange, validateInput, autoConsult, consultCEP, addressData]
  );

  const handleBlur = useCallback(() => {
    if (showValidation) {
      validateInput(removeNonNumeric(formattedValue));
    }
  }, [formattedValue, showValidation, validateInput]);

  const handleConsult = useCallback(async () => {
    const cleanCEP = removeNonNumeric(formattedValue);
    if (cleanCEP.length === 8) {
      return await consultCEP(cleanCEP);
    }
    return null;
  }, [formattedValue, consultCEP]);

  const setValue = useCallback(
    (newValue) => {
      const formatted = formatCEP(newValue);
      setFormattedValue(formatted);
      validateInput(newValue);
      setAddressData(null);
    },
    [validateInput]
  );

  const clear = useCallback(() => {
    setFormattedValue("");
    setIsValid(true);
    setValidationMessage("");
    setIsLoading(false);
    setIsDirty(false);
    setAddressData(null);
  }, []);

  return {
    // Valores
    formattedValue,
    rawValue: removeNonNumeric(formattedValue),
    isValid,
    validationMessage,
    isLoading,
    isDirty,
    addressData,

    // Métodos
    handleChange,
    handleBlur,
    handleConsult,
    setValue,
    clear,
    validate: () => validateInput(removeNonNumeric(formattedValue)),

    // Estado computado
    isEmpty: !formattedValue || formattedValue.trim() === "",
    isComplete: removeNonNumeric(formattedValue).length === 8,
    canConsult:
      isValid && removeNonNumeric(formattedValue).length === 8 && !isLoading,
    displayError:
      showValidation && !isValid && isDirty ? validationMessage : null,
    hasAddressData: !!addressData,
  };
};
