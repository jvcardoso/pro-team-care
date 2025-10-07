import React from "react";
import { useNavigate } from "react-router-dom";
import B2BBillingDashboard from "../components/billing/B2BBillingDashboard";
import type { ProTeamCareInvoice } from "../types/b2b-billing.types";

const B2BBillingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleCompanyClick = (companyId: number) => {
    navigate(`/empresas/${companyId}`);
  };

  const handleInvoiceClick = (invoice: ProTeamCareInvoice) => {
    // Implementar navegação para detalhes da fatura ou modal
    console.log("Visualizar fatura:", invoice);
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <B2BBillingDashboard
        refreshInterval={300000} // 5 minutos
        onCompanyClick={handleCompanyClick}
        onInvoiceClick={handleInvoiceClick}
      />
    </div>
  );
};

export default B2BBillingPage;
