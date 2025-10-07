/**
 * BillingMetricsCards Component
 * Displays key billing metrics in card format
 */

import React from "react";
import { BillingMetrics } from "../../types/billing.types";
import billingService from "../../services/billingService";

interface BillingMetricsCardsProps {
  metrics: BillingMetrics;
  loading?: boolean;
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color: string;
  trend?: "up" | "down" | "neutral";
  percentage?: number;
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color,
  trend,
  percentage,
  loading = false,
}) => {
  const getTrendIcon = () => {
    if (!trend || !percentage) return null;

    switch (trend) {
      case "up":
        return <span className="text-green-600">↗️ {percentage}%</span>;
      case "down":
        return <span className="text-red-600">↘️ {percentage}%</span>;
      default:
        return <span className="text-gray-600">→ {percentage}%</span>;
    }
  };

  const getColorClasses = () => {
    switch (color) {
      case "blue":
        return "bg-blue-50 border-blue-200";
      case "green":
        return "bg-green-50 border-green-200";
      case "yellow":
        return "bg-yellow-50 border-yellow-200";
      case "red":
        return "bg-red-50 border-red-200";
      case "purple":
        return "bg-purple-50 border-purple-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  if (loading) {
    return (
      <div className={`rounded-lg border-2 p-6 ${getColorClasses()}`}>
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-2">
            <div className="h-4 bg-gray-300 rounded w-24"></div>
            <div className="h-6 w-6 bg-gray-300 rounded"></div>
          </div>
          <div className="h-8 bg-gray-300 rounded w-32 mb-1"></div>
          <div className="h-3 bg-gray-300 rounded w-20"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border-2 p-6 ${getColorClasses()}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
        </div>
        {getTrendIcon() && (
          <div className="text-sm font-medium">{getTrendIcon()}</div>
        )}
      </div>
    </div>
  );
};

const BillingMetricsCards: React.FC<BillingMetricsCardsProps> = ({
  metrics,
  loading = false,
  className = "",
}) => {
  const cards = [
    {
      title: "Faturas Pendentes",
      value: metrics.total_pending_invoices,
      subtitle: billingService.formatCurrency(metrics.total_pending_amount),
      icon: "📄",
      color: "yellow",
    },
    {
      title: "Faturas Vencidas",
      value: metrics.total_overdue_invoices,
      subtitle: billingService.formatCurrency(metrics.total_overdue_amount),
      icon: "⚠️",
      color: "red",
    },
    {
      title: "Recebido este Mês",
      value: billingService.formatCurrency(metrics.total_paid_this_month),
      subtitle: "Pagamentos confirmados",
      icon: "💰",
      color: "green",
    },
    {
      title: "Faturado este Mês",
      value: billingService.formatCurrency(metrics.total_expected_this_month),
      subtitle: "Total esperado",
      icon: "📊",
      color: "blue",
    },
    {
      title: "Taxa de Cobrança",
      value: `${metrics.collection_rate_percentage.toFixed(1)}%`,
      subtitle: "Eficiência de cobrança",
      icon: "🎯",
      color:
        metrics.collection_rate_percentage >= 80
          ? "green"
          : metrics.collection_rate_percentage >= 60
          ? "yellow"
          : "red",
    },
    {
      title: "Prazo Médio",
      value: metrics.average_payment_delay_days
        ? `${metrics.average_payment_delay_days} dias`
        : "N/A",
      subtitle: "Atraso no pagamento",
      icon: "⏱️",
      color: "purple",
    },
  ];

  return (
    <div
      className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}
    >
      {cards.map((card, index) => (
        <MetricCard
          key={index}
          title={card.title}
          value={card.value}
          subtitle={card.subtitle}
          icon={card.icon}
          color={card.color}
          loading={loading}
        />
      ))}
    </div>
  );
};

export default BillingMetricsCards;
