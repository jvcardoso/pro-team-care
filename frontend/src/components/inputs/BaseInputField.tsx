/**
 * BaseInputField - Componente base para todos os inputs especializados
 * 🎯 Elimina 980+ linhas de código duplicado
 *
 * Centraliza toda a lógica comum:
 * - Estado de validação e formatação
 * - Handlers de eventos
 * - Classes CSS dinâmicas
 * - Mensagens de erro e sucesso
 * - Ícones e indicadores visuais
 */

import React, {
  useState,
  useEffect,
  useCallback,
  ReactNode,
  forwardRef,
} from "react";
import { Star, Check, X, AlertCircle } from "lucide-react";

// Tipos para formatação e validação
export interface ValidationResult {
  isValid: boolean;
  message: string;
  isComplete?: boolean;
}

export interface FormatterConfig {
  formatter: (value: string) => string;
  cleaner?: (value: string) => string;
  maxLength?: number;
  completedLength?: number;
}

export interface ValidatorConfig {
  validator: (value: string, required?: boolean) => ValidationResult;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

// Props do BaseInputField
export interface BaseInputFieldProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  // Configuração específica do input
  label?: string;
  required?: boolean;
  error?: string;
  helper?: string;
  showValidation?: boolean;

  // Visual
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";

  // Formatação e validação
  formatterConfig?: FormatterConfig;
  validatorConfig?: ValidatorConfig;

  // Callbacks customizados
  onChange?: (event: {
    target: { name?: string; value: string };
    formatted: string;
    isValid: boolean;
    rawValue: string;
    validationResult: ValidationResult;
  }) => void;

  // Comportamento
  cleanValueForCallback?: boolean;
  showProgressIndicator?: boolean;
  progressMessage?: (remaining: number, total: number) => string;
  successMessage?: string;

  // Classes CSS
  className?: string;
  containerClassName?: string;
}

