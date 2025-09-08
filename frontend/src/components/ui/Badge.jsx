/**
 * Componente Badge - Badge para indicadores visuais
 * Suporta diferentes cores, tamanhos e variações
 */

import React from "react";

/**
 * Componente Badge
 *
 * @param {string} text - Texto do badge
 * @param {string} color - Cor do badge (classe CSS)
 * @param {string} size - Tamanho do badge (sm, md, lg)
 * @param {string} variant - Variação do badge (solid, outline)
 * @param {string} className - Classes CSS adicionais
 */
export const Badge = ({
  text,
  color = "bg-gray-500",
  size = "md",
  variant = "solid",
  className = "",
  ...props
}) => {
  if (!text) return null;

  // Classes de tamanho
  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-xs",
    md: "px-2 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  };

  // Classes de variação
  const variantClasses = {
    solid: `${color} text-white`,
    outline: `border border-current ${color.replace(
      "bg-",
      "text-"
    )} bg-transparent`,
  };

  const baseClasses = "inline-block rounded-full font-medium whitespace-nowrap";
  const appliedSize = sizeClasses[size] || sizeClasses.md;
  const appliedVariant = variantClasses[variant] || variantClasses.solid;

  return (
    <span
      className={`${baseClasses} ${appliedSize} ${appliedVariant} ${className}`}
      {...props}
    >
      {text}
    </span>
  );
};

export default Badge;
