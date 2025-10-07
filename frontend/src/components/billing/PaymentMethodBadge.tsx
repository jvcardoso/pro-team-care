/**
 * PaymentMethodBadge Component
 * Displays payment method with appropriate icons
 */

import React from "react";
import { PaymentMethod } from "../../types/billing.types";

interface PaymentMethodBadgeProps {
  method: PaymentMethod;
  className?: string;
}

const PaymentMethodBadge: React.FC<PaymentMethodBadgeProps> = ({
  method,
  className = "",
}) => {
  const getMethodConfig = () => {
    switch (method) {
      case PaymentMethod.PIX:
        return {
          label: "PIX",
          color: "bg-purple-100 text-purple-800 border-purple-200",
          icon: "💳",
        };
      case PaymentMethod.TRANSFERENCIA:
        return {
          label: "Transferência",
          color: "bg-blue-100 text-blue-800 border-blue-200",
          icon: "🏦",
        };
      case PaymentMethod.TED:
        return {
          label: "TED",
          color: "bg-blue-100 text-blue-800 border-blue-200",
          icon: "🏦",
        };
      case PaymentMethod.BOLETO:
        return {
          label: "Boleto",
          color: "bg-orange-100 text-orange-800 border-orange-200",
          icon: "📄",
        };
      case PaymentMethod.CARTAO:
        return {
          label: "Cartão",
          color: "bg-green-100 text-green-800 border-green-200",
          icon: "💳",
        };
      case PaymentMethod.DINHEIRO:
        return {
          label: "Dinheiro",
          color: "bg-yellow-100 text-yellow-800 border-yellow-200",
          icon: "💰",
        };
      case PaymentMethod.DEPOSITO:
        return {
          label: "Depósito",
          color: "bg-indigo-100 text-indigo-800 border-indigo-200",
          icon: "🏛️",
        };
      default:
        return {
          label: "Outro",
          color: "bg-gray-100 text-gray-800 border-gray-200",
          icon: "❓",
        };
    }
  };

  const config = getMethodConfig();

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color} ${className}`}
      title={`Método de pagamento: ${config.label}`}
    >
      <span className="text-xs">{config.icon}</span>
      {config.label}
    </span>
  );
};

export default PaymentMethodBadge;
