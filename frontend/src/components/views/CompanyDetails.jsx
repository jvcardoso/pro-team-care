import React, { useState, useEffect } from 'react';
import { companiesService } from '../../services/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import CompanyBasicInfo from '../entities/CompanyBasicInfo';
import ReceitaFederalInfo from '../metadata/ReceitaFederalInfo';
import { ArrowLeft, Edit, Trash2, Phone, Mail, MapPin, Building, Calendar, User, Globe, MessageCircle, Send, Navigation, ExternalLink } from 'lucide-react';

const CompanyDetails = ({ companyId, onEdit, onBack, onDelete }) => {
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('informacoes');

  useEffect(() => {
    if (companyId) {
      loadCompany();
    }
  }, [companyId]);

  const loadCompany = async () => {
    try {
      setLoading(true);
      const data = await companiesService.getCompany(companyId);
      setCompany(data);
    } catch (err) {
      setError('Erro ao carregar empresa');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Tem certeza que deseja excluir esta empresa?')) {
      try {
        await companiesService.deleteCompany(companyId);
        onDelete?.();
      } catch (err) {
        alert('Erro ao excluir empresa');
        console.error(err);
      }
    }
  };


  const formatPhone = (phone) => {
    if (!phone.number) return '-';
    const number = phone.number.replace(/\D/g, '');
    if (number.length === 11) {
      return `+${phone.country_code} (${number.slice(0,2)}) ${number.slice(2,7)}-${number.slice(7)}`;
    }
    if (number.length === 10) {
      return `+${phone.country_code} (${number.slice(0,2)}) ${number.slice(2,6)}-${number.slice(6)}`;
    }
    return `+${phone.country_code} ${number}`;
  };

  const formatZipCode = (zipCode) => {
    if (!zipCode) return '-';
    return zipCode.replace(/^(\d{5})(\d{3})$/, '$1-$2');
  };

  const getStatusBadge = (status) => {
    const baseClasses = 'px-3 py-1 text-sm font-medium rounded-full';
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

  const getPhoneTypeLabel = (type) => {
    switch (type) {
      case 'commercial': return 'Comercial';
      case 'mobile': return 'Celular';
      case 'fax': return 'Fax';
      default: return type;
    }
  };

  const getEmailTypeLabel = (type) => {
    switch (type) {
      case 'work': return 'Trabalho';
      case 'personal': return 'Pessoal';
      case 'other': return 'Outro';
      default: return type;
    }
  };

  const getAddressTypeLabel = (type) => {
    switch (type) {
      case 'commercial': return 'Comercial';
      case 'residential': return 'Residencial';
      case 'billing': return 'Cobrança';
      case 'delivery': return 'Entrega';
      default: return type;
    }
  };

  const openWhatsApp = (phone) => {
    const number = phone.number.replace(/\D/g, '');
    const url = `https://wa.me/${phone.country_code}${number}`;
    window.open(url, '_blank');
  };

  const openEmail = (email) => {
    const url = `mailto:${email.email_address}`;
    window.open(url, '_blank');
  };

  const openGoogleMaps = (address) => {
    const query = encodeURIComponent(`${address.street}, ${address.number}, ${address.city}, ${address.state}, ${address.zip_code}, ${address.country}`);
    const url = `https://www.google.com/maps/search/?api=1&query=${query}`;
    window.open(url, '_blank');
  };

  const openWaze = (address) => {
    const query = encodeURIComponent(`${address.street}, ${address.number}, ${address.city}, ${address.state}`);
    const url = `https://waze.com/ul?q=${query}`;
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">Carregando empresa...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadCompany}>Tentar Novamente</Button>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Empresa não encontrada</p>
        <Button onClick={onBack} className="mt-4" icon={<ArrowLeft className="h-4 w-4" />}>
          Voltar
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="secondary" outline onClick={onBack} icon={<ArrowLeft className="h-4 w-4" />}>
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{company.people.name}</h1>
            <div className="flex items-center gap-4 mt-1">
              {company.people.trade_name && company.people.trade_name !== company.people.name && (
                <p className="text-muted-foreground">{company.people.trade_name}</p>
              )}
              <span className={getStatusBadge(company.people.status)}>
                {getStatusLabel(company.people.status)}
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="primary" onClick={() => onEdit?.(companyId)} icon={<Edit className="h-4 w-4" />}>
            Editar
          </Button>
          <Button variant="danger" outline onClick={handleDelete} icon={<Trash2 className="h-4 w-4" />}>
            Excluir
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex space-x-8">
          <button
            onClick={() => setActiveTab('informacoes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'informacoes'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Informações
          </button>
          <button
            onClick={() => setActiveTab('estabelecimentos')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'estabelecimentos'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Estabelecimentos
          </button>
          <button
            onClick={() => setActiveTab('clientes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'clientes'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Clientes
          </button>
          <button
            onClick={() => setActiveTab('profissionais')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'profissionais'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Profissionais
          </button>
          <button
            onClick={() => setActiveTab('pacientes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pacientes'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Pacientes
          </button>
          <button
            onClick={() => setActiveTab('usuarios')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'usuarios'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            Usuários
          </button>
          <button
            onClick={() => setActiveTab('lgpd')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'lgpd'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            }`}
          >
            LGPD
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'informacoes' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Informações Básicas */}
        <div className="lg:col-span-2 space-y-6">
          <CompanyBasicInfo company={company} />

          {/* Telefones */}
          {company.phones && company.phones.length > 0 && (
            <Card title="Telefones">
              <div className="space-y-4">
                {company.phones.map((phone, index) => (
                  <div key={phone.id || index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <Phone className="h-4 w-4 text-blue-600 dark:text-blue-300" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{formatPhone(phone)}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>{getPhoneTypeLabel(phone.type)}</span>
                          {phone.is_principal && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                              Principal
                            </span>
                          )}
                          {phone.is_whatsapp && (
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                              WhatsApp
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {phone.is_whatsapp && (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => openWhatsApp(phone)}
                          icon={<MessageCircle className="h-4 w-4" />}
                          title="Abrir no WhatsApp"
                        >
                          WhatsApp
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* E-mails */}
          {company.emails && company.emails.length > 0 && (
            <Card title="E-mails">
              <div className="space-y-4">
                {company.emails.map((email, index) => (
                  <div key={email.id || index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                        <Mail className="h-4 w-4 text-green-600 dark:text-green-300" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{email.email_address}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>{getEmailTypeLabel(email.type)}</span>
                          {email.is_principal && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                              Principal
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => openEmail(email)}
                        icon={<Send className="h-4 w-4" />}
                        title="Enviar email"
                      >
                        Enviar Email
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Endereços */}
          {company.addresses && company.addresses.length > 0 && (
            <Card title="Endereços">
              <div className="space-y-4">
                {company.addresses.map((address, index) => (
                  <div key={address.id || index} className="p-4 bg-muted/30 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                        <MapPin className="h-4 w-4 text-orange-600 dark:text-orange-300" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-foreground">
                            {getAddressTypeLabel(address.type)}
                          </span>
                          {address.is_principal && (
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                              Principal
                            </span>
                          )}
                        </div>
                        <p className="text-foreground">
                          {address.street}
                          {address.number && `, ${address.number}`}
                          {address.details && ` - ${address.details}`}
                        </p>
                        <p className="text-foreground">
                          {address.neighborhood}, {address.city} - {address.state}
                        </p>
                        <p className="text-muted-foreground">
                          CEP: {formatZipCode(address.zip_code)}
                          {address.country && address.country !== 'Brasil' && ` - ${address.country}`}
                        </p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => openGoogleMaps(address)}
                          icon={<Navigation className="h-4 w-4" />}
                          title="Abrir no Google Maps"
                        >
                          Maps
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => openWaze(address)}
                          icon={<ExternalLink className="h-4 w-4" />}
                          title="Abrir no Waze"
                        >
                          Waze
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <ReceitaFederalInfo metadata={company.metadata} />
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Resumo */}
          <Card title="Resumo">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Estabelecimentos</span>
                <span className="font-medium text-muted-foreground">Em breve</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Clientes</span>
                <span className="font-medium text-muted-foreground">Em breve</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Profissionais</span>
                <span className="font-medium text-muted-foreground">Em breve</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Pacientes</span>
                <span className="font-medium text-muted-foreground">Em breve</span>
              </div>
            </div>
          </Card>

          {/* Metadados */}
          <Card title="Informações do Sistema">
            <div className="space-y-4 text-sm">
              <div>
                <label className="block text-muted-foreground mb-1">ID da Empresa</label>
                <p className="text-foreground font-mono">#{company.id}</p>
              </div>
              <div>
                <label className="block text-muted-foreground mb-1">Criado em</label>
                <p className="text-foreground">{new Date(company.created_at).toLocaleString('pt-BR')}</p>
              </div>
              <div>
                <label className="block text-muted-foreground mb-1">Atualizado em</label>
                <p className="text-foreground">{new Date(company.updated_at).toLocaleString('pt-BR')}</p>
              </div>
              {company.display_order !== null && (
                <div>
                  <label className="block text-muted-foreground mb-1">Ordem de Exibição</label>
                  <p className="text-foreground">{company.display_order}</p>
                </div>
              )}
            </div>
          </Card>

          {/* Configurações */}
          {company.settings && Object.keys(company.settings).length > 0 && (
            <Card title="Configurações">
              <div className="space-y-2 text-sm">
                {Object.entries(company.settings).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}</span>
                    <span className="text-foreground">
                      {typeof value === 'boolean' ? (value ? 'Sim' : 'Não') : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      </div>
      )}

      {activeTab === 'estabelecimentos' && (
        <div className="text-center py-12">
          <Building className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Estabelecimentos</h3>
          <p className="text-muted-foreground">Em breve: Gerencie os estabelecimentos desta empresa</p>
        </div>
      )}

      {activeTab === 'clientes' && (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Clientes</h3>
          <p className="text-muted-foreground">Em breve: Gerencie os clientes desta empresa</p>
        </div>
      )}

      {activeTab === 'profissionais' && (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Profissionais</h3>
          <p className="text-muted-foreground">Em breve: Gerencie os profissionais desta empresa</p>
        </div>
      )}

      {activeTab === 'pacientes' && (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Pacientes</h3>
          <p className="text-muted-foreground">Em breve: Gerencie os pacientes desta empresa</p>
        </div>
      )}

      {activeTab === 'usuarios' && (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">Usuários</h3>
          <p className="text-muted-foreground">Em breve: Gerencie os usuários desta empresa</p>
        </div>
      )}

      {activeTab === 'lgpd' && (
        <div className="text-center py-12">
          <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">LGPD</h3>
          <p className="text-muted-foreground">Em breve: Gerencie as configurações de privacidade e LGPD</p>
        </div>
      )}
    </div>
  );
};

export default CompanyDetails;