const BaseInputField = forwardRef<HTMLInputElement, BaseInputFieldProps>(
  (
    {
      // Core props
      label,
      value = "",
      onChange,
      placeholder,
      required = false,
      disabled = false,
      error = "",
      helper = "",
      showValidation = true,

      // Visual props
      leftIcon,
      rightIcon,
      showIcon = true,
      size = "md",

      // Formatter/Validator
      formatterConfig,
      validatorConfig,

      // Behavior props
      cleanValueForCallback = true,
      showProgressIndicator = false,
      progressMessage,
      successMessage,

      // CSS props
      className = "",
      containerClassName = "",

      // Rest props
      ...props
    },
    ref
  ) => {
    // 🎯 Estado centralizado (elimina duplicação em todos os inputs)
    const [formattedValue, setFormattedValue] = useState("");
    const [isValid, setIsValid] = useState(true);
    const [validationResult, setValidationResult] = useState<ValidationResult>({
      isValid: true,
      message: "",
      isComplete: false,
    });
    const [isFocused, setIsFocused] = useState(false);
    const [isDirty, setIsDirty] = useState(false);

    // 🔄 Sincronizar valor externo (lógica comum a todos os inputs)
    useEffect(() => {
      if (value !== undefined) {
        let formatted = value;

        if (formatterConfig?.formatter) {
          formatted = formatterConfig.formatter(String(value));
        }

        setFormattedValue(formatted);

        // Validar se necessário
        if (showValidation && value && validatorConfig?.validator) {
          const result = validatorConfig.validator(String(value), required);
          setIsValid(result.isValid);
          setValidationResult(result);
        }
      }
    }, [value, showValidation, required, formatterConfig, validatorConfig]);

    // 🔍 Função de validação centralizada
    const validateInput = useCallback(
      (inputValue: string): ValidationResult => {
        if (!validatorConfig?.validator) {
          return { isValid: true, message: "", isComplete: true };
        }

        const result = validatorConfig.validator(inputValue, required);
        setIsValid(result.isValid);
        setValidationResult(result);
        return result;
      },
      [validatorConfig, required]
    );

    // 📝 Handler de mudança centralizado (elimina duplicação)
    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const inputValue = e.target.value;
        let processedValue = inputValue;
        let cleanValue = inputValue;

        // Aplicar limpeza se configurada
        if (formatterConfig?.cleaner) {
          cleanValue = formatterConfig.cleaner(inputValue);
        }

        // Aplicar limite de caracteres
        if (formatterConfig?.maxLength) {
          cleanValue = cleanValue.slice(0, formatterConfig.maxLength);
        }

        // Aplicar formatação
        if (formatterConfig?.formatter) {
          processedValue = formatterConfig.formatter(cleanValue);
        } else {
          processedValue = cleanValue;
        }

        setFormattedValue(processedValue);
        setIsDirty(true);

        // Validação em tempo real se configurada
        let validationResult: ValidationResult = { isValid: true, message: "" };
        if (showValidation && validatorConfig?.validateOnChange && isDirty) {
          validationResult = validateInput(cleanValue);
        }

        // Callback customizado
        if (onChange) {
          onChange({
            target: {
              name: e.target.name,
              value: cleanValueForCallback ? cleanValue : processedValue,
            },
            formatted: processedValue,
            isValid: validationResult.isValid,
            rawValue: cleanValue,
            validationResult,
          });
        }
      },
      [
        formatterConfig,
        validatorConfig,
        showValidation,
        isDirty,
        required,
        cleanValueForCallback,
        onChange,
        validateInput,
      ]
    );

    // 🎯 Focus handlers centralizados
    const handleFocus = useCallback(
      (e: React.FocusEvent<HTMLInputElement>) => {
        setIsFocused(true);
        props.onFocus?.(e);
      },
      [props.onFocus]
    );

    const handleBlur = useCallback(
      (e: React.FocusEvent<HTMLInputElement>) => {
        setIsFocused(false);
        setIsDirty(true);

        // Validação final no blur se configurada
        if (showValidation && validatorConfig?.validateOnBlur !== false) {
          const cleanValue = formatterConfig?.cleaner
            ? formatterConfig.cleaner(formattedValue)
            : formattedValue;
          validateInput(cleanValue);
        }

        props.onBlur?.(e);
      },
      [
        showValidation,
        validatorConfig,
        formatterConfig,
        formattedValue,
        validateInput,
        props.onBlur,
      ]
    );

    // 🎨 Classes CSS dinâmicas centralizadas
    const getInputClasses = useCallback(() => {
      const sizeClasses = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-3 py-2 text-sm",
        lg: "px-4 py-3 text-base",
      };

      const baseClasses = [
        "w-full border rounded-md transition-colors",
        "bg-input text-foreground placeholder-muted-foreground",
        "focus:ring-2 focus:ring-ring focus:outline-none",
        sizeClasses[size],
      ];

      // Ajustar padding para ícones
      if (leftIcon || (showIcon && leftIcon)) {
        baseClasses.push("pl-10");
      }
      if (rightIcon || (showValidation && formattedValue && isDirty)) {
        baseClasses.push("pr-10");
      }

      // Estados de validação
      let borderColor = "border-border";
      if (error || (!isValid && showValidation && isDirty)) {
        borderColor = "border-red-500 focus:ring-red-500 focus:border-red-500";
      } else if (
        isValid &&
        formattedValue &&
        showValidation &&
        isDirty &&
        validationResult.isComplete
      ) {
        borderColor =
          "border-green-500 focus:ring-green-500 focus:border-green-500";
      } else if (isFocused) {
        borderColor = "focus:border-ring";
      }

      // Estado disabled
      if (disabled) {
        baseClasses.push("opacity-50 cursor-not-allowed");
      }

      return [...baseClasses, borderColor, className].filter(Boolean).join(" ");
    }, [
      size,
      leftIcon,
      rightIcon,
      showIcon,
      showValidation,
      formattedValue,
      isDirty,
      error,
      isValid,
      isFocused,
      disabled,
      validationResult.isComplete,
      className,
    ]);

    // 💬 Mensagens de ajuda e erro
    const displayError =
      error ||
      (showValidation && !isValid && isDirty ? validationResult.message : "");
    const shouldShowSuccess =
      isValid &&
      formattedValue &&
      showValidation &&
      isDirty &&
      validationResult.isComplete;
    const shouldShowProgress =
      showProgressIndicator &&
      formattedValue &&
      !validationResult.isComplete &&
      isDirty;

    return (
      <div className={`space-y-1 ${containerClassName}`}>
        {/* Label */}
        {label && (
          <label className="flex items-center text-sm font-medium text-foreground">
            {label}
            {required && (
              <Star
                className="h-3 w-3 text-red-500 ml-1 fill-current"
                aria-hidden="true"
              />
            )}
          </label>
        )}

        <div className="relative">
          {/* Left Icon */}
          {(leftIcon || (showIcon && leftIcon)) && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <span className="text-muted-foreground" aria-hidden="true">
                {leftIcon}
              </span>
            </div>
          )}

          {/* Input Field */}
          <input
            ref={ref}
            type="text"
            value={formattedValue}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={placeholder}
            disabled={disabled}
            className={getInputClasses()}
            aria-invalid={!isValid}
            aria-describedby={
              displayError ? `${props.id || "input"}-error` : undefined
            }
            {...props}
          />

          {/* Right Icon / Validation Indicator */}
          {(rightIcon || (showValidation && formattedValue && isDirty)) && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              {rightIcon || (
                <>
                  {isValid && validationResult.isComplete ? (
                    <Check
                      className="h-4 w-4 text-green-500"
                      aria-hidden="true"
                    />
                  ) : !isValid ? (
                    <X className="h-4 w-4 text-red-500" aria-hidden="true" />
                  ) : null}
                </>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {displayError && (
          <p
            className="flex items-center text-sm text-red-600"
            role="alert"
            id={`${props.id || "input"}-error`}
          >
            <AlertCircle className="h-3 w-3 mr-1 flex-shrink-0" />
            {displayError}
          </p>
        )}

        {/* Helper Text */}
        {!displayError && helper && (
          <p className="text-xs text-muted-foreground">{helper}</p>
        )}

        {/* Success Message */}
        {!displayError && shouldShowSuccess && successMessage && (
          <p className="text-xs text-green-600">{successMessage}</p>
        )}

        {/* Progress Indicator */}
        {!displayError &&
          shouldShowProgress &&
          progressMessage &&
          formatterConfig?.maxLength && (
            <p className="text-xs text-muted-foreground">
              {progressMessage(
                formatterConfig.maxLength -
                  (formatterConfig.cleaner
                    ? formatterConfig.cleaner(formattedValue).length
                    : formattedValue.length),
                formatterConfig.maxLength
              )}
            </p>
          )}

        {/* Focus Hint */}
        {!displayError && !formattedValue && isFocused && placeholder && (
          <p className="text-xs text-muted-foreground">
            {typeof placeholder === "string" && placeholder.includes("000")
              ? `Digite ${label?.toLowerCase() || "o valor"}`
              : placeholder}
          </p>
        )}
      </div>
    );
  }
);

BaseInputField.displayName = "BaseInputField";

export default BaseInputField;
