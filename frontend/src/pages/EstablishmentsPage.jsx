import React, { useState, useEffect } from "react";
import { establishmentsService, companiesService } from "../services/api";
import { PageErrorBoundary } from "../components/error";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import ActionDropdown from "../components/ui/ActionDropdown";
import { getStatusBadge, getStatusLabel } from "../utils/statusUtils";
import { notify } from "../utils/notifications.jsx";
import {
  Building2,
  Search,
  Plus,
  Filter,
  MapPin,
  Edit,
  Eye,
  Building,
  UserCheck,
  UserX,
  ArrowUpDown,
  Calendar,
  Users,
} from "lucide-react";

const EstablishmentsPage = () => {
  return (
    <PageErrorBoundary pageName="Estabelecimentos">
      <EstablishmentsPageContent />
    </PageErrorBoundary>
  );
};

const EstablishmentsPageContent = () => {
  const [establishments, setEstablishments] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("todos");
  const [filterCompany, setFilterCompany] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'edit', 'details'
  const [selectedEstablishmentId, setSelectedEstablishmentId] = useState(null);

  // Opções de filtro
  const typeOptions = [
    { value: "", label: "Todos os tipos" },
    { value: "matriz", label: "Matriz" },
    { value: "filial", label: "Filial" },
    { value: "unidade", label: "Unidade" },
    { value: "posto", label: "Posto" },
  ];

  const categoryOptions = [
    { value: "", label: "Todas as categorias" },
    { value: "clinica", label: "Clínica" },
    { value: "hospital", label: "Hospital" },
    { value: "laboratorio", label: "Laboratório" },
    { value: "farmacia", label: "Farmácia" },
    { value: "consultorio", label: "Consultório" },
    { value: "upa", label: "UPA" },
    { value: "ubs", label: "UBS" },
    { value: "outro", label: "Outro" },
  ];

  useEffect(() => {
    if (currentView === "list") {
      loadEstablishments();
      loadTotalCount();
    }
  }, [currentPage, searchTerm, filterStatus, filterCompany, filterType, filterCategory, currentView]);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await companiesService.getCompanies({ 
        is_active: true, 
        page: 1, 
        size: 100 
      });
      setCompanies(response.companies || []);
    } catch (err) {
      console.error("Error loading companies:", err);
    }
  };

  const loadEstablishments = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: currentPage,
        size: itemsPerPage,
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && {
          is_active: filterStatus === "active",
        }),
        ...(filterCompany && { company_id: parseInt(filterCompany) }),
        ...(filterType && { type: filterType }),
        ...(filterCategory && { category: filterCategory }),
      };

      console.log("Loading establishments with params:", params);
      const response = await establishmentsService.getEstablishments(params);
      console.log("Establishments response:", response);

      const establishments = response?.establishments || response || [];
      setEstablishments(Array.isArray(establishments) ? establishments : []);
    } catch (err) {
      console.error("Error loading establishments:", err);
      setError(`Erro ao carregar estabelecimentos: ${err.message || "Erro desconhecido"}`);
      setEstablishments([]);
    } finally {
      setLoading(false);
    }
  };

  const loadTotalCount = async () => {
    try {
      const params = {
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== "todos" && {
          is_active: filterStatus === "active",
        }),
        ...(filterCompany && { company_id: parseInt(filterCompany) }),
        ...(filterType && { type: filterType }),
        ...(filterCategory && { category: filterCategory }),
      };
      const data = await establishmentsService.countEstablishments(params);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error("Erro ao carregar contagem:", err);
      setTotalCount(0);
    }
  };

  const handleToggleStatus = async (establishmentId, newStatus) => {
    const establishment = establishments.find((e) => e.id === establishmentId);
    const establishmentName = establishment?.person?.name || establishment?.code || "este estabelecimento";
    const action = newStatus ? "ativar" : "inativar";

    const executeToggle = async () => {
      try {
        await establishmentsService.toggleEstablishmentStatus(establishmentId, newStatus);
        notify.success(`Estabelecimento ${action === "ativar" ? "ativado" : "inativado"} com sucesso!`);
        loadEstablishments();
        loadTotalCount();
      } catch (err) {
        notify.error(`Erro ao ${action} estabelecimento`);
        console.error(err);
      }
    };

    notify.confirm(
      `${action === "ativar" ? "Ativar" : "Inativar"} Estabelecimento`,
      `Tem certeza que deseja ${action} o estabelecimento "${establishmentName}"?`,
      executeToggle
    );
  };

  const handleDelete = async (establishmentId) => {
    const establishment = establishments.find((e) => e.id === establishmentId);
    const establishmentName = establishment?.person?.name || establishment?.code || "este estabelecimento";

    const executeDelete = async () => {
      try {
        await establishmentsService.deleteEstablishment(establishmentId);
        notify.success("Estabelecimento excluído com sucesso!");
        loadEstablishments();
        loadTotalCount();
      } catch (err) {
        const errorMessage = err.response?.data?.detail || err.message || "Erro desconhecido";
        notify.error(`Erro ao excluir estabelecimento: ${errorMessage}`);
        console.error(err);
      }
    };

    notify.confirmDelete(
      "Excluir Estabelecimento",
      `Tem certeza que deseja excluir o estabelecimento "${establishmentName}"?`,
      executeDelete
    );
  };

  const handleCreate = () => {
    setSelectedEstablishmentId(null);
    setCurrentView("create");
  };

  const handleEdit = (establishmentId) => {
    setSelectedEstablishmentId(establishmentId);
    setCurrentView("edit");
  };

  const handleView = (establishmentId) => {
    setSelectedEstablishmentId(establishmentId);
    setCurrentView("details");
  };

  const handleSave = () => {
    setCurrentView("list");
    setSelectedEstablishmentId(null);
    loadEstablishments();
    loadTotalCount();
  };

  const handleCancel = () => {
    setCurrentView("list");
    setSelectedEstablishmentId(null);
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  // Render different views based on current state
  if (currentView === "create" || currentView === "edit") {
    // TODO: Implementar EstablishmentForm
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">
            {currentView === "create" ? "Novo Estabelecimento" : "Editar Estabelecimento"}
          </h1>
          <Button variant="secondary" onClick={handleCancel}>
            Voltar
          </Button>
        </div>
        <Card>
          <div className="p-8 text-center text-gray-500">
            Formulário de estabelecimento em desenvolvimento...
          </div>
        </Card>
      </div>
    );
  }

  if (currentView === "details") {
    // TODO: Implementar EstablishmentDetails
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Detalhes do Estabelecimento</h1>
          <Button variant="secondary" onClick={handleCancel}>
            Voltar
          </Button>
        </div>
        <Card>
          <div className="p-8 text-center text-gray-500">
            Detalhes do estabelecimento em desenvolvimento...
          </div>
        </Card>
      </div>
    );
  }

  // List view loading states
  if (loading && establishments.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Carregando estabelecimentos...</p>
        </div>
      </div>
    );
  }

  if (error && establishments.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={loadEstablishments}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Estabelecimentos</h1>
          <p className="text-muted-foreground">
            Gerencie os estabelecimentos cadastrados no sistema
          </p>
        </div>
        <Button
          onClick={handleCreate}
          icon={<Plus className="h-4 w-4" />}
          className="shrink-0"
        >
          <span className="hidden sm:inline">Novo Estabelecimento</span>
          <span className="sm:hidden">Novo</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="space-y-4">
          {/* Search and Main Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Input
              placeholder="Buscar estabelecimentos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="sm:col-span-2"
            />

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todos">Todos os status</option>
              <option value="active">Ativos</option>
              <option value="inactive">Inativos</option>
            </select>

            <select
              value={filterCompany}
              onChange={(e) => setFilterCompany(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="">Todas as empresas</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.person?.name || `Empresa ${company.id}`}
                </option>
              ))}
            </select>
          </div>

          {/* Secondary Filters */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              {typeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            <div className="flex justify-end">
              <Button
                variant="secondary"
                outline
                icon={<Filter className="h-4 w-4" />}
                size="sm"
              >
                <span className="hidden sm:inline">Limpar Filtros</span>
                <span className="sm:hidden">Limpar</span>
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Building2 className="h-6 w-6 text-blue-600 dark:text-blue-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="text-2xl font-bold text-foreground">{totalCount}</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <UserCheck className="h-6 w-6 text-green-600 dark:text-green-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Ativos</p>
              <p className="text-2xl font-bold text-foreground">
                {establishments.filter((e) => e.is_active === true).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-gray-100 dark:bg-gray-900 rounded-lg">
              <UserX className="h-6 w-6 text-gray-600 dark:text-gray-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Inativos</p>
              <p className="text-2xl font-bold text-foreground">
                {establishments.filter((e) => e.is_active === false).length}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Building className="h-6 w-6 text-purple-600 dark:text-purple-300" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-muted-foreground">Principais</p>
              <p className="text-2xl font-bold text-foreground">
                {establishments.filter((e) => e.is_principal === true).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Establishments Table */}
      <Card title="Lista de Estabelecimentos">
        {/* Desktop Table */}
        <div className="hidden lg:block">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Estabelecimento
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Empresa
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Tipo/Categoria
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Criado em
                  </th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {establishments.map((establishment) => (
                  <tr
                    key={establishment.id}
                    className="border-b border-border hover:bg-muted/50"
                  >
                    <td className="py-3 px-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-foreground">
                            {establishment.person?.name || establishment.code}
                          </p>
                          {establishment.is_principal && (
                            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                              Principal
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground font-mono">
                          {establishment.code}
                        </p>
                        {establishment.person?.tax_id && (
                          <p className="text-xs text-muted-foreground">
                            CNPJ: {establishment.person.tax_id}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm text-foreground">
                          {establishment.company_name || `Empresa ${establishment.company_id}`}
                        </p>
                        {establishment.company_tax_id && (
                          <p className="text-xs text-muted-foreground font-mono">
                            {establishment.company_tax_id}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm font-medium text-foreground capitalize">
                          {establishment.type}
                        </p>
                        <p className="text-xs text-muted-foreground capitalize">
                          {establishment.category}
                        </p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={getStatusBadge(
                          establishment.is_active ? "active" : "inactive"
                        )}
                      >
                        {getStatusLabel(establishment.is_active ? "active" : "inactive")}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-foreground">
                      {establishment.created_at
                        ? new Date(establishment.created_at).toLocaleDateString("pt-BR")
                        : "-"}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex justify-center">
                        <ActionDropdown>
                          <ActionDropdown.Item
                            icon={<Eye className="h-4 w-4" />}
                            onClick={() => handleView(establishment.id)}
                          >
                            Ver Detalhes
                          </ActionDropdown.Item>
                          
                          <ActionDropdown.Item
                            icon={<Edit className="h-4 w-4" />}
                            onClick={() => handleEdit(establishment.id)}
                          >
                            Editar
                          </ActionDropdown.Item>
                          
                          <ActionDropdown.Item
                            icon={establishment.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                            onClick={() => handleToggleStatus(establishment.id, !establishment.is_active)}
                            variant={establishment.is_active ? "warning" : "success"}
                          >
                            {establishment.is_active ? "Inativar" : "Ativar"}
                          </ActionDropdown.Item>

                          <ActionDropdown.Item
                            icon={<ArrowUpDown className="h-4 w-4" />}
                            onClick={() => handleDelete(establishment.id)}
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

        {/* Mobile Cards */}
        <div className="lg:hidden space-y-4">
          {establishments.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">
                Nenhum estabelecimento encontrado
              </p>
            </div>
          ) : (
            establishments.map((establishment, index) => (
              <div
                key={establishment?.id || index}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-gray-900 dark:text-white text-base">
                        {establishment.person?.name || establishment.code}
                      </h3>
                      {establishment.is_principal && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                          Principal
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 font-mono">
                      {establishment.code}
                    </p>
                  </div>
                  <span
                    className={getStatusBadge(
                      establishment.is_active ? "active" : "inactive"
                    )}
                  >
                    {getStatusLabel(establishment.is_active ? "active" : "inactive")}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                  <div className="flex items-center">
                    <Building2 className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300 capitalize">
                      {establishment.type}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300 capitalize">
                      {establishment.category}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">
                      {establishment.created_at
                        ? new Date(establishment.created_at).toLocaleDateString("pt-BR")
                        : "-"}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Users className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-gray-600 dark:text-gray-300">
                      {establishment.company_name?.substring(0, 20) || `Empresa ${establishment.company_id}`}
                    </span>
                  </div>
                </div>

                <div className="flex justify-end pt-3 border-t border-gray-200 dark:border-gray-700">
                  <ActionDropdown>
                    <ActionDropdown.Item
                      icon={<Eye className="h-4 w-4" />}
                      onClick={() => handleView(establishment.id)}
                    >
                      Ver Detalhes
                    </ActionDropdown.Item>
                    
                    <ActionDropdown.Item
                      icon={<Edit className="h-4 w-4" />}
                      onClick={() => handleEdit(establishment.id)}
                    >
                      Editar
                    </ActionDropdown.Item>
                    
                    <ActionDropdown.Item
                      icon={establishment.is_active ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                      onClick={() => handleToggleStatus(establishment.id, !establishment.is_active)}
                      variant={establishment.is_active ? "warning" : "success"}
                    >
                      {establishment.is_active ? "Inativar" : "Ativar"}
                    </ActionDropdown.Item>

                    <ActionDropdown.Item
                      icon={<ArrowUpDown className="h-4 w-4" />}
                      onClick={() => handleDelete(establishment.id)}
                      variant="danger"
                    >
                      Excluir
                    </ActionDropdown.Item>
                  </ActionDropdown>
                </div>
              </div>
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
              estabelecimentos
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

export default EstablishmentsPage;