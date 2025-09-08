/**
 * Componente Alert - Alertas e notificações
 * Suporta diferentes tipos e estilos
 */

import React from "react";
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from "lucide-react";

/**
 * Componente Alert
 *
 * @param {string} type - Tipo do alerta (success, error, warning, info)
 * @param {string} title - Título do alerta
 * @param {React.ReactNode} children - Conteúdo do alerta
 * @param {boolean} dismissible - Se pode ser fechado
 * @param {Function} onDismiss - Callback para fechar
 * @param {string} className - Classes CSS adicionais
 */
export const Alert = ({
  type = "info",
  title,
  children,
  dismissible = false,
  onDismiss,
  className = "",
  ...props
}) => {
  // Configurações por tipo
  const typeConfig = {
    success: {
      icon: CheckCircle,
      classes:
        "bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400",
      iconClasses: "text-green-600 dark:text-green-400",
    },
    error: {
      icon: AlertCircle,
      classes:
        "bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400",
      iconClasses: "text-red-600 dark:text-red-400",
    },
    warning: {
      icon: AlertTriangle,
      classes:
        "bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-400",
      iconClasses: "text-yellow-600 dark:text-yellow-400",
    },
    info: {
      icon: Info,
      classes:
        "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400",
      iconClasses: "text-blue-600 dark:text-blue-400",
    },
  };

  const config = typeConfig[type] || typeConfig.info;
  const IconComponent = config.icon;

  return (
    <div
      className={`border rounded-lg p-4 ${config.classes} ${className}`}
      role="alert"
      {...props}
    >
      <div className="flex items-start space-x-3">
        {/* Ícone */}
        <IconComponent
          size={20}
          className={`flex-shrink-0 mt-0.5 ${config.iconClasses}`}
        />

        {/* Conteúdo */}
        <div className="flex-1 min-w-0">
          {title && <h4 className="font-medium mb-1">{title}</h4>}
          {children && <div className="text-sm">{children}</div>}
        </div>

        {/* Botão de fechar */}
        {dismissible && (
          <button
            onClick={onDismiss}
            className={`flex-shrink-0 p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/5 ${config.iconClasses}`}
            aria-label="Fechar alerta"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
};

export default Alert;
