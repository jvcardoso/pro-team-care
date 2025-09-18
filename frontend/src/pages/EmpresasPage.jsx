import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { companiesService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import AccessDeniedError from "../components/error/AccessDeniedError";
import useErrorHandler from "../hooks/useErrorHandler";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import ActionDropdown from "../components/ui/ActionDropdown";
import CompanyForm from "../components/forms/CompanyForm";
import CompanyDetails from "../components/views/CompanyDetails";
import CompanyMobileCard from "../components/mobile/CompanyMobileCard";
import { getStatusBadge, getStatusLabel } from "../utils/statusUtils";
import { formatTaxId } from "../utils/formatters";
import { notify } from "../utils/notifications.jsx";
import {
  Building,
  Search,
  Plus,
  Filter,
  Phone,
  Mail,
  MapPin,
  Edit,
  Eye,
  Trash2,
  Calendar,
} from "lucide-react";

const EmpresasPage = () => {
  return (
    <PageErrorBoundary pageName="Empresas">
      <EmpresasPageContent />
    </PageErrorBoundary>
  );
};

const EmpresasPageContent = () => {
  // Add error boundary logging
  if (typeof window !== "undefined") {
    window.addEventListener("error", (e) => {
      console.error("Page Error:", e.error);
    });
  }
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
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("todos");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);

  // Verificar parâmetros da URL ao carregar a página
  useEffect(() => {
    const companyIdParam = searchParams.get("companyId");

    // Se há um ID na URL, mostrar detalhes da empresa
    if (id) {
      console.log("🔍 ID da empresa detectado na URL:", id);
      setSelectedCompanyId(parseInt(id));
      setCurrentView("details");
    } else if (companyIdParam) {
      console.log("🔍 Empresa encontrada na URL (param):", companyIdParam);
      setSelectedCompanyId(parseInt(companyIdParam));
      setCurrentView("details");
    }
  }, [searchParams, id]);

  // Debounce search term
  useEffect(() => {
    if (currentView !== "list") return;

    const timeoutId = setTimeout(
      () => {
        loadCompanies();
        loadTotalCount();
      },
      searchTerm ? 500 : 0
    ); // 500ms debounce for search, immediate for other filters

    return () => clearTimeout(timeoutId);
  }, [currentPage, searchTerm, filterStatus, currentView]);

  const loadCompanies = async () => {
    try {
      setLoading(true);

      const params = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && { status: filterStatus }),
      };

      console.log("Loading companies with params:", params);
      const data = await companiesService.getCompanies(params);
      console.log("Companies loaded:", data?.length || 0);

      setCompanies(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error loading companies:", err);
      handleError(err);
      setCompanies([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const loadTotalCount = async () => {
    try {
      const params = {
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && { status: filterStatus }),
      };
      const data = await companiesService.getCompaniesCount(params);
      setTotalCount(data.total);
    } catch (err) {
      console.error("Erro ao carregar contagem:", err);
    }
  };

  const handleDelete = async (companyId) => {
    const company = companies.find((c) => c.id === companyId);
    const companyName = company?.name || "esta empresa";

    const executeDelete = async () => {
      try {
        await companiesService.deleteCompany(companyId);
        notify.success("Empresa excluída com sucesso!");
        loadCompanies();
        loadTotalCount();
      } catch (err) {
        notify.error("Erro ao excluir empresa");
        console.error(err);
      }
    };

    notify.confirmDelete(
      "Excluir Empresa",
      `Tem certeza que deseja excluir a empresa "${companyName}"?`,
      executeDelete
    );
  };

  const handleCreate = () => {
    // Garantir limpeza completa do estado antes de criar
    setSelectedCompanyId(null);
    setCurrentView("create");
    // Pequeno delay para garantir que o estado seja atualizado
    setTimeout(() => {
      if (selectedCompanyId !== null) {
        console.warn(
          "selectedCompanyId não foi limpo adequadamente, forçando limpeza"
        );
        setSelectedCompanyId(null);
      }
    }, 0);
  };

  const handleEdit = (companyId) => {
    setSelectedCompanyId(companyId);
    setCurrentView("edit");
  };

  const handleView = (companyId) => {
    // Usar URL params em vez de estado interno (Padrão C)
    navigate(`/admin/empresas/${companyId}?tab=informacoes`);
  };

  const handleSave = (redirectToDetails = false, companyId = null) => {
    console.log("📝 handleSave chamado:", { redirectToDetails, companyId });
    if (redirectToDetails && companyId) {
      console.log(
        "🔄 Navegando para detalhes da empresa na aba estabelecimentos:",
        companyId
      );
      // Definir estado para mostrar detalhes da empresa na aba estabelecimentos
      setSelectedCompanyId(companyId);
      setCurrentView("details");
      // Também atualizar a URL para refletir o estado
      navigate(`/admin/empresas?tab=estabelecimentos&companyId=${companyId}`, {
        replace: true,
      });
    } else {
      console.log("📋 Voltando para lista");
      setCurrentView("list");
      setSelectedCompanyId(null);
      loadCompanies();
      loadTotalCount();
      // Limpar parâmetros da URL
      navigate("/admin/empresas", { replace: true });
    }
  };

  const handleCancel = () => {
    setCurrentView("list");
    setSelectedCompanyId(null);
    // Limpar parâmetros da URL
    navigate("/admin/empresas", { replace: true });
    // Limpar qualquer estado residual
    setTimeout(() => {
      if (currentView !== "list" || selectedCompanyId !== null) {
        console.warn("Estado não foi limpo adequadamente no cancelamento");
        setCurrentView("list");
        setSelectedCompanyId(null);
      }
    }, 0);
  };

  const handleBack = () => {
    setCurrentView("list");
    setSelectedCompanyId(null);
    // Limpar parâmetros da URL ao voltar para a lista
    navigate("/admin/empresas", { replace: true });
  };

  const handleDeleteFromDetails = () => {
    // Voltar para lista após exclusão
    navigate("/admin/empresas", { replace: true });
    loadCompanies();
    loadTotalCount();
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    // Garantir que companyId seja null no modo de criação
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
    // Obter a aba inicial dos parâmetros da URL, padrão para 'informacoes'
    const initialTab = searchParams.get("tab") || "informacoes";

    return (
      <CompanyDetails
        companyId={selectedCompanyId}
        onEdit={handleEdit}
        onBack={handleBack}
        onDelete={handleDeleteFromDetails}
        initialTab={initialTab}
      />
    );
  }

  // List view loading states
  if (loading && companies.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando empresas...</p>
        </div>
      </div>
    );
  }

  // Handle error states with new error handling system
  if (hasError && companies.length === 0) {
    if (isAccessDenied) {
      return (
        <AccessDeniedError
          title="Acesso Negado às Empresas"
          message="Você não possui permissão para visualizar as empresas do sistema. Entre em contato com o administrador para solicitar acesso a esta funcionalidade."
          resource="empresas do sistema"
          action="visualizar"
          onRetry={() => window.location.reload()}
        />
      );
    } else {
      return (
        <div className="space-y-6">
          <div className="text-center py-12">
            <p className="text-red-600 mb-4">{userMessage}</p>
            {canRetry && (
              <Button onClick={loadCompanies}>Tentar Novamente</Button>
            )}
          </div>
        </div>
      );
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Empresas</h1>
          <p className="text-muted-foreground">
            Gerencie as empresas cadastradas no sistema
          </p>
        </div>
        <Button
          onClick={handleCreate}
          icon={<Plus className="h-4 w-4" />}
          className="shrink-0"
        >
          <span className="hidden sm:inline">Nova Empresa</span>
          <span className="sm:hidden">Nova</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          {/* Search and Status Filter */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="Buscar por nome, razão social ou CNPJ..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="flex-1 min-w-0"
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none min-w-0 sm:w-48"
            >
              <option value="todos">Todos os status</option>
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
              <option value="suspended">Suspenso</option>
            </select>
          </div>

          {/* Additional Filters Button */}
          <div className="flex justify-end">
            <Button
              variant="secondary"
              outline
              icon={<Filter className="h-4 w-4" />}
            >
              <span className="hidden sm:inline">Filtros Avançados</span>
              <span className="sm:hidden">Filtros</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Building className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total Empresas</p>
              <p className="text-2xl font-bold text-foreground">{totalCount}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Building className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativas</p>
              <p className="text-2xl font-bold text-foreground">
                {companies.filter((c) => c.status === "active").length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-gray-100 dark:bg-gray-900 rounded-lg">
              <Building className="h-6 w-6 text-gray-600 dark:text-gray-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Inativas</p>
              <p className="text-2xl font-bold text-foreground">
                {companies.filter((c) => c.status === "inactive").length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <Building className="h-6 w-6 text-red-600 dark:text-red-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Suspensas</p>
              <p className="text-2xl font-bold text-foreground">
                {companies.filter((c) => c.status === "suspended").length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Companies Table */}
      <Card title="Lista de Empresas">
        {/* Desktop Table */}
        <div className="hidden lg:block">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Empresa
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    CNPJ
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Contatos
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Criado em
                  </th>
                  <th className="relative py-3 px-4">
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr
                    key={company.id}
                    className="border-b border-border hover:bg-muted/50"
                  >
                    <td className="py-3 px-4">
                      <div>
                        <p className="font-medium text-foreground">
                          {company.name}
                        </p>
                        {company.trade_name &&
                          company.trade_name !== company.name && (
                            <p className="text-sm text-muted-foreground">
                              {company.trade_name}
                            </p>
                          )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-foreground font-mono text-sm">
                      {formatTaxId(company.tax_id)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Phone className="h-3 w-3 mr-1" />
                          {company.phones_count} telefone
                          {company.phones_count !== 1 ? "s" : ""}
                        </div>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Mail className="h-3 w-3 mr-1" />
                          {company.emails_count} email
                          {company.emails_count !== 1 ? "s" : ""}
                        </div>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <MapPin className="h-3 w-3 mr-1" />
                          {company.addresses_count} endereço
                          {company.addresses_count !== 1 ? "s" : ""}
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={getStatusBadge(company.status)}>
                        {getStatusLabel(company.status)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      {new Date(company.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-center relative">
                        <ActionDropdown>
                          <ActionDropdown.Item
                            icon={<Eye className="h-4 w-4" />}
                            onClick={() => handleView(company.id)}
                          >
                            Ver Detalhes
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<Edit className="h-4 w-4" />}
                            onClick={() => handleEdit(company.id)}
                          >
                            Editar
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<Trash2 className="h-4 w-4" />}
                            onClick={() => handleDelete(company.id)}
                            variant="danger"
                          >
                            Excluir
                          </ActionDropdown.Item>
                        </ActionDropdown>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tablet: Cards compactos */}
        <div className="hidden md:block lg:hidden space-y-3 p-4">
          {companies.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhuma empresa encontrada
              </p>
            </div>
          ) : (
            companies.map((company, index) => (
              <div
                key={company?.id || index}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {company.name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate font-mono">
                        {formatTaxId(company.tax_id)}
                      </p>
                      {company.trade_name &&
                        company.trade_name !== company.name && (
                          <p className="text-xs text-gray-400 dark:text-gray-500 truncate">
                            {company.trade_name}
                          </p>
                        )}
                    </div>
                    <div className="text-center">
                      <span
                        className={getStatusBadge(company.status || "active")}
                      >
                        {getStatusLabel(company.status || "active")}
                      </span>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(company.created_at).toLocaleDateString(
                          "pt-BR"
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <ActionDropdown>
                      <ActionDropdown.Item
                        icon={<Eye className="h-4 w-4" />}
                        onClick={() => handleView(company.id)}
                      >
                        Ver Detalhes
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<Edit className="h-4 w-4" />}
                        onClick={() => handleEdit(company.id)}
                      >
                        Editar
                      </ActionDropdown.Item>
                      <ActionDropdown.Item
                        icon={<Trash2 className="h-4 w-4" />}
                        onClick={() => handleDelete(company.id)}
                        variant="danger"
                      >
                        Excluir
                      </ActionDropdown.Item>
                    </ActionDropdown>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Mobile Cards */}
        <div className="md:hidden space-y-4">
          {companies.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhuma empresa encontrada
              </p>
            </div>
          ) : (
            companies.map((company, index) => (
              <CompanyMobileCard
                key={company?.id || index}
                company={company}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                getStatusBadge={getStatusBadge}
                getStatusLabel={getStatusLabel}
                formatTaxId={formatTaxId}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Mostrando{" "}
              {Math.min((currentPage - 1) * itemsPerPage + 1, totalCount)} a{" "}
              {Math.min(currentPage * itemsPerPage, totalCount)} de {totalCount}{" "}
              empresas
            </p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                outline
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                outline
                size="sm"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Próxima
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default EmpresasPage;
