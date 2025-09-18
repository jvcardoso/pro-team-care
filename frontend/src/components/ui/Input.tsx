import React, { forwardRef, ReactNode, useId } from "react";
import { Star } from "lucide-react";

interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helper?: string;
  required?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "success" | "warning" | "error";
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  className?: string;
  containerClassName?: string;
  type?: string;
  multiline?: boolean;
  rows?: number;
}

const Input = forwardRef<HTMLInputElement | HTMLTextAreaElement, InputProps>(
  (
    {
      label,
      error,
      helper,
      required = false,
      size = "md",
      variant = "default",
      leftIcon,
      rightIcon,
      className = "",
      containerClassName = "",
      type = "text",
      multiline = false,
      rows = 3,
      ...props
    },
    ref
  ) => {
    const baseClasses = [
      "w-full border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2",
      "bg-input text-foreground placeholder-muted-foreground",
      "border-border focus:border-ring focus:ring-ring",
    ];

    // Size classes
    const sizeClasses = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-3 py-2 text-sm",
      lg: "px-4 py-3 text-base",
    };

    // Variant classes
    const variantClasses = {
      default: "",
      success: "border-green-500 focus:border-green-500 focus:ring-green-500",
      warning:
        "border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500",
      error: "border-red-500 focus:border-red-500 focus:ring-red-500",
    };

    const inputClasses = [
      ...baseClasses,
      sizeClasses[size],
      variantClasses[variant],
      error && "border-red-500 focus:border-red-500 focus:ring-red-500",
      leftIcon && "pl-10",
      rightIcon && "pr-10",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    const containerClasses = ["w-full", containerClassName]
      .filter(Boolean)
      .join(" ");

    // Generate stable IDs for accessibility
    const reactId = useId();
    const inputId = props.id || `input-${reactId}`;
    const errorId = error ? `${inputId}-error` : undefined;
    const helperId = helper ? `${inputId}-helper` : undefined;
    const labelId = label ? `${inputId}-label` : undefined;

    return (
      <div className={containerClasses}>
        {label && (
          <label
            htmlFor={inputId}
            id={labelId}
            className="flex items-center text-sm font-medium text-foreground mb-2"
          >
            {label}
            {required && (
              <>
                <Star
                  className="h-3 w-3 text-red-500 ml-1 fill-current"
                  aria-hidden="true"
                />
                <span className="sr-only"> (obrigatório)</span>
              </>
            )}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-muted-foreground" aria-hidden="true">
                {leftIcon}
              </span>
            </div>
          )}

          {multiline ? (
            <textarea
              ref={ref as React.Ref<HTMLTextAreaElement>}
              id={inputId}
              className={inputClasses}
              required={required}
              aria-required={required}
              aria-invalid={!!error}
              aria-describedby={
                [errorId, helperId].filter(Boolean).join(" ") || undefined
              }
              aria-labelledby={labelId}
              rows={rows}
              {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
              value={props.value ?? ""}
            />
          ) : (
            <input
              ref={ref as React.Ref<HTMLInputElement>}
              id={inputId}
              type={type}
              className={inputClasses}
              required={required}
              aria-required={required}
              aria-invalid={!!error}
              aria-describedby={
                [errorId, helperId].filter(Boolean).join(" ") || undefined
              }
              aria-labelledby={labelId}
              {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
              value={props.value ?? ""}
            />
          )}

          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className="text-muted-foreground" aria-hidden="true">
                {rightIcon}
              </span>
            </div>
          )}
        </div>

        {error && (
          <p
            id={errorId}
            className="mt-1 text-sm text-red-500"
            role="alert"
            aria-live="polite"
          >
            {error}
          </p>
        )}

        {helper && !error && (
          <p id={helperId} className="mt-1 text-sm text-muted-foreground">
            {helper}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
