import React from "react";

const MetricCard = ({
  icon,
  title,
  value,
  subtitle,
  trend,
  color = "blue",
}) => {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
    green:
      "bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400",
    purple:
      "bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
    orange:
      "bg-orange-50 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400",
    red: "bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400",
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="card-content">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
              {title}
            </p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
            {trend && (
              <p
                className={`text-xs mt-2 ${
                  trend >= 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)} no mês
              </p>
            )}
          </div>
          {icon && (
            <div
              className={`w-12 h-12 rounded-lg ${colorClasses[color]} flex items-center justify-center text-2xl`}
            >
              {icon}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
