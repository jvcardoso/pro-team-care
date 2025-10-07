import React from "react";
import { ArrowLeft } from "lucide-react";
import Card from "../ui/Card";
import Button from "../ui/Button";

interface ActionButton {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "danger";
  outline?: boolean;
  icon?: React.ReactNode;
}

interface MetricCard {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color?: string;
  onClick?: () => void;
}

interface Tab {
  key: string;
  label: string;
  shortLabel?: string;
  icon?: React.ReactNode;
}

interface EntityDetailsLayoutProps {
  // Header
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  statusBadge?: React.ReactNode;
  backButton?: {
    onClick: () => void;
    label?: string;
  };
  actionButtons?: ActionButton[];

  // Metrics (sidebar)
  metrics?: MetricCard[];

  // Tabs
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tab: string) => void;

  // Content
  children: React.ReactNode;

  // Loading/Error states
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

const EntityDetailsLayout: React.FC<EntityDetailsLayoutProps> = ({
  title,
  subtitle,
  icon,
  statusBadge,
  backButton,
  actionButtons = [],
  metrics = [],
  tabs,
  activeTab,
  onTabChange,
  children,
  loading = false,
  error = null,
  onRetry,
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Carregando...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        {onRetry && (
          <Button onClick={onRetry}>Tentar Novamente</Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header - Layout Otimizado */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        {/* Left Side: Icon + Title + Subtitle + Badge */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            {icon && <span className="text-primary flex-shrink-0">{icon}</span>}
            <h1 className="text-lg sm:text-2xl font-bold text-foreground break-words">
              {title}
            </h1>
          </div>
          {subtitle && (
            <p className="text-sm sm:text-base text-muted-foreground break-words">
              {subtitle}
            </p>
          )}
          {statusBadge && <div className="mt-2">{statusBadge}</div>}
        </div>

        {/* Right Side: Action Buttons (Voltar + Editar + Excluir) */}
        <div className="flex flex-wrap gap-2 sm:flex-shrink-0">
          {backButton && (
            <Button
              variant="secondary"
              outline
              onClick={backButton.onClick}
              icon={<ArrowLeft className="h-4 w-4" />}
            >
              {backButton.label || "Voltar"}
            </Button>
          )}
          {actionButtons.map((button, index) => (
            <Button
              key={index}
              variant={button.variant || "primary"}
              outline={button.outline}
              onClick={button.onClick}
              icon={button.icon}
            >
              {button.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Metrics Cards - Horizontal Layout */}
      {metrics.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics.map((metric, index) => (
            <div
              key={index}
              onClick={metric.onClick}
              className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 ${
                metric.onClick
                  ? "cursor-pointer hover:shadow-md transition-shadow"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground mb-1">
                    {metric.label}
                  </p>
                  <p className="text-2xl font-bold text-foreground">
                    {metric.value}
                  </p>
                </div>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${metric.color || "bg-blue-50 text-blue-600"}`}>
                  {metric.icon}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="overflow-x-auto scrollbar-hide">
          <div className="flex space-x-1 sm:space-x-4 lg:space-x-8 min-w-max">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => onTabChange(tab.key)}
                className={`py-3 sm:py-4 px-1 sm:px-2 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap ${
                  activeTab === tab.key
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }`}
              >
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.shortLabel || tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      {children}
    </div>
  );
};

export default EntityDetailsLayout;
