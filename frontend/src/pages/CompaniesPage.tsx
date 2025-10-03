/**
 * Companies Page
 * Página completa de gestão de empresas usando o DataTableTemplate
 */

import React, { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { DataTableTemplate } from "../components/shared/DataTable/DataTableTemplate";
import { useCompaniesDataTable } from "../hooks/useCompaniesDataTable";
import { createCompaniesConfig } from "../config/tables/companies.config";
import CompanyDetails from "../components/views/CompanyDetails";
import { companiesService } from "../services/companiesService";

export const CompaniesPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  console.log("🏢 CompaniesPage renderizada com ID:", id);

  // Buscar nome da empresa para breadcrumb quando houver ID
  useEffect(() => {
    if (id) {
      const loadCompanyName = async () => {
        try {
          const company = await companiesService.getById(parseInt(id));
          if (company?.people?.name) {
            localStorage.setItem(`company_name_${id}`, company.people.name);
          }
        } catch (error) {
          console.error("Erro ao buscar nome da empresa:", error);
        }
      };
      loadCompanyName();
    }
  }, [id]);

  // Se tem ID na URL, mostrar detalhes da empresa
  if (id) {
    console.log("📋 Mostrando detalhes da empresa ID:", id);
    return <CompanyDetails />;
  }

  // Caso contrário, mostrar lista de empresas
  const tableData = useCompaniesDataTable({
    initialPageSize: 10,
  });

  // Criar configuração com navegação
  const companiesConfig = createCompaniesConfig(navigate);

  return (
    <div className="p-6">
      <DataTableTemplate config={companiesConfig} tableData={tableData} />
    </div>
  );
};

export default CompaniesPage;
