/**
 * Badge visual para status de ativação de empresa
 *
 * Exibe o status atual do processo de ativação com cores e ícones
 */

import React from "react";
import {
  getStatusLabel,
  getStatusBadgeClasses,
  getStatusIcon,
} from "../../services/companyActivationService";

interface CompanyActivationBadgeProps {
  status:
    | "pending_contract"
    | "contract_signed"
    | "pending_user"
    | "active"
    | "suspended";
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const CompanyActivationBadge: React.FC<CompanyActivationBadgeProps> = ({
  status,
  showIcon = true,
  size = "md",
  className = "",
}) => {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
    lg: "px-3 py-1.5 text-base",
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        font-medium rounded-full
        ${getStatusBadgeClasses(status)}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {showIcon && <span>{getStatusIcon(status)}</span>}
      <span>{getStatusLabel(status)}</span>
    </span>
  );
};

export default CompanyActivationBadge;
