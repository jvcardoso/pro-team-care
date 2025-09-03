import { useState, useCallback, useMemo } from "react";

/**
 * Hook genérico para gerenciar formulários complexos
 */
export const useForm = (initialData = {}, options = {}) => {
  const {
    validate,
    onSubmit,
    resetOnSubmit = false,
    validateOnChange = false,
    validateOnBlur = true,
  } = options;

  const [formData, setFormData] = useState(initialData);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Validar um campo específico
  const validateField = useCallback(
    (name, value) => {
      if (!validate || !validate[name]) return null;

      const validator = validate[name];
      if (typeof validator === "function") {
        return validator(value, formData);
      }

      // Validador objeto com regras
      if (typeof validator === "object") {
        const { required, minLength, maxLength, pattern, custom } = validator;

        if (required && (!value || value.toString().trim() === "")) {
          return validator.requiredMessage || "Campo obrigatório";
        }

        if (value && minLength && value.toString().length < minLength) {
          return (
            validator.minLengthMessage || `Mínimo de ${minLength} caracteres`
          );
        }

        if (value && maxLength && value.toString().length > maxLength) {
          return (
            validator.maxLengthMessage || `Máximo de ${maxLength} caracteres`
          );
        }

        if (value && pattern && !pattern.test(value.toString())) {
          return validator.patternMessage || "Formato inválido";
        }

        if (value && custom && typeof custom === "function") {
          return custom(value, formData);
        }
      }

      return null;
    },
    [validate, formData]
  );

  // Validar todos os campos
  const validateForm = useCallback(() => {
    if (!validate) return {};

    const newErrors = {};
    Object.keys(validate).forEach((name) => {
      const error = validateField(name, formData[name]);
      if (error) {
        newErrors[name] = error;
      }
    });

    setErrors(newErrors);
    return newErrors;
  }, [validate, formData, validateField]);

  // Atualizar valor de um campo
  const setValue = useCallback(
    (name, value) => {
      setFormData((prev) => ({ ...prev, [name]: value }));

      // Validar no change se habilitado
      if (validateOnChange) {
        const error = validateField(name, value);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }

      // Limpar erro do submit
      if (submitError) {
        setSubmitError(null);
      }
    },
    [validateField, validateOnChange, submitError]
  );

  // Atualizar múltiplos valores
  const setValues = useCallback(
    (newValues) => {
      setFormData((prev) => ({ ...prev, ...newValues }));

      if (validateOnChange && validate) {
        const newErrors = { ...errors };
        Object.keys(newValues).forEach((name) => {
          if (validate[name]) {
            const error = validateField(name, newValues[name]);
            newErrors[name] = error;
          }
        });
        setErrors(newErrors);
      }
    },
    [errors, validate, validateField, validateOnChange]
  );

  // Marcar campo como tocado
  const setFieldTouched = useCallback(
    (name, isTouched = true) => {
      setTouched((prev) => ({ ...prev, [name]: isTouched }));

      // Validar no blur se habilitado
      if (validateOnBlur && isTouched) {
        const error = validateField(name, formData[name]);
        setErrors((prev) => ({ ...prev, [name]: error }));
      }
    },
    [validateField, validateOnBlur, formData]
  );

  // Resetar formulário
  const reset = useCallback(
    (newInitialData) => {
      const resetData = newInitialData || initialData;
      setFormData(resetData);
      setErrors({});
      setTouched({});
      setIsSubmitting(false);
      setSubmitError(null);
    },
    [initialData]
  );

  // Submit do formulário
  const handleSubmit = useCallback(
    async (e) => {
      if (e && e.preventDefault) {
        e.preventDefault();
      }

      setIsSubmitting(true);
      setSubmitError(null);

      // Validar todos os campos
      const formErrors = validateForm();
      const hasErrors = Object.keys(formErrors).length > 0;

      if (hasErrors) {
        setIsSubmitting(false);
        // Marcar todos os campos como tocados para mostrar erros
        const allTouched = {};
        Object.keys(validate || {}).forEach((name) => {
          allTouched[name] = true;
        });
        setTouched(allTouched);
        return { success: false, errors: formErrors };
      }

      try {
        let result;
        if (onSubmit) {
          result = await onSubmit(formData);
        }

        if (resetOnSubmit) {
          reset();
        }

        setIsSubmitting(false);
        return { success: true, result };
      } catch (error) {
        setIsSubmitting(false);
        setSubmitError(error.message || "Erro ao salvar formulário");
        return { success: false, error };
      }
    },
    [formData, validateForm, onSubmit, resetOnSubmit, reset, validate]
  );

  // Helpers para criar props de input
  const getFieldProps = useCallback(
    (name, options = {}) => {
      return {
        name,
        value: formData[name] || "",
        onChange: (e) => {
          const value = e.target ? e.target.value : e;
          setValue(name, value);
        },
        onBlur: () => setFieldTouched(name, true),
        error: touched[name] ? errors[name] : null,
        ...options,
      };
    },
    [formData, errors, touched, setValue, setFieldTouched]
  );

  // Estado computado
  const isValid = useMemo(() => {
    return Object.keys(errors).length === 0;
  }, [errors]);

  const isDirty = useMemo(() => {
    return JSON.stringify(formData) !== JSON.stringify(initialData);
  }, [formData, initialData]);

  const hasErrors = useMemo(() => {
    return Object.values(errors).some((error) => !!error);
  }, [errors]);

  return {
    // Estado
    formData,
    errors,
    touched,
    isSubmitting,
    submitError,

    // Estado computado
    isValid,
    isDirty,
    hasErrors,

    // Métodos
    setValue,
    setValues,
    setFieldTouched,
    validateField,
    validateForm,
    handleSubmit,
    reset,
    getFieldProps,

    // Utilitários
    getFieldError: (name) => (touched[name] ? errors[name] : null),
    isFieldTouched: (name) => !!touched[name],
    isFieldValid: (name) => !errors[name],
    getTouchedFields: () =>
      Object.keys(touched).filter((name) => touched[name]),
    getErrorFields: () => Object.keys(errors).filter((name) => errors[name]),
  };
};
