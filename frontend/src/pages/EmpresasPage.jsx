import React, { useState, useEffect } from 'react';
import { companiesService } from '../services/api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import CompanyForm from '../components/forms/CompanyForm';
import CompanyDetails from '../components/views/CompanyDetails';
import { Building, Search, Plus, Filter, Phone, Mail, MapPin, Edit, Eye, Trash2 } from 'lucide-react';

const EmpresasPage = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('todos');
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [currentView, setCurrentView] = useState('list'); // 'list', 'create', 'edit', 'details'
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);

  useEffect(() => {
    if (currentView === 'list') {
      loadCompanies();
      loadTotalCount();
    }
  }, [currentPage, searchTerm, filterStatus, currentView]);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const params = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== 'todos' && { status: filterStatus })
      };

      const data = await companiesService.getCompanies(params);
      setCompanies(data);
    } catch (err) {
      setError('Erro ao carregar empresas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadTotalCount = async () => {
    try {
      const params = {
        ...(searchTerm && { search: searchTerm }),
        ...(filterStatus !== 'todos' && { status: filterStatus })
      };
      const data = await companiesService.getCompaniesCount(params);
      setTotalCount(data.total);
    } catch (err) {
      console.error('Erro ao carregar contagem:', err);
    }
  };

  const handleDelete = async (companyId) => {
    if (window.confirm('Tem certeza que deseja excluir esta empresa?')) {
      try {
        await companiesService.deleteCompany(companyId);
        loadCompanies();
        loadTotalCount();
      } catch (err) {
        setError('Erro ao excluir empresa');
        console.error(err);
      }
    }
  };

  const handleCreate = () => {
    setSelectedCompanyId(null);
    setCurrentView('create');
  };

  const handleEdit = (companyId) => {
    setSelectedCompanyId(companyId);
    setCurrentView('edit');
  };

  const handleView = (companyId) => {
    setSelectedCompanyId(companyId);
    setCurrentView('details');
  };

  const handleSave = () => {
    setCurrentView('list');
    setSelectedCompanyId(null);
    loadCompanies();
    loadTotalCount();
  };

  const handleCancel = () => {
    setCurrentView('list');
    setSelectedCompanyId(null);
  };

  const handleBack = () => {
    setCurrentView('list');
    setSelectedCompanyId(null);
  };

  const handleDeleteFromDetails = () => {
    setCurrentView('list');
    setSelectedCompanyId(null);
    loadCompanies();
    loadTotalCount();
  };

  const getStatusBadge = (status) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    switch (status) {
      case 'active':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
      case 'inactive':
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
      case 'suspended':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active': return 'Ativo';
      case 'inactive': return 'Inativo';
      case 'suspended': return 'Suspenso';
      default: return status;
    }
  };

  const formatTaxId = (taxId) => {
    if (!taxId) return '-';
    return taxId.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
  };

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  // Render different views based on current state
  if (currentView === 'create' || currentView === 'edit') {
    return (
      <CompanyForm 
        companyId={selectedCompanyId}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    );
  }

  if (currentView === 'details') {
    return (
      <CompanyDetails 
        companyId={selectedCompanyId}
        onEdit={handleEdit}
        onBack={handleBack}
        onDelete={handleDeleteFromDetails}
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

  if (error && companies.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={loadCompanies}>Tentar Novamente</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Empresas</h1>
          <p className="text-muted-foreground">Gerencie as empresas cadastradas no sistema</p>
        </div>
        <Button onClick={handleCreate} icon={<Plus className="h-4 w-4" />}>
          Nova Empresa
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-1 gap-4">
            <Input
              placeholder="Buscar empresas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
              className="max-w-sm"
            />
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
            >
              <option value="todos">Todos os status</option>
              <option value="active">Ativo</option>
              <option value="inactive">Inativo</option>
              <option value="suspended">Suspenso</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button variant="secondary" outline icon={<Filter className="h-4 w-4" />}>
              Filtros
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
                {companies.filter(c => c.status === 'active').length}
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
                {companies.filter(c => c.status === 'inactive').length}
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
                {companies.filter(c => c.status === 'suspended').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Companies Table */}
      <Card title="Lista de Empresas">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Empresa</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">CNPJ</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Contatos</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Criado em</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Ações</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((company) => (
                <tr key={company.id} className="border-b border-border hover:bg-muted/50">
                  <td className="py-3 px-4">
                    <div>
                      <p className="font-medium text-foreground">{company.name}</p>
                      {company.trade_name && company.trade_name !== company.name && (
                        <p className="text-sm text-muted-foreground">{company.trade_name}</p>
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
                        {company.phones_count} telefone{company.phones_count !== 1 ? 's' : ''}
                      </div>
                      <div className="flex items-center text-sm text-muted-foreground">
                        <Mail className="h-3 w-3 mr-1" />
                        {company.emails_count} email{company.emails_count !== 1 ? 's' : ''}
                      </div>
                      <div className="flex items-center text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3 mr-1" />
                        {company.addresses_count} endereço{company.addresses_count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={getStatusBadge(company.status)}>
                      {getStatusLabel(company.status)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-foreground">
                    {new Date(company.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="secondary" 
                        outline 
                        icon={<Eye className="h-3 w-3" />}
                        onClick={() => handleView(company.id)}
                      >
                        Ver
                      </Button>
                      <Button 
                        size="sm" 
                        variant="primary" 
                        outline 
                        icon={<Edit className="h-3 w-3" />}
                        onClick={() => handleEdit(company.id)}
                      >
                        Editar
                      </Button>
                      <Button 
                        size="sm" 
                        variant="danger" 
                        outline 
                        icon={<Trash2 className="h-3 w-3" />}
                        onClick={() => handleDelete(company.id)}
                      >
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Mostrando {Math.min((currentPage - 1) * itemsPerPage + 1, totalCount)} a{' '}
              {Math.min(currentPage * itemsPerPage, totalCount)} de {totalCount} empresas
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