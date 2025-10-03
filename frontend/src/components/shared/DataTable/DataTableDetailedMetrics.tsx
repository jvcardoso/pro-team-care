/**
 * DataTableDetailedMetrics Component
 * Renders the collapsible detailed metrics panel
 */

import React from "react";
import { DataTableConfig } from "../../../types/dataTable.types";

interface DataTableDetailedMetricsProps {
  detailedMetrics?: DataTableConfig["metrics"]["detailed"];
  showDetailedMetrics: boolean;
  onToggle: () => void;
}

export const DataTableDetailedMetrics: React.FC<
  DataTableDetailedMetricsProps
> = ({ detailedMetrics, showDetailedMetrics, onToggle }) => {
  if (!detailedMetrics) return null;

  return (
    <div className="mb-6">
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full px-4 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 dark:hover:bg-gray-700 transition-colors"
      >
        <span className="flex items-center">
          <svg
            className="w-5 h-5 mr-2 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          {detailedMetrics.title}
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${
            showDetailedMetrics ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Collapsible Content */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          showDetailedMetrics ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Metrics Sections */}
          {detailedMetrics.sections.map((section, sectionIndex) => (
            <div
              key={sectionIndex}
              className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
            >
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                {section.title}
              </h3>
              <div className="space-y-2">
                {section.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex justify-between items-center"
                  >
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {item.title}
                    </span>
                    <div className="text-right">
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        {item.value}
                      </span>
                      {item.subtitle && (
                        <span className="text-xs text-gray-500 ml-1">
                          {item.subtitle}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Quick Actions */}
          {detailedMetrics.quickActions && (
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                ⚡ Ações Rápidas
              </h3>
              <div className="space-y-2">
                {detailedMetrics.quickActions.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.action}
                    className={`w-full text-left px-3 py-2 text-xs rounded-lg transition-colors ${getActionColorClasses(
                      action.color
                    )}`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function getActionColorClasses(color: string): string {
  const colorMap = {
    green:
      "text-green-700 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:text-green-300 dark:hover:bg-green-900/30",
    yellow:
      "text-yellow-700 bg-yellow-50 hover:bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-300 dark:hover:bg-yellow-900/30",
    blue: "text-blue-700 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-300 dark:hover:bg-blue-900/30",
    red: "text-red-700 bg-red-50 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-300 dark:hover:bg-red-900/30",
    purple:
      "text-purple-700 bg-purple-50 hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-300 dark:hover:bg-purple-900/30",
    gray: "text-gray-700 bg-gray-50 hover:bg-gray-100 dark:bg-gray-900/20 dark:text-gray-300 dark:hover:bg-gray-900/30",
  };

  return colorMap[color as keyof typeof colorMap] || colorMap.gray;
}

export default DataTableDetailedMetrics;
