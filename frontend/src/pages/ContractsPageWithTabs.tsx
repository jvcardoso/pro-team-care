import React, { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageErrorBoundary } from "../components/error";
import ContractDashboard from "../components/views/ContractDashboard";
import ContractsPage from "./ContractsPage";

const ContractsPageWithTabs: React.FC = () => {
  return (
    <PageErrorBoundary pageName="Contratos">
      <ContractsPageContent />
    </PageErrorBoundary>
  );
};

const ContractsPageContent: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get("tab") || "dashboard";

  const handleTabChange = (tab: string) => {
    setSearchParams({ tab });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Gestão de Contratos
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Dashboard executivo e gestão completa de contratos Home Care
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => handleTabChange("dashboard")}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${
                currentTab === "dashboard"
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }
            `}
          >
            📊 Dashboard
          </button>
          <button
            onClick={() => handleTabChange("lista")}
            className={`
              whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
              ${
                currentTab === "lista"
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300"
              }
            `}
          >
            📋 Lista de Contratos
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {currentTab === "dashboard" && <ContractDashboard />}
        {currentTab === "lista" && <ContractsPage />}
      </div>
    </div>
  );
};

export default ContractsPageWithTabs;
