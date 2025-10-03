import React, { useState, useEffect } from "react";
import {
  contractsService,
  ServicesCatalog,
  ServicesListParams,
} from "../services/contractsService";
import { PageErrorBoundary } from "../components/error";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { notify } from "../utils/notifications.jsx";
import {
  Package,
  Search,
  Filter,
  Eye,
  Edit,
  Plus,
  Heart,
  Stethoscope,
  Activity,
  Pill,
  Brain,
  Baby,
  Users,
  Wrench,
  Star,
  Clock,
  DollarSign,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

const ServicesCatalogPage: React.FC = () => {
  return (
    <PageErrorBoundary pageName="Catálogo de Serviços">
      <ServicesCatalogPageContent />
    </PageErrorBoundary>
  );
};

const ServicesCatalogPageContent: React.FC = () => {
  const [services, setServices] = useState<ServicesCatalog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("todas");
  const [filterType, setFilterType] = useState<string>("todos");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // Categories and types for filtering
  const categories = [
    { value: "todas", label: "Todas as Categorias" },
    { value: "ENFERMAGEM", label: "Enfermagem", icon: Heart },
    { value: "FISIOTERAPIA", label: "Fisioterapia", icon: Activity },
    { value: "MEDICINA", label: "Medicina", icon: Stethoscope },
    { value: "EQUIPAMENTO", label: "Equipamentos", icon: Wrench },
    { value: "NUTRIÇÃO", label: "Nutrição", icon: Pill },
    { value: "PSICOLOGIA", label: "Psicologia", icon: Brain },
    { value: "TERAPIA_OCUPACIONAL", label: "Terapia Ocupacional", icon: Users },
    { value: "FONOAUDIOLOGIA", label: "Fonoaudiologia", icon: Baby },
    {
      value: "TERAPIA_RESPIRATORIA",
      label: "Terapia Respiratória",
      icon: Activity,
    },
    { value: "CUIDADOS", label: "Cuidados de Apoio", icon: Heart },
  ];

  const types = [
    { value: "todos", label: "Todos os Tipos" },
    { value: "PROCEDIMENTO", label: "Procedimento" },
    { value: "CONSULTA", label: "Consulta" },
    { value: "EXAME", label: "Exame" },
    { value: "TERAPIA", label: "Terapia" },
    { value: "LOCAÇÃO", label: "Locação" },
    { value: "ASSISTENCIA", label: "Assistência" },
  ];

  // Load services
  useEffect(() => {
    loadServices();
  }, [currentPage, filterCategory, filterType, searchTerm]);

  const loadServices = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ServicesListParams = {
        page: currentPage,
        size: itemsPerPage,
      };

      if (filterCategory !== "todas") {
        params.category = filterCategory;
      }

      if (filterType !== "todos") {
        params.service_type = filterType;
      }

      const response = await contractsService.listServices(params);

      // Filter by search term on client side
      let filteredServices = response.services;
      if (searchTerm) {
        filteredServices = response.services.filter(
          (service) =>
            service.service_name
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            service.service_code
              .toLowerCase()
              .includes(searchTerm.toLowerCase()) ||
            service.description
              ?.toLowerCase()
              .includes(searchTerm.toLowerCase())
        );
      }

      setServices(filteredServices);
      setTotalCount(response.total);
    } catch (error) {
      console.error("Erro ao carregar serviços:", error);
      setError("Erro ao carregar catálogo de serviços");
      notify.error("Erro ao carregar catálogo de serviços");
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category: string) => {
    const categoryData = categories.find((c) => c.value === category);
    const Icon = categoryData?.icon || Package;
    return <Icon className="w-5 h-5" />;
  };

  const getCategoryLabel = (category: string) => {
    return categories.find((c) => c.value === category)?.label || category;
  };

  const getTypeLabel = (type: string) => {
    return types.find((t) => t.value === type)?.label || type;
  };

  const getTypeBadgeColor = (type: string) => {
    const colors = {
      PROCEDIMENTO: "bg-blue-100 text-blue-800 border-blue-200",
      CONSULTA: "bg-green-100 text-green-800 border-green-200",
      EXAME: "bg-purple-100 text-purple-800 border-purple-200",
      TERAPIA: "bg-orange-100 text-orange-800 border-orange-200",
      LOCAÇÃO: "bg-gray-100 text-gray-800 border-gray-200",
      ASSISTENCIA: "bg-yellow-100 text-yellow-800 border-yellow-200",
    };
    return (
      colors[type as keyof typeof colors] ||
      "bg-gray-100 text-gray-800 border-gray-200"
    );
  };

  const formatCurrency = (value: number | undefined) => {
    if (!value) return "Sob consulta";
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value);
  };

  // Statistics
  const totalServices = services.length;
  const activeServices = services.filter((s) => s.is_active).length;
  const averageValue =
    services.reduce((sum, s) => sum + (s.default_unit_value || 0), 0) /
      totalServices || 0;
  const servicesRequiringPrescription = services.filter(
    (s) => s.requires_prescription
  ).length;

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Package className="w-6 h-6 mr-2" />
            Catálogo de Serviços Home Care
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Gestão completa do catálogo de serviços especializados
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Button className="flex items-center">
            <Plus className="w-4 h-4 mr-2" />
            Novo Serviço
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <Package className="w-8 h-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">
                  Total Serviços
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalServices}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Ativos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {activeServices}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <DollarSign className="w-8 h-8 text-orange-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Valor Médio</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(averageValue)}
                </p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">
                  Requer Prescrição
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {servicesRequiringPrescription}
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Buscar por nome, código ou descrição..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {types.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Carregando serviços...</span>
          </div>
        ) : services.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            Nenhum serviço encontrado
          </div>
        ) : (
          services.map((service) => (
            <Card
              key={service.id}
              className="hover:shadow-lg transition-shadow"
            >
              <div className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center">
                    <div className="text-blue-600 mr-2">
                      {getCategoryIcon(service.service_category)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm">
                        {service.service_name}
                      </h3>
                      <p className="text-xs text-gray-500">
                        {service.service_code}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {service.is_active ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <Clock className="w-4 h-4 text-gray-400" />
                    )}
                  </div>
                </div>

                {/* Category and Type */}
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    {getCategoryLabel(service.service_category)}
                  </span>
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getTypeBadgeColor(
                      service.service_type
                    )}`}
                  >
                    {getTypeLabel(service.service_type)}
                  </span>
                </div>

                {/* Description */}
                {service.description && (
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                    {service.description}
                  </p>
                )}

                {/* Details */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Valor:</span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(service.default_unit_value)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Domiciliar:</span>
                    <span
                      className={
                        service.home_visit_required
                          ? "text-green-600"
                          : "text-gray-400"
                      }
                    >
                      {service.home_visit_required ? "Sim" : "Não"}
                    </span>
                  </div>

                  {service.requires_prescription && (
                    <div className="flex items-center text-xs text-orange-600">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      Requer prescrição
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="mt-4 flex justify-end space-x-2">
                  <Button variant="outline" size="sm">
                    <Eye className="w-3 h-3" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Edit className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Card>
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex-1 flex justify-between sm:hidden">
              <Button
                variant="outline"
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Próximo
              </Button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando{" "}
                  <span className="font-medium">
                    {(currentPage - 1) * itemsPerPage + 1}
                  </span>{" "}
                  até{" "}
                  <span className="font-medium">
                    {Math.min(currentPage * itemsPerPage, totalCount)}
                  </span>{" "}
                  de <span className="font-medium">{totalCount}</span> serviços
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <Button
                    variant="outline"
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="rounded-r-none"
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="rounded-l-none"
                  >
                    Próximo
                  </Button>
                </nav>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ServicesCatalogPage;
