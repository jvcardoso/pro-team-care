/**
 * InvoiceStatusBadge Component
 * Displays invoice status with appropriate colors and icons
 */

import React from "react";
import { InvoiceStatus } from "../../types/billing.types";

interface InvoiceStatusBadgeProps {
  status: InvoiceStatus;
  isOverdue?: boolean;
  className?: string;
}

const InvoiceStatusBadge: React.FC<InvoiceStatusBadgeProps> = ({
  status,
  isOverdue = false,
  className = "",
}) => {
  const getStatusConfig = () => {
    // If overdue, show as overdue regardless of status
    if (
      isOverdue &&
      status !== InvoiceStatus.PAGA &&
      status !== InvoiceStatus.CANCELADA
    ) {
      return {
        label: "Em Atraso",
        color: "bg-red-100 text-red-800 border-red-200",
        icon: "⚠️",
      };
    }

    switch (status) {
      case InvoiceStatus.PENDENTE:
        return {
          label: "Pendente",
          color: "bg-yellow-100 text-yellow-800 border-yellow-200",
          icon: "⏳",
        };
      case InvoiceStatus.ENVIADA:
        return {
          label: "Enviada",
          color: "bg-blue-100 text-blue-800 border-blue-200",
          icon: "📤",
        };
      case InvoiceStatus.PAGA:
        return {
          label: "Paga",
          color: "bg-green-100 text-green-800 border-green-200",
          icon: "✅",
        };
      case InvoiceStatus.VENCIDA:
        return {
          label: "Vencida",
          color: "bg-red-100 text-red-800 border-red-200",
          icon: "❌",
        };
      case InvoiceStatus.CANCELADA:
        return {
          label: "Cancelada",
          color: "bg-gray-100 text-gray-800 border-gray-200",
          icon: "🚫",
        };
      case InvoiceStatus.EM_ATRASO:
        return {
          label: "Em Atraso",
          color: "bg-red-100 text-red-800 border-red-200",
          icon: "⚠️",
        };
      default:
        return {
          label: "Desconhecido",
          color: "bg-gray-100 text-gray-800 border-gray-200",
          icon: "❓",
        };
    }
  };

  const config = getStatusConfig();

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color} ${className}`}
      title={`Status: ${config.label}`}
    >
      <span className="text-xs">{config.icon}</span>
      {config.label}
    </span>
  );
};

export default InvoiceStatusBadge;
