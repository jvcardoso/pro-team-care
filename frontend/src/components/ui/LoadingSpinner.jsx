/**
 * Componente LoadingSpinner - Indicador de loading
 * Spinner animado reutilizável
 */

import React from "react";

/**
 * Componente LoadingSpinner
 *
 * @param {string} size - Tamanho do spinner (sm, md, lg)
 * @param {string} className - Classes CSS adicionais
 */
export const LoadingSpinner = ({ size = "md", className = "", ...props }) => {
  // Classes de tamanho
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
  };

  const appliedSize = sizeClasses[size] || sizeClasses.md;

  return (
    <div
      className={`${appliedSize} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${className}`}
      role="status"
      aria-label="Carregando"
      {...props}
    >
      <span className="sr-only">Carregando...</span>
    </div>
  );
};

export default LoadingSpinner;
