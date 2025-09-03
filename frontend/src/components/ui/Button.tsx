import React, { ReactNode } from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode;
  variant?: "primary" | "secondary" | "success" | "danger" | "warning";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  outline?: boolean;
  block?: boolean;
  className?: string;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  type?: "button" | "submit" | "reset";
  icon?: ReactNode;
  iconPosition?: "left" | "right";
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  outline = false,
  block = false,
  className = "",
  onClick,
  type = "button",
  icon,
  iconPosition = "left",
  ...props
}) => {
  const baseClasses = [
    "inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors",
    "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring",
    "disabled:opacity-50 disabled:pointer-events-none",
  ];

  // Size classes - Mobile-optimized with better touch targets
  const sizeClasses = {
    sm: "px-3 py-2 text-sm min-h-[36px]", // Increased touch target
    md: "px-4 py-2.5 text-sm min-h-[40px]", // Better mobile tap area
    lg: "px-6 py-3 text-base min-h-[44px]", // iOS recommended minimum
  };

  // Variant classes
  const variantClasses = {
    primary: outline
      ? "border border-primary-500 text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950"
      : "bg-primary-500 text-white hover:bg-primary-600",
    secondary: outline
      ? "border border-secondary-500 text-secondary-500 hover:bg-secondary-50 dark:hover:bg-secondary-950"
      : "bg-secondary-500 text-white hover:bg-secondary-600",
    success: outline
      ? "border border-green-500 text-green-500 hover:bg-green-50 dark:hover:bg-green-950"
      : "bg-green-500 text-white hover:bg-green-600",
    danger: outline
      ? "border border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-950"
      : "bg-red-500 text-white hover:bg-red-600",
    warning: outline
      ? "border border-yellow-500 text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-950"
      : "bg-yellow-500 text-white hover:bg-yellow-600",
  };

  const buttonClasses = [
    ...baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    block && "w-full",
    loading && "relative pointer-events-none",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>): void => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  const renderIcon = (): ReactNode => {
    if (loading) {
      return (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      );
    }
    return icon;
  };

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
      aria-busy={loading}
      aria-describedby={loading ? `${props.id || "button"}-loading` : undefined}
      role="button"
      tabIndex={disabled ? -1 : 0}
      {...props}
    >
      {loading && (
        <span
          id={`${props.id || "button"}-loading`}
          className="sr-only"
          aria-live="polite"
        >
          Carregando...
        </span>
      )}
      {icon && iconPosition === "left" && (
        <span aria-hidden="true">{renderIcon()}</span>
      )}
      <span className={loading ? "opacity-75" : ""}>{children}</span>
      {icon && iconPosition === "right" && (
        <span aria-hidden="true">{renderIcon()}</span>
      )}
    </button>
  );
};

export default Button;
