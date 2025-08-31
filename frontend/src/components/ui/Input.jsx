import React, { forwardRef } from 'react';
import { Star } from 'lucide-react';

const Input = forwardRef(({ 
  label,
  error,
  helper,
  required = false,
  size = 'md',
  variant = 'default',
  leftIcon,
  rightIcon,
  className = '',
  containerClassName = '',
  type = 'text',
  ...props 
}, ref) => {
  const baseClasses = [
    'w-full border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
    'bg-input text-foreground placeholder-muted-foreground',
    'border-border focus:border-ring focus:ring-ring'
  ];

  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-base'
  };

  // Variant classes
  const variantClasses = {
    default: '',
    success: 'border-green-500 focus:border-green-500 focus:ring-green-500',
    warning: 'border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500',
    error: 'border-red-500 focus:border-red-500 focus:ring-red-500'
  };

  const inputClasses = [
    ...baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    error && 'border-red-500 focus:border-red-500 focus:ring-red-500',
    leftIcon && 'pl-10',
    rightIcon && 'pr-10',
    className
  ].filter(Boolean).join(' ');

  const containerClasses = [
    'w-full',
    containerClassName
  ].filter(Boolean).join(' ');

  return (
    <div className={containerClasses}>
      {label && (
        <label className="flex items-center text-sm font-medium text-foreground mb-2">
          {label}
          {required && <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />}
        </label>
      )}
      
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-muted-foreground">
              {leftIcon}
            </span>
          </div>
        )}
        
        <input
          ref={ref}
          type={type}
          className={inputClasses}
          {...props}
          value={props.value ?? ''}
        />
        
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-muted-foreground">
              {rightIcon}
            </span>
          </div>
        )}
      </div>
      
      {error && (
        <p className="mt-1 text-sm text-red-500">
          {error}
        </p>
      )}
      
      {helper && !error && (
        <p className="mt-1 text-sm text-muted-foreground">
          {helper}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;