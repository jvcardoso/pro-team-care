/**
 * DataTableMetrics Component
 * Renders the main KPI metrics cards
 */

import React from "react";
import { DataTableMetric } from "../../../types/dataTable.types";

interface DataTableMetricsProps {
  metrics: DataTableMetric[];
}

export const DataTableMetrics: React.FC<DataTableMetricsProps> = ({
  metrics,
}) => {
  const getColorClasses = (color: string, type: "bg" | "text" | "icon") => {
    const colorMap = {
      blue: {
        bg: "bg-blue-100 dark:bg-blue-900",
        text: "text-blue-600 dark:text-blue-400",
        icon: "text-blue-600 dark:text-blue-300",
      },
      green: {
        bg: "bg-green-100 dark:bg-green-900",
        text: "text-green-600 dark:text-green-400",
        icon: "text-green-600 dark:text-green-300",
      },
      purple: {
        bg: "bg-purple-100 dark:bg-purple-900",
        text: "text-purple-600 dark:text-purple-400",
        icon: "text-purple-600 dark:text-purple-300",
      },
      yellow: {
        bg: "bg-yellow-100 dark:bg-yellow-900",
        text: "text-yellow-600 dark:text-yellow-400",
        icon: "text-yellow-600 dark:text-yellow-300",
      },
      red: {
        bg: "bg-red-100 dark:bg-red-900",
        text: "text-red-600 dark:text-red-400",
        icon: "text-red-600 dark:text-red-300",
      },
      gray: {
        bg: "bg-gray-100 dark:bg-gray-900",
        text: "text-gray-600 dark:text-gray-400",
        icon: "text-gray-600 dark:text-gray-300",
      },
    };

    return (
      colorMap[color as keyof typeof colorMap]?.[type] || colorMap.gray[type]
    );
  };

  return (
    <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.id}
          className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center">
            <div
              className={`p-3 ${getColorClasses(
                metric.color,
                "bg"
              )} rounded-lg`}
            >
              <div className={getColorClasses(metric.color, "icon")}>
                {metric.icon}
              </div>
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {metric.title}
              </p>
              <div className="flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {metric.value}
                </p>
                {metric.percentage && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    de {metric.percentage}%
                  </p>
                )}
              </div>
              {metric.subtitle && (
                <p
                  className={`text-xs ${getColorClasses(
                    metric.color,
                    "text"
                  )} mt-1`}
                >
                  {metric.subtitle}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DataTableMetrics;
