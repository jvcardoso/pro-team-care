/**
 * Subscription Plans Page
 * Página completa de gestão de planos de assinatura usando DataTableTemplate
 */

import React, { useState } from 'react';
import DataTableTemplate from '../components/shared/DataTable/DataTableTemplate';
import SubscriptionPlanModal from '../components/billing/SubscriptionPlanModal';
import SubscriptionPlanViewModal from '../components/billing/SubscriptionPlanViewModal';
import { useSubscriptionPlans } from '../hooks/useSubscriptionPlans';
import { useCompanyBillingData, CompanyBillingData } from '../hooks/useCompanyBillingData';
import { createSubscriptionPlansConfig } from '../config/tables/subscription-plans.config';
import { createCompanyBillingConfig } from '../config/tables/company-billing.config';
import type { SubscriptionPlan } from '../types/b2b-billing.types';

const SubscriptionPlansPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'plans' | 'company-plans'>('plans');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [viewPlan, setViewPlan] = useState<SubscriptionPlan | null>(null);

  const handleCreatePlan = () => {
    setSelectedPlan(null);
    setIsModalOpen(true);
  };

  const handleEditPlan = (plan: SubscriptionPlan) => {
    setSelectedPlan(plan);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedPlan(null);
  };

  const handleModalSuccess = () => {
    setIsModalOpen(false);
    setSelectedPlan(null);
    // Reload data will be handled by the hook
  };

  const handleViewPlan = (plan: SubscriptionPlan) => {
    setViewPlan(plan);
    setIsViewModalOpen(true);
  };

  const handleViewModalClose = () => {
    setIsViewModalOpen(false);
    setViewPlan(null);
  };

  const handleViewCompany = (company: CompanyBillingData) => {
    // Navigate to company details page (informações tab)
    window.location.href = `/admin/empresas/${company.id}?tab=informacoes`;
  };

  // Use the subscription plans hook
  const tableData = useSubscriptionPlans({
    onCreatePlan: handleCreatePlan,
    onEditPlan: handleEditPlan,
    onViewPlan: handleViewPlan,
    onDeletePlan: (_plan) => {
      // The delete logic is handled in the hook
    },
  });

  // Use the company billing data hook
  const companyBillingTableData = useCompanyBillingData();

  return (
    <div className="p-6">
      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('plans')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'plans'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💳 Planos
            </button>
            <button
              onClick={() => setActiveTab('company-plans')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'company-plans'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🏢 Empresa X Planos
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'plans' && (
        <>
          <DataTableTemplate<SubscriptionPlan>
            config={createSubscriptionPlansConfig(handleCreatePlan, handleEditPlan, handleViewPlan)}
            tableData={tableData}
            loading={tableData.loading}
          />

          <SubscriptionPlanModal
            isOpen={isModalOpen}
            onClose={handleModalClose}
            onSuccess={handleModalSuccess}
            plan={selectedPlan}
          />

          <SubscriptionPlanViewModal
            isOpen={isViewModalOpen}
            onClose={handleViewModalClose}
            plan={viewPlan}
          />
        </>
      )}

      {activeTab === 'company-plans' && (
        <DataTableTemplate<CompanyBillingData>
          config={createCompanyBillingConfig(handleViewCompany)}
          tableData={companyBillingTableData}
          loading={companyBillingTableData.loading}
        />
      )}
    </div>
  );
};

export default SubscriptionPlansPage;
