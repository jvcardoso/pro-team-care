import React, { useState, useEffect } from 'react';
import { companiesService } from '../../services/api';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { Save, X, Plus, Trash2 } from 'lucide-react';

const CompanyForm = ({ companyId, onSave, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    people: {
      person_type: 'PJ',
      name: '',
      trade_name: '',
      tax_id: '',
      incorporation_date: '',
      tax_regime: 'simples_nacional',
      legal_nature: 'ltda',
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
      complement: '',
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

  useEffect(() => {
    if (companyId) {
      loadCompany();
    }
  }, [companyId]);

  const loadCompany = async () => {
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
        phones: company.phones.length > 0 ? company.phones : formData.phones,
        emails: company.emails.length > 0 ? company.emails : formData.emails,
        addresses: company.addresses.length > 0 ? company.addresses : formData.addresses
      });
    } catch (err) {
      setError('Erro ao carregar empresa');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
      setError(err.response?.data?.detail || 'Erro ao salvar empresa');
      console.error(err);
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

  const addPhone = () => {
    setFormData(prev => ({
      ...prev,
      phones: [...prev.phones, {
        country_code: '55',
        number: '',
        type: 'commercial',
        is_principal: false,
        is_whatsapp: false
      }]
    }));
  };

  const updatePhone = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      phones: prev.phones.map((phone, i) => 
        i === index ? { ...phone, [field]: value } : phone
      )
    }));
  };

  const removePhone = (index) => {
    setFormData(prev => ({
      ...prev,
      phones: prev.phones.filter((_, i) => i !== index)
    }));
  };

  const addEmail = () => {
    setFormData(prev => ({
      ...prev,
      emails: [...prev.emails, {
        email_address: '',
        type: 'work',
        is_principal: false
      }]
    }));
  };

  const updateEmail = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      emails: prev.emails.map((email, i) => 
        i === index ? { ...email, [field]: value } : email
      )
    }));
  };

  const removeEmail = (index) => {
    setFormData(prev => ({
      ...prev,
      emails: prev.emails.filter((_, i) => i !== index)
    }));
  };

  const addAddress = () => {
    setFormData(prev => ({
      ...prev,
      addresses: [...prev.addresses, {
        street: '',
        number: '',
        details: '',
        neighborhood: '',
        city: '',
        state: '',
        zip_code: '',
        country: 'Brasil',
        type: 'commercial',
        is_principal: false
      }]
    }));
  };

  const updateAddress = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      addresses: prev.addresses.map((address, i) => 
        i === index ? { ...address, [field]: value } : address
      )
    }));
  };

  const removeAddress = (index) => {
    setFormData(prev => ({
      ...prev,
      addresses: prev.addresses.filter((_, i) => i !== index)
    }));
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
            <Input
              label="CNPJ *"
              value={formData.people.tax_id}
              onChange={(e) => updatePeople('tax_id', e.target.value.replace(/\D/g, ''))}
              placeholder="00.000.000/0001-00"
              maxLength={14}
              required
            />
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
        </Card>

        {/* Telefones */}
        <Card title="Telefones">
          <div className="space-y-4">
            {formData.phones.map((phone, index) => (
              <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <Input
                  label="Número"
                  value={phone.number}
                  onChange={(e) => updatePhone(index, 'number', e.target.value)}
                  placeholder="11987654321"
                />
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Tipo</label>
                  <select
                    value={phone.type}
                    onChange={(e) => updatePhone(index, 'type', e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                  >
                    <option value="commercial">Comercial</option>
                    <option value="mobile">Celular</option>
                    <option value="fax">Fax</option>
                  </select>
                </div>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={phone.is_whatsapp}
                      onChange={(e) => updatePhone(index, 'is_whatsapp', e.target.checked)}
                      className="mr-2"
                    />
                    WhatsApp
                  </label>
                </div>
                <Button
                  type="button"
                  variant="danger"
                  outline
                  size="sm"
                  onClick={() => removePhone(index)}
                  disabled={formData.phones.length === 1}
                  icon={<Trash2 className="h-4 w-4" />}
                >
                  Remover
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              outline
              onClick={addPhone}
              icon={<Plus className="h-4 w-4" />}
            >
              Adicionar Telefone
            </Button>
          </div>
        </Card>

        {/* E-mails */}
        <Card title="E-mails">
          <div className="space-y-4">
            {formData.emails.map((email, index) => (
              <div key={index} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <Input
                  label="E-mail"
                  type="email"
                  value={email.email_address}
                  onChange={(e) => updateEmail(index, 'email_address', e.target.value)}
                  placeholder="contato@empresa.com"
                />
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Tipo</label>
                  <select
                    value={email.type}
                    onChange={(e) => updateEmail(index, 'type', e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                  >
                    <option value="work">Trabalho</option>
                    <option value="personal">Pessoal</option>
                    <option value="other">Outro</option>
                  </select>
                </div>
                <Button
                  type="button"
                  variant="danger"
                  outline
                  size="sm"
                  onClick={() => removeEmail(index)}
                  disabled={formData.emails.length === 1}
                  icon={<Trash2 className="h-4 w-4" />}
                >
                  Remover
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              outline
              onClick={addEmail}
              icon={<Plus className="h-4 w-4" />}
            >
              Adicionar E-mail
            </Button>
          </div>
        </Card>

        {/* Endereços */}
        <Card title="Endereços">
          <div className="space-y-6">
            {formData.addresses.map((address, index) => (
              <div key={index} className="space-y-4 p-4 border border-border rounded-lg">
                <div className="flex justify-between items-center">
                  <h4 className="font-medium text-foreground">Endereço {index + 1}</h4>
                  <Button
                    type="button"
                    variant="danger"
                    outline
                    size="sm"
                    onClick={() => removeAddress(index)}
                    disabled={formData.addresses.length === 1}
                    icon={<Trash2 className="h-4 w-4" />}
                  >
                    Remover
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="Logradouro"
                    value={address.street}
                    onChange={(e) => updateAddress(index, 'street', e.target.value)}
                    placeholder="Rua, Avenida, etc."
                  />
                  <Input
                    label="Número"
                    value={address.number}
                    onChange={(e) => updateAddress(index, 'number', e.target.value)}
                    placeholder="123"
                  />
                  <Input
                    label="Complemento"
                    value={address.details || ''}
                    onChange={(e) => updateAddress(index, 'details', e.target.value)}
                    placeholder="Sala, Andar, etc."
                  />
                  <Input
                    label="Bairro"
                    value={address.neighborhood}
                    onChange={(e) => updateAddress(index, 'neighborhood', e.target.value)}
                    placeholder="Centro, Bela Vista, etc."
                  />
                  <Input
                    label="Cidade"
                    value={address.city}
                    onChange={(e) => updateAddress(index, 'city', e.target.value)}
                    placeholder="São Paulo"
                  />
                  <Input
                    label="Estado"
                    value={address.state}
                    onChange={(e) => updateAddress(index, 'state', e.target.value)}
                    placeholder="SP"
                    maxLength={2}
                  />
                  <Input
                    label="CEP"
                    value={address.zip_code}
                    onChange={(e) => updateAddress(index, 'zip_code', e.target.value.replace(/\D/g, ''))}
                    placeholder="01310100"
                    maxLength={8}
                  />
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Tipo</label>
                    <select
                      value={address.type}
                      onChange={(e) => updateAddress(index, 'type', e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                    >
                      <option value="commercial">Comercial</option>
                      <option value="residential">Residencial</option>
                      <option value="billing">Cobrança</option>
                      <option value="delivery">Entrega</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              outline
              onClick={addAddress}
              icon={<Plus className="h-4 w-4" />}
            >
              Adicionar Endereço
            </Button>
          </div>
        </Card>
      </form>
    </div>
  );
};

export default CompanyForm;