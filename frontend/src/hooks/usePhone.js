import { useState, useCallback } from "react";
import { formatPhone } from "../utils/formatters";
import {
  removeNonNumeric,
  validatePhone,
  validateDDD,
} from "../utils/validators";

/**
 * Hook para gerenciar lógica de entrada de telefone
 */
export const usePhone = (initialValue = "", options = {}) => {
  const {
    required = false,
    onChange,
    countryCode = "55",
    showValidation = true,
  } = options;

  const [formattedValue, setFormattedValue] = useState(() => {
    return initialValue ? formatPhone(initialValue) : "";
  });

  const [isValid, setIsValid] = useState(true);
  const [validationMessage, setValidationMessage] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  const validateInput = useCallback(
    (inputValue) => {
      const cleanValue = removeNonNumeric(inputValue);

      if (!cleanValue && required) {
        setIsValid(false);
        setValidationMessage("Telefone é obrigatório");
        return false;
      }

      if (cleanValue && !validatePhone(cleanValue)) {
        setIsValid(false);

        if (cleanValue.length < 10) {
          setValidationMessage("Telefone deve ter pelo menos 10 dígitos");
        } else if (cleanValue.length > 11) {
          setValidationMessage("Telefone deve ter no máximo 11 dígitos");
        } else {
          const ddd = cleanValue.substring(0, 2);
          if (!validateDDD(ddd)) {
            setValidationMessage("DDD inválido");
          } else {
            setValidationMessage("Telefone inválido");
          }
        }
        return false;
      }

      setIsValid(true);
      setValidationMessage("");
      return true;
    },
    [required]
  );

  const handleChange = useCallback(
    (value) => {
      const numbersOnly = removeNonNumeric(value);
      const limitedNumbers = numbersOnly.slice(0, 11);
      const formatted = formatPhone(limitedNumbers);

      setFormattedValue(formatted);
      setIsDirty(true);

      const isCurrentlyValid = validateInput(limitedNumbers);

      // Callback externo
      onChange?.({
        value: limitedNumbers,
        formatted: formatted,
        isValid: isCurrentlyValid,
        type: getPhoneType(limitedNumbers),
      });
    },
    [onChange, validateInput]
  );

  const handleBlur = useCallback(() => {
    if (showValidation) {
      validateInput(removeNonNumeric(formattedValue));
    }
  }, [formattedValue, showValidation, validateInput]);

  const setValue = useCallback(
    (newValue) => {
      const formatted = formatPhone(newValue);
      setFormattedValue(formatted);
      validateInput(newValue);
    },
    [validateInput]
  );

  const clear = useCallback(() => {
    setFormattedValue("");
    setIsValid(true);
    setValidationMessage("");
    setIsDirty(false);
  }, []);

  const getPhoneType = useCallback((phoneNumber) => {
    const numbers = removeNonNumeric(phoneNumber);
    if (numbers.length === 11) {
      return "mobile";
    } else if (numbers.length === 10) {
      return "landline";
    }
    return null;
  }, []);

  return {
    // Valores
    formattedValue,
    rawValue: removeNonNumeric(formattedValue),
    isValid,
    validationMessage,
    isDirty,
    phoneType: getPhoneType(formattedValue),

    // Métodos
    handleChange,
    handleBlur,
    setValue,
    clear,
    validate: () => validateInput(removeNonNumeric(formattedValue)),

    // Estado computado
    isEmpty: !formattedValue || formattedValue.trim() === "",
    isComplete: removeNonNumeric(formattedValue).length >= 10,
    displayError:
      showValidation && !isValid && isDirty ? validationMessage : null,
  };
};
