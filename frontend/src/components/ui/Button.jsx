import React from 'react';

const Button = ({ 
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  outline = false,
  block = false,
  className = '',
  onClick,
  type = 'button',
  icon,
  iconPosition = 'left',
  ...props 
}) => {
  const baseClasses = [
    'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-colors',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-ring',
    'disabled:opacity-50 disabled:pointer-events-none'
  ];

  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  // Variant classes
  const variantClasses = {
    primary: outline 
      ? 'border border-primary-500 text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950'
      : 'bg-primary-500 text-white hover:bg-primary-600',
    secondary: outline
      ? 'border border-secondary-500 text-secondary-500 hover:bg-secondary-50 dark:hover:bg-secondary-950'
      : 'bg-secondary-500 text-white hover:bg-secondary-600',
    success: outline
      ? 'border border-green-500 text-green-500 hover:bg-green-50 dark:hover:bg-green-950'
      : 'bg-green-500 text-white hover:bg-green-600',
    danger: outline
      ? 'border border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-950'
      : 'bg-red-500 text-white hover:bg-red-600',
    warning: outline
      ? 'border border-yellow-500 text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-950'
      : 'bg-yellow-500 text-white hover:bg-yellow-600'
  };

  const buttonClasses = [
    ...baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    block && 'w-full',
    loading && 'relative pointer-events-none',
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  const renderIcon = () => {
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
      {...props}
    >
      {icon && iconPosition === 'left' && renderIcon()}
      {children}
      {icon && iconPosition === 'right' && renderIcon()}
    </button>
  );
};

export default Button;