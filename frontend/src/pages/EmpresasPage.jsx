import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { companiesService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import AccessDeniedError from "../components/error/AccessDeniedError";
import useErrorHandler from "../hooks/useErrorHandler";
import DataTableTemplate from "../components/shared/DataTable/DataTableTemplate";
import { useDataTable } from "../hooks/useDataTable";
import { createCompaniesConfig } from "../config/tables/companies.config";
import CompanyForm from "../components/forms/CompanyForm";
import CompanyDetails from "../components/views/CompanyDetails";
import Button from "../components/ui/Button";
import { Plus } from "lucide-react";

const EmpresasPage = () => {
  return (
    <PageErrorBoundary pageName="Empresas">
      <EmpresasPageContent />
    </PageErrorBoundary>
  );
};

const EmpresasPageContent = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { id } = useParams();
  const {
    handleError,
    isAccessDenied,
    hasError,
    userMessage,
    statusCode,
    canRetry,
  } = useErrorHandler();

  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);

  const handleAddCompany = () => {
    setCurrentView("create");
  };

  // Initialize data table hook with navigate
  const dataTableProps = useDataTable({
    config: {
      ...createCompaniesConfig(navigate),
      onAdd: handleAddCompany,
    },
    initialData: companies,
  });

  // Verificar parâmetros da URL ao carregar a página
  useEffect(() => {
    const companyIdParam = searchParams.get("companyId");
    const action = searchParams.get("action");
    const view = searchParams.get("view");

    // Se há um ID na URL, mostrar detalhes da empresa
    if (id) {
      setSelectedCompanyId(parseInt(id));
      setCurrentView("details");
    } else if (view === "create") {
      setCurrentView("create");
      setSelectedCompanyId(null);
    } else if (companyIdParam) {
      setSelectedCompanyId(parseInt(companyIdParam));
      if (action === "edit") {
        setCurrentView("edit");
      } else {
        setCurrentView("details");
      }
    }
  }, [searchParams, id]);

  // Load companies data
  useEffect(() => {
    if (currentView !== "list") return;

    const loadCompanies = async () => {
      try {
        setLoading(true);
        const response = await companiesService.getCompanies({
          skip: 0,
          limit: 1000, // Load more for the table
        });
        setCompanies(Array.isArray(response) ? response : []);
      } catch (error) {
        console.error("Erro ao carregar empresas:", error);
        handleError(error);
        setCompanies([]);
      } finally {
        setLoading(false);
      }
    };

    loadCompanies();
  }, [currentView]);

  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedCompanyId(null);
    navigate("/admin/empresas");
  };

  const handleSave = (redirectToDetails = false, companyId = null) => {
    if (redirectToDetails && companyId) {
      setSelectedCompanyId(companyId);
      setCurrentView("details");
      navigate(`/admin/empresas/${companyId}?tab=faturamento`);
    } else {
      setCurrentView("list");
      setSelectedCompanyId(null);
      navigate("/admin/empresas");
    }
  };

  const handleCancel = () => {
    setCurrentView("list");
    setSelectedCompanyId(null);
    navigate("/admin/empresas");
  };

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    const companyIdToPass = currentView === "create" ? null : selectedCompanyId;

    return (
      <CompanyForm
        companyId={companyIdToPass}
        onSave={() => handleSave(false)}
        onCancel={handleCancel}
        onRedirectToDetails={(companyId) => handleSave(true, companyId)}
      />
    );
  }

  if (currentView === "details") {
    return (
      <CompanyDetails
        companyId={selectedCompanyId}
        onBack={handleBackToList}
        onEdit={() => setCurrentView("edit")}
        onDelete={handleBackToList}
      />
    );
  }

  // Default: list view using DataTableTemplate
  return (
    <div className="space-y-6">
      <DataTableTemplate
        config={createCompaniesConfig(navigate)}
        tableData={dataTableProps}
      />
    </div>
  );
};

export default EmpresasPage;
