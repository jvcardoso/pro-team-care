import React, { useState, useEffect, useCallback } from 'react';
import { companiesService } from '../../services/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { Save, X } from 'lucide-react';
import { PhoneInputGroup, EmailInputGroup, AddressInputGroup } from '../contacts';
import { InputCNPJ } from '../inputs';

const CompanyForm = ({ companyId, onSave, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    people: {
      person_type: 'PJ',
      name: '',
      trade_name: '',
      tax_id: '',
      secondary_tax_id: '',
      incorporation_date: '',
      tax_regime: 'simples_nacional',
      legal_nature: 'ltda',
      municipal_registration: '',
      website: '',
      description: '',
      status: 'active'
    },
    company: {
      settings: {},
      metadata: {},
      display_order: 0
    },
    phones: [{
      country_code: '55',
      number: '',
      type: 'commercial',
      is_principal: true,
      is_whatsapp: false
    }],
    emails: [{
      email_address: '',
      type: 'work',
      is_principal: true
    }],
    addresses: [{
      street: '',
      number: '',
      details: '',
      neighborhood: '',
      city: '',
      state: '',
      zip_code: '',
      country: 'Brasil',
      type: 'commercial',
      is_principal: true
    }]
  });

  const isEditing = Boolean(companyId);

  const loadCompany = useCallback(async () => {
    try {
      setLoading(true);
      const company = await companiesService.getCompany(companyId);
      setFormData({
        people: company.people,
        company: {
          settings: company.settings || {},
          metadata: company.metadata || {},
          display_order: company.display_order || 0
        },
        phones: company.phones.length > 0 ? company.phones : [{
          country_code: '55',
          number: '',
          type: 'commercial',
          is_principal: true,
          is_whatsapp: false
        }],
        emails: company.emails.length > 0 ? company.emails : [{
          email_address: '',
          type: 'work',
          is_principal: true
        }],
        addresses: company.addresses.length > 0 ? company.addresses : [{
          street: '',
          number: '',
          details: '',
          neighborhood: '',
          city: '',
          state: '',
          zip_code: '',
          country: 'BR',
          type: 'commercial',
          is_principal: true
        }]
      });
    } catch (err) {
      setError('Erro ao carregar empresa');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (companyId) {
      loadCompany();
    }
  }, [companyId, loadCompany]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      // Validação básica
      if (!formData.people.name.trim()) {
        setError('Nome da empresa é obrigatório');
        return;
      }
      if (!formData.people.tax_id.trim()) {
        setError('CNPJ é obrigatório');
        return;
      }

      // Limpar campos vazios
      const cleanedData = {
        ...formData,
        phones: formData.phones.filter(phone => phone.number.trim()),
        emails: formData.emails.filter(email => email.email_address.trim()),
        addresses: formData.addresses.filter(address => 
          address.street.trim() && address.city.trim()
        )
      };

      if (isEditing) {
        await companiesService.updateCompany(companyId, cleanedData);
      } else {
        await companiesService.createCompany(cleanedData);
      }

      onSave?.();
    } catch (err) {
      console.error('Erro completo:', err);
      console.error('Response data:', err.response?.data);
      
      let errorMessage = 'Erro desconhecido ao salvar empresa';
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.response?.status === 400) {
        errorMessage = 'Dados inválidos. Verifique os campos obrigatórios.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Empresa não encontrada.';
      } else if (err.response?.status >= 500) {
        errorMessage = 'Erro interno do servidor. Tente novamente.';
      } else if (err.message) {
        errorMessage = `Erro de conexão: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updatePeople = (field, value) => {
    setFormData(prev => ({
      ...prev,
      people: { ...prev.people, [field]: value }
    }));
  };

  const handlePhonesChange = (phones) => {
    setFormData(prev => ({ ...prev, phones }));
  };

  const handlePhoneAdd = (newPhone) => {
    setFormData(prev => ({
      ...prev,
      phones: [...prev.phones, newPhone]
    }));
  };

  const handlePhoneRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      phones: prev.phones.filter((_, i) => i !== index)
    }));
  };

  const handleEmailsChange = (emails) => {
    setFormData(prev => ({ ...prev, emails }));
  };

  const handleEmailAdd = (newEmail) => {
    setFormData(prev => ({
      ...prev,
      emails: [...prev.emails, newEmail]
    }));
  };

  const handleEmailRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      emails: prev.emails.filter((_, i) => i !== index)
    }));
  };

  const handleAddressesChange = (addresses) => {
    setFormData(prev => ({ ...prev, addresses }));
  };

  const handleAddressAdd = (newAddress) => {
    setFormData(prev => ({
      ...prev,
      addresses: [...prev.addresses, newAddress]
    }));
  };

  const handleAddressRemove = (index) => {
    setFormData(prev => ({
      ...prev,
      addresses: prev.addresses.filter((_, i) => i !== index)
    }));
  };

  const handleCompanyFound = (companyData) => {
    // Confirmar com usuário antes de sobrescrever dados existentes
    const hasExistingData = formData.people.name || formData.people.trade_name;
    
    if (hasExistingData) {
      const confirmOverwrite = window.confirm(
        'Dados da empresa encontrados na Receita Federal. Deseja preencher os campos automaticamente? Isso irá sobrescrever os dados já preenchidos.'
      );
      
      if (!confirmOverwrite) {
        return;
      }
    }

    // Preencher formulário com dados da consulta
    setFormData(prev => ({
      ...prev,
      people: {
        ...prev.people,
        ...companyData.people
      },
      // Mesclar telefones (manter existentes + adicionar novos)
      phones: companyData.phones.length > 0 
        ? [...companyData.phones, ...prev.phones.filter(p => p.number)]
        : prev.phones,
      // Mesclar emails (manter existentes + adicionar novos)
      emails: companyData.emails.length > 0
        ? [...companyData.emails, ...prev.emails.filter(e => e.email_address)]
        : prev.emails,
      // Mesclar endereços (manter existentes + adicionar novos)
      addresses: companyData.addresses.length > 0
        ? [...companyData.addresses, ...prev.addresses.filter(a => a.street || a.city)]
        : prev.addresses
    }));

    // Limpar erro se houver
    setError(null);

    // Mostrar feedback positivo
    console.log('Dados da empresa preenchidos automaticamente:', companyData);
  };

  if (loading && isEditing) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">Carregando empresa...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {isEditing ? 'Editar Empresa' : 'Nova Empresa'}
          </h1>
          <p className="text-muted-foreground">
            {isEditing ? 'Atualize as informações da empresa' : 'Cadastre uma nova empresa no sistema'}
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" outline onClick={onCancel} icon={<X className="h-4 w-4" />}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={loading} icon={<Save className="h-4 w-4" />}>
            {loading ? 'Salvando...' : 'Salvar'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Dados da Empresa */}
        <Card title="Dados da Empresa">
          <div className="space-y-6">
            {/* CNPJ - Primeiro campo com consulta */}
            <InputCNPJ
              label="CNPJ *"
              value={formData.people.tax_id}
              onChange={(data) => updatePeople('tax_id', data.target.value)}
              onCompanyFound={handleCompanyFound}
              placeholder="00.000.000/0000-00"
              required
              disabled={loading}
              showValidation={true}
              showConsultButton={true}
              autoConsult={false}
            />

            {/* Campos principais */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Razão Social *"
                value={formData.people.name}
                onChange={(e) => updatePeople('name', e.target.value)}
                placeholder="Nome completo da empresa"
                required
              />
              <Input
                label="Nome Fantasia"
                value={formData.people.trade_name || ''}
                onChange={(e) => updatePeople('trade_name', e.target.value)}
                placeholder="Nome comercial"
              />
            </div>

            {/* Campos secundários */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Input
                label="Inscrição Estadual"
                value={formData.people.secondary_tax_id || ''}
                onChange={(e) => updatePeople('secondary_tax_id', e.target.value)}
                placeholder="123.456.789"
              />
              <Input
                label="Inscrição Municipal"
                value={formData.people.municipal_registration || ''}
                onChange={(e) => updatePeople('municipal_registration', e.target.value)}
                placeholder="12345678"
              />
              <Input
                label="Website"
                value={formData.people.website || ''}
                onChange={(e) => updatePeople('website', e.target.value)}
                placeholder="https://www.empresa.com.br"
                type="url"
              />
            </div>

            {/* Natureza e regime */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Input
                label="Natureza Jurídica"
                value={formData.people.legal_nature || ''}
                onChange={(e) => updatePeople('legal_nature', e.target.value)}
                placeholder="Sociedade Limitada"
              />
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Regime Tributário
                </label>
                <select
                  value={formData.people.tax_regime || 'simples_nacional'}
                  onChange={(e) => updatePeople('tax_regime', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  <option value="simples_nacional">Simples Nacional</option>
                  <option value="lucro_presumido">Lucro Presumido</option>
                  <option value="lucro_real">Lucro Real</option>
                  <option value="mei">MEI</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Status
                </label>
                <select
                  value={formData.people.status}
                  onChange={(e) => updatePeople('status', e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  <option value="active">Ativo</option>
                  <option value="inactive">Inativo</option>
                  <option value="suspended">Suspenso</option>
                </select>
              </div>
            </div>

            {/* Data de abertura */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Data de Abertura"
                value={formData.people.incorporation_date || ''}
                onChange={(e) => updatePeople('incorporation_date', e.target.value)}
                type="date"
              />
            </div>

            {/* Descrição */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Descrição da Empresa
              </label>
              <textarea
                value={formData.people.description || ''}
                onChange={(e) => updatePeople('description', e.target.value)}
                placeholder="Breve descrição das atividades da empresa..."
                rows={3}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none resize-none"
              />
            </div>
          </div>
        </Card>

        {/* Informações da Receita Federal */}
        {formData.people.metadata && Object.keys(formData.people.metadata).length > 0 && (
          <Card title="Informações da Receita Federal" className="bg-blue-50 dark:bg-blue-900/20">
            <div className="space-y-4">
              {/* CNAE Principal */}
              {formData.people.metadata.cnae_fiscal && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      CNAE Principal
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.people.metadata.cnae_fiscal} - {formData.people.metadata.cnae_fiscal_descricao}
                    </p>
                  </div>
                  {formData.people.metadata.porte && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Porte da Empresa
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.people.metadata.porte}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* CNAEs Secundários */}
              {formData.people.metadata.cnaes_secundarios && formData.people.metadata.cnaes_secundarios.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    CNAEs Secundários
                  </label>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {formData.people.metadata.cnaes_secundarios.map((cnae, index) => (
                      <p key={index} className="text-xs text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {cnae.code} - {cnae.text}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Informações da situação */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {formData.people.metadata.situacao && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Situação na RF
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.people.metadata.situacao}
                    </p>
                  </div>
                )}
                {formData.people.metadata.data_situacao && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Data da Situação
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.people.metadata.data_situacao}
                    </p>
                  </div>
                )}
                {formData.people.metadata.tipo && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Tipo de Estabelecimento
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.people.metadata.tipo}
                    </p>
                  </div>
                )}
              </div>

              {/* Capital social e última atualização */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {formData.people.metadata.capital_social && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Capital Social
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      R$ {formData.people.metadata.capital_social}
                    </p>
                  </div>
                )}
                {formData.people.metadata.ultima_atualizacao_rf && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Última Atualização RF
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {new Date(formData.people.metadata.ultima_atualizacao_rf).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                )}
              </div>

              {/* Situação especial e motivo */}
              {(formData.people.metadata.situacao_especial || formData.people.metadata.motivo_situacao) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {formData.people.metadata.situacao_especial && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Situação Especial
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.people.metadata.situacao_especial}
                      </p>
                    </div>
                  )}
                  {formData.people.metadata.motivo_situacao && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Motivo da Situação
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.people.metadata.motivo_situacao}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Telefones */}
        <Card>
          <PhoneInputGroup
            phones={formData.phones}
            onChange={handlePhonesChange}
            onAdd={handlePhoneAdd}
            onRemove={handlePhoneRemove}
            required={true}
            disabled={loading}
            showValidation={true}
            minPhones={1}
            maxPhones={5}
            title="Telefones"
          />
        </Card>

        {/* E-mails */}
        <Card>
          <EmailInputGroup
            emails={formData.emails}
            onChange={handleEmailsChange}
            onAdd={handleEmailAdd}
            onRemove={handleEmailRemove}
            required={true}
            disabled={loading}
            showValidation={true}
            minEmails={1}
            maxEmails={5}
            title="E-mails"
          />
        </Card>

        {/* Endereços */}
        <Card>
          <AddressInputGroup
            addresses={formData.addresses}
            onChange={handleAddressesChange}
            onAdd={handleAddressAdd}
            onRemove={handleAddressRemove}
            required={true}
            disabled={loading}
            showValidation={true}
            minAddresses={1}
            maxAddresses={3}
            title="Endereços"
          />
        </Card>
      </form>
    </div>
  );
};

export default CompanyForm;