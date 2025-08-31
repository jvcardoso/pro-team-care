import React, { useState, useEffect, useCallback } from 'react';
import { companiesService } from '../../services/api';
import { consultarCNPJ, formatarCNPJ } from '../../services/cnpjService';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { Save, X, Search, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { PhoneInputGroup, EmailInputGroup, AddressInputGroup } from '../contacts';
import { InputCNPJ } from '../inputs';
import toast from 'react-hot-toast';

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

  const [showNumberConfirmation, setShowNumberConfirmation] = useState(false);
  const [pendingAddresses, setPendingAddresses] = useState(null);

  const isEditing = Boolean(companyId);

  const loadCompany = useCallback(async () => {
    try {
      setLoading(true);
      const company = await companiesService.getCompany(companyId);
      setFormData({
        people: company.people,
        company: company.company || {
          settings: {},
          metadata: {},
          display_order: 0
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
      if (!formData.people.name?.trim()) {
        setError('Nome da empresa é obrigatório');
        return;
      }
      if (!formData.people.tax_id?.trim()) {
        setError('CNPJ é obrigatório');
        return;
      }

      // Verificar se há pelo menos um endereço válido
      const hasValidAddress = formData.addresses.some(address =>
        address.street?.trim() && address.city?.trim()
      );
      if (!hasValidAddress) {
        setError('Pelo menos um endereço com rua e cidade é obrigatório');
        return;
      }

      // Verificar se há endereços sem número informado
      const addressesWithoutNumber = formData.addresses.filter(address =>
        address.street?.trim() && address.city?.trim() && (!address.number?.trim() || address.number?.trim() === '')
      );

      if (addressesWithoutNumber.length > 0) {
        // Mostrar confirmação para endereços sem número
        setPendingAddresses(formData);
        setShowNumberConfirmation(true);
        return;
      }

      // Verificar se há pelo menos um telefone válido (sincronizado com a limpeza)
      console.log('=== [VALIDATION] Verificando telefones ===');
      console.log('Telefones no formData:', formData.phones);

      const validPhones = formData.phones.filter(phone =>
        phone.number?.trim() && phone.number.trim().length >= 8
      );
      console.log('Telefones válidos (8+ dígitos):', validPhones);

      const hasValidPhone = validPhones.length > 0;
      console.log('Tem telefone válido?', hasValidPhone);

      if (!hasValidPhone) {
        setError('Erro na validação dos telefones, verifique os números informados');
        return;
      }

      // Verificar se há pelo menos um email válido
      const hasValidEmail = formData.emails.some(email => email.email_address?.trim());
      if (!hasValidEmail) {
        setError('Pelo menos um email é obrigatório');
        return;
      }

      // Validações adicionais para campos específicos
      if (!formData.people.person_type) {
        setError('Tipo de pessoa é obrigatório');
        return;
      }

      // Limpar valores undefined/null que podem causar problemas no backend
      const sanitizeData = (obj) => {
        if (obj === null || obj === undefined) return obj;
        if (typeof obj === 'object') {
          const cleaned = {};
          for (const [key, value] of Object.entries(obj)) {
            // Processar metadata mantendo campos importantes
            if (key === 'metadata' && typeof value === 'object') {
              console.log('=== [SANITIZE] Processando metadata ===');
              console.log('Metadata original keys:', Object.keys(value));
              console.log('Metadata original:', value);

              const cleanMetadata = {};
              // Manter campos essenciais
              if (value.cnae_fiscal) cleanMetadata.cnae_fiscal = value.cnae_fiscal;
              if (value.cnae_fiscal_descricao) cleanMetadata.cnae_fiscal_descricao = value.cnae_fiscal_descricao;
              if (value.porte) cleanMetadata.porte = value.porte;
              if (value.situacao) cleanMetadata.situacao = value.situacao;
              if (value.capital_social) cleanMetadata.capital_social = value.capital_social;
              if (value.natureza_juridica) cleanMetadata.natureza_juridica = value.natureza_juridica;
              if (value.ultima_atualizacao_rf) cleanMetadata.ultima_atualizacao_rf = value.ultima_atualizacao_rf;

              // Incluir campos adicionais importantes
              if (value.cnaes_secundarios) cleanMetadata.cnaes_secundarios = value.cnaes_secundarios;
              if (value.data_situacao) cleanMetadata.data_situacao = value.data_situacao;
              if (value.tipo) cleanMetadata.tipo = value.tipo;
              if (value.municipio) cleanMetadata.municipio = value.municipio;
              if (value.uf) cleanMetadata.uf = value.uf;

              console.log('Metadata limpo keys:', Object.keys(cleanMetadata));
              console.log('Metadata limpo:', cleanMetadata);

              // Não incluir campos muito complexos como receita_ws_data completo
              if (Object.keys(cleanMetadata).length > 0) {
                cleaned[key] = cleanMetadata;
                console.log('✅ Metadata incluído nos dados finais');
              } else {
                console.log('❌ Metadata vazio - não incluído');
              }
            } else if (value !== null && value !== undefined && value !== '') {
              cleaned[key] = sanitizeData(value);
            }
          }
          return cleaned;
        }
        return obj;
      };

      // Limpar campos vazios e preparar dados
      let cleanedData = {
        people: sanitizeData(formData.people),
        company: sanitizeData(formData.company) || {
          settings: {},
          metadata: {},
          display_order: 0
        },
        phones: formData.phones
          .filter(phone => {
            const isValid = phone.number?.trim() && phone.number.trim().length >= 8;
            console.log(`[CLEANUP] Telefone ${phone.number}: válido=${isValid}, length=${phone.number?.trim()?.length || 0}`);
            return isValid;
          })
          .map(phone => sanitizeData({
            country_code: phone.country_code || '55',
            number: phone.number.trim().replace(/\D/g, ''), // Remover não dígitos
            type: phone.type || 'commercial',
            is_principal: phone.is_principal || false,
            is_whatsapp: phone.is_whatsapp || false
          }))
          .slice(0, 3), // Limitar a 3 telefones
        emails: formData.emails
          .filter(email => email.email_address?.trim())
          .map(email => sanitizeData({
            email_address: email.email_address.trim(),
            type: email.type || 'work',
            is_principal: email.is_principal || false
          })),
        addresses: formData.addresses
          .filter(address => address.street?.trim() && address.city?.trim())
          .map(address => {
            // Debug: verificar se coordenadas estão presentes
            if (address.latitude && address.longitude) {
              console.log(`📍 Endereço com coordenadas encontrado: ${address.latitude}, ${address.longitude}`);
            } else {
              console.log(`⚠️ Endereço sem coordenadas: ${address.street}, ${address.city}`);
            }

            // Função especial para sanitizar endereços preservando campo number
            const sanitizeAddress = (addr) => {
              if (addr === null || addr === undefined) return addr;
              if (typeof addr === 'object') {
                const cleaned = {};
                for (const [key, value] of Object.entries(addr)) {
                  // Sempre incluir o campo number, mesmo se vazio
                  if (key === 'number') {
                    cleaned[key] = value || '';
                  } else if (value !== null && value !== undefined && value !== '') {
                    cleaned[key] = sanitizeAddress(value);
                  }
                }
                return cleaned;
              }
              return addr;
            };

            // Garantir que campos obrigatórios tenham valores
            const cleanAddress = {
              ...address,
              country: address.country || 'BR',
              type: address.type || 'commercial',
              is_principal: address.is_principal || false,
              // Campo number: manter como está (pode ser vazio)
              number: address.number || ''
            };

            return sanitizeAddress(cleanAddress);
          })
          .slice(0, 1) // Apenas o primeiro endereço
      };



      // Garantir que o campo company esteja sempre presente
      if (!cleanedData.company || Object.keys(cleanedData.company).length === 0) {
        cleanedData.company = {
          settings: {},
          metadata: {},
          display_order: 0
        };
      }

      // Verificar se os arrays têm pelo menos um item válido
      if (cleanedData.phones.length === 0) {
        setError('Pelo menos um telefone deve ser válido');
        return;
      }

      if (cleanedData.emails.length === 0) {
        setError('Pelo menos um email deve ser válido');
        return;
      }

      if (cleanedData.addresses.length === 0) {
        setError('Pelo menos um endereço deve ser válido');
        return;
      }

      // Validações finais dos campos obrigatórios
      if (!cleanedData.people.person_type) {
        cleanedData.people.person_type = 'PJ';
      }

      if (!cleanedData.people.status) {
        cleanedData.people.status = 'active';
      }



      // Log detalhado dos dados sendo enviados para debug
      console.log('=== [DEBUG] DADOS SENDO ENVIADOS PARA SALVAR EMPRESA ===');
      console.log('Timestamp:', new Date().toISOString());
      console.log('URL:', isEditing ? `/api/v1/companies/${companyId}` : '/api/v1/companies/');
      console.log('Method:', isEditing ? 'PUT' : 'POST');
      console.log('Estrutura completa:', JSON.stringify(cleanedData, null, 2));
      console.log('People keys:', Object.keys(cleanedData.people));
      console.log('Company keys:', Object.keys(cleanedData.company));
      console.log('Phones count:', cleanedData.phones.length);
      console.log('Emails count:', cleanedData.emails.length);
      console.log('Addresses count:', cleanedData.addresses.length);
      
      // Debug coordenadas e números
      console.log('=== [DEBUG] ENDEREÇOS DETALHADOS ===');
      cleanedData.addresses.forEach((addr, i) => {
        console.log(`Endereço ${i + 1}:`, {
          street: addr.street,
          number: addr.number,
          numberType: typeof addr.number,
          numberLength: addr.number?.length || 0,
          city: addr.city,
          state: addr.state,
          zip_code: addr.zip_code,
          latitude: addr.latitude,
          longitude: addr.longitude,
          geocoding_source: addr.geocoding_source,
          geocoding_accuracy: addr.geocoding_accuracy
        });
      });

      // Verificar campos de metadata (AGORA NO COMPANY!)
      console.log('=== [METADATA] Campos do metadata (companies.metadata) ===');
      if (cleanedData.company.metadata && Object.keys(cleanedData.company.metadata).length > 0) {
        console.log('✅ Metadata encontrado no COMPANY!');
        console.log('Metadata keys:', Object.keys(cleanedData.company.metadata));
        console.log('CNAEs Secundários:', cleanedData.company.metadata.cnaes_secundarios);
        console.log('Situação na RF:', cleanedData.company.metadata.situacao);
        console.log('Data da Situação:', cleanedData.company.metadata.data_situacao);
        console.log('Tipo de Estabelecimento:', cleanedData.company.metadata.tipo);
        console.log('Capital Social:', cleanedData.company.metadata.capital_social);
        console.log('Última Atualização RF:', cleanedData.company.metadata.ultima_atualizacao_rf);
      } else {
        console.log('❌ Nenhum metadata encontrado no company!');
      }

      // Verificar campos obrigatórios
      console.log('=== [VALIDATION] Campos obrigatórios ===');
      console.log('People.name:', !!cleanedData.people.name);
      console.log('People.tax_id:', !!cleanedData.people.tax_id);
      console.log('People.person_type:', !!cleanedData.people.person_type);
      console.log('Company exists:', !!cleanedData.company);
      console.log('Phones valid:', cleanedData.phones.length > 0);
      console.log('Emails valid:', cleanedData.emails.length > 0);
      console.log('Addresses valid:', cleanedData.addresses.length > 0);

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

      if (err.response?.status === 422) {
        // Erro de validação do Pydantic (FastAPI)
        if (Array.isArray(err.response.data?.detail)) {
          const validationErrors = err.response.data.detail.map(error => {
            const field = error.loc?.join('.') || 'campo';
            return `${field}: ${error.msg}`;
          });
          errorMessage = `Erros de validação:\n${validationErrors.join('\n')}`;
        } else if (err.response.data?.detail) {
          errorMessage = err.response.data.detail;
        } else {
          errorMessage = 'Dados inválidos. Verifique os campos obrigatórios.';
        }
      } else if (err.response?.status === 400) {
        errorMessage = 'Dados inválidos. Verifique os campos obrigatórios.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Empresa não encontrada.';
      } else if (err.response?.status >= 500) {
        // Erro interno do servidor - tentar extrair mais detalhes
        const serverError = err.response?.data?.detail || err.response?.data?.message || 'Erro interno do servidor';
        errorMessage = `Erro interno do servidor: ${serverError}. Verifique os logs do backend.`;
        console.error('Erro 500 - Detalhes do servidor:', err.response?.data);
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

  const handleNumberConfirmation = async (confirmed) => {
    setShowNumberConfirmation(false);

    if (confirmed && pendingAddresses) {
      // Usuário confirmou salvar sem número - definir S/N para endereços sem número
      const updatedAddresses = pendingAddresses.addresses.map(address => ({
        ...address,
        number: address.number?.trim() || 'S/N'
      }));

      const dataWithDefaultNumbers = {
        ...pendingAddresses,
        addresses: updatedAddresses
      };

      // Continuar com o salvamento
      await proceedWithSave(dataWithDefaultNumbers);
    }

    setPendingAddresses(null);
  };

  const proceedWithSave = async (dataToSave) => {
    try {
      setLoading(true);
      setError(null);

      // Limpar valores undefined/null que podem causar problemas no backend
      const sanitizeData = (obj) => {
        if (obj === null || obj === undefined) return obj;
        if (typeof obj === 'object') {
          const cleaned = {};
          for (const [key, value] of Object.entries(obj)) {
            // Processar metadata mantendo campos importantes
            if (key === 'metadata' && typeof value === 'object') {
              console.log('=== [SANITIZE] Processando metadata ===');
              console.log('Metadata original keys:', Object.keys(value));
              console.log('Metadata original:', value);

              const cleanMetadata = {};
              // Manter campos essenciais
              if (value.cnae_fiscal) cleanMetadata.cnae_fiscal = value.cnae_fiscal;
              if (value.cnae_fiscal_descricao) cleanMetadata.cnae_fiscal_descricao = value.cnae_fiscal_descricao;
              if (value.porte) cleanMetadata.porte = value.porte;
              if (value.situacao) cleanMetadata.situacao = value.situacao;
              if (value.capital_social) cleanMetadata.capital_social = value.capital_social;
              if (value.natureza_juridica) cleanMetadata.natureza_juridica = value.natureza_juridica;
              if (value.ultima_atualizacao_rf) cleanMetadata.ultima_atualizacao_rf = value.ultima_atualizacao_rf;

              // Incluir campos adicionais importantes
              if (value.cnaes_secundarios) cleanMetadata.cnaes_secundarios = value.cnaes_secundarios;
              if (value.data_situacao) cleanMetadata.data_situacao = value.data_situacao;
              if (value.tipo) cleanMetadata.tipo = value.tipo;
              if (value.municipio) cleanMetadata.municipio = value.municipio;
              if (value.uf) cleanMetadata.uf = value.uf;

              console.log('Metadata limpo keys:', Object.keys(cleanMetadata));
              console.log('Metadata limpo:', cleanMetadata);

              // Não incluir campos muito complexos como receita_ws_data completo
              if (Object.keys(cleanMetadata).length > 0) {
                cleaned[key] = cleanMetadata;
                console.log('✅ Metadata incluído nos dados finais');
              } else {
                console.log('❌ Metadata vazio - não incluído');
              }
            } else if (value !== null && value !== undefined && value !== '') {
              cleaned[key] = sanitizeData(value);
            }
          }
          return cleaned;
        }
        return obj;
      };

      // Limpar campos vazios e preparar dados
      let cleanedData = {
        people: sanitizeData(dataToSave.people),
        company: sanitizeData(dataToSave.company) || {
          settings: {},
          metadata: {},
          display_order: 0
        },
        phones: dataToSave.phones
          .filter(phone => {
            const isValid = phone.number?.trim() && phone.number.trim().length >= 8;
            console.log(`[CLEANUP] Telefone ${phone.number}: válido=${isValid}, length=${phone.number?.trim()?.length || 0}`);
            return isValid;
          })
          .map(phone => sanitizeData({
            country_code: phone.country_code || '55',
            number: phone.number.trim().replace(/\D/g, ''), // Remover não dígitos
            type: phone.type || 'commercial',
            is_principal: phone.is_principal || false,
            is_whatsapp: phone.is_whatsapp || false
          }))
          .slice(0, 3), // Limitar a 3 telefones
        emails: dataToSave.emails
          .filter(email => email.email_address?.trim())
          .map(email => sanitizeData({
            email_address: email.email_address.trim(),
            type: email.type || 'work',
            is_principal: email.is_principal || false
          })),
        addresses: dataToSave.addresses
          .filter(address => address.street?.trim() && address.city?.trim())
          .map(address => {
            // Debug: verificar se coordenadas estão presentes
            if (address.latitude && address.longitude) {
              console.log(`📍 Endereço com coordenadas encontrado: ${address.latitude}, ${address.longitude}`);
            } else {
              console.log(`⚠️ Endereço sem coordenadas: ${address.street}, ${address.city}`);
            }

            // Garantir que campos obrigatórios tenham valores
            const cleanAddress = {
              ...address,
              country: address.country || 'BR',
              type: address.type || 'commercial',
              is_principal: address.is_principal || false,
              // Campo number: se vazio, usar "S/N" (Sem Número)
              number: address.number?.trim() || 'S/N'
            };

            return sanitizeData(cleanAddress);
          })
          .slice(0, 1) // Apenas o primeiro endereço
      };

      // Garantir que o campo company esteja sempre presente
      if (!cleanedData.company || Object.keys(cleanedData.company).length === 0) {
        cleanedData.company = {
          settings: {},
          metadata: {},
          display_order: 0
        };
      }

      // Verificar se os arrays têm pelo menos um item válido
      if (cleanedData.phones.length === 0) {
        setError('Pelo menos um telefone deve ser válido');
        return;
      }

      if (cleanedData.emails.length === 0) {
        setError('Pelo menos um email deve ser válido');
        return;
      }

      if (cleanedData.addresses.length === 0) {
        setError('Pelo menos um endereço deve ser válido');
        return;
      }

      // Validações finais dos campos obrigatórios
      if (!cleanedData.people.person_type) {
        cleanedData.people.person_type = 'PJ';
      }

      if (!cleanedData.people.status) {
        cleanedData.people.status = 'active';
      }

      // Log detalhado dos dados sendo enviados para debug
      console.log('=== [DEBUG] DADOS SENDO ENVIADOS PARA SALVAR EMPRESA ===');
      console.log('Timestamp:', new Date().toISOString());
      console.log('URL:', isEditing ? `/api/v1/companies/${companyId}` : '/api/v1/companies/');
      console.log('Method:', isEditing ? 'PUT' : 'POST');
      console.log('Estrutura completa:', JSON.stringify(cleanedData, null, 2));
      console.log('People keys:', Object.keys(cleanedData.people));
      console.log('Company keys:', Object.keys(cleanedData.company));
      console.log('Phones count:', cleanedData.phones.length);
      console.log('Emails count:', cleanedData.emails.length);
      console.log('Addresses count:', cleanedData.addresses.length);

      // Verificar campos de metadata (AGORA NO COMPANY!)
      console.log('=== [METADATA] Campos do metadata (companies.metadata) ===');
      if (cleanedData.company.metadata && Object.keys(cleanedData.company.metadata).length > 0) {
        console.log('✅ Metadata encontrado no COMPANY!');
        console.log('Metadata keys:', Object.keys(cleanedData.company.metadata));
        console.log('CNAEs Secundários:', cleanedData.company.metadata.cnaes_secundarios);
        console.log('Situação na RF:', cleanedData.company.metadata.situacao);
        console.log('Data da Situação:', cleanedData.company.metadata.data_situacao);
        console.log('Tipo de Estabelecimento:', cleanedData.company.metadata.tipo);
        console.log('Capital Social:', cleanedData.company.metadata.capital_social);
        console.log('Última Atualização RF:', cleanedData.company.metadata.ultima_atualizacao_rf);
      } else {
        console.log('❌ Nenhum metadata encontrado no company!');
      }

      // Verificar campos obrigatórios
      console.log('=== [VALIDATION] Campos obrigatórios ===');
      console.log('People.name:', !!cleanedData.people.name);
      console.log('People.tax_id:', !!cleanedData.people.tax_id);
      console.log('People.person_type:', !!cleanedData.people.person_type);
      console.log('Company exists:', !!cleanedData.company);
      console.log('Phones valid:', cleanedData.phones.length > 0);
      console.log('Emails valid:', cleanedData.emails.length > 0);
      console.log('Addresses valid:', cleanedData.addresses.length > 0);

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

      if (err.response?.status === 422) {
        // Erro de validação do Pydantic (FastAPI)
        if (Array.isArray(err.response.data?.detail)) {
          const validationErrors = err.response.data.detail.map(error => {
            const field = error.loc?.join('.') || 'campo';
            return `${field}: ${error.msg}`;
          });
          errorMessage = `Erros de validação:\n${validationErrors.join('\n')}`;
        } else if (err.response.data?.detail) {
          errorMessage = err.response.data.detail;
        } else {
          errorMessage = 'Dados inválidos. Verifique os campos obrigatórios.';
        }
      } else if (err.response?.status === 400) {
        errorMessage = 'Dados inválidos. Verifique os campos obrigatórios.';
      } else if (err.response?.status === 404) {
        errorMessage = 'Empresa não encontrada.';
      } else if (err.response?.status >= 500) {
        // Erro interno do servidor - tentar extrair mais detalhes
        const serverError = err.response?.data?.detail || err.response?.data?.message || 'Erro interno do servidor';
        errorMessage = `Erro interno do servidor: ${serverError}. Verifique os logs do backend.`;
        console.error('Erro 500 - Detalhes do servidor:', err.response?.data);
      } else if (err.message) {
        errorMessage = `Erro de conexão: ${err.message}`;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCNPJConsulta = async () => {
    const cnpj = formData.people.tax_id?.trim();

    if (!cnpj || cnpj.length < 14) {
      setError('Digite um CNPJ válido com 14 dígitos');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const dadosEmpresa = await consultarCNPJ(cnpj);

      // Verificar se os dados retornados são válidos
      const hasValidData = dadosEmpresa?.people?.name ||
                          dadosEmpresa?.phones?.length > 0 ||
                          dadosEmpresa?.emails?.length > 0 ||
                          dadosEmpresa?.addresses?.length > 0;

      // Se não há dados válidos, não faz nada
      if (!hasValidData) {
        notify.info('Nenhum dado encontrado para este CNPJ');
        return;
      }

      // Verificar se há dados existentes que serão sobrescritos
      const hasExistingData = formData.people.name || formData.people.trade_name ||
                             formData.phones.some(p => p.number) ||
                             formData.emails.some(e => e.email_address) ||
                             formData.addresses.some(a => a.street);

      const fillData = () => {
        // LIMPAR formulário antes de preencher
        const cleanFormData = {
          people: {
            person_type: 'PJ',
            name: '',
            trade_name: '',
            tax_id: formData.people.tax_id, // Manter apenas o CNPJ
            incorporation_date: '',
            legal_nature: '',
            status: 'active',
            tax_regime: 'simples_nacional',
            description: ''
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
            country: 'BR',
            type: 'commercial',
            is_principal: true
          }]
        };

        // Preencher com dados da ReceitaWS
        console.log('=== [CNPJ] Atribuindo dados ao formData ===');
        console.log('Dados da empresa recebidos:', dadosEmpresa);
        console.log('Metadata da empresa:', dadosEmpresa.people?.metadata);

        setFormData({
          people: {
            ...cleanFormData.people,
            name: dadosEmpresa.people?.name || '',
            trade_name: dadosEmpresa.people?.trade_name || '',
            incorporation_date: dadosEmpresa.people?.incorporation_date || '',
            legal_nature: dadosEmpresa.people?.legal_nature || '',
            status: dadosEmpresa.people?.status || 'active',
            tax_regime: dadosEmpresa.people?.tax_regime || 'simples_nacional',
            description: dadosEmpresa.people?.description || ''
            // ❌ REMOVER metadata daqui - vai para company
          },
          company: {
            ...cleanFormData.company,
            // ✅ METADATA VAI PARA COMPANY!
            metadata: dadosEmpresa.people?.metadata || {}
          },
          phones: dadosEmpresa.phones?.length > 0 ? dadosEmpresa.phones : cleanFormData.phones,
          emails: dadosEmpresa.emails?.length > 0 ? dadosEmpresa.emails : cleanFormData.emails,
          addresses: dadosEmpresa.addresses?.length > 0 ? dadosEmpresa.addresses : cleanFormData.addresses
        });

        console.log('FormData após atribuição:', formData);

        // Feedback visual de sucesso
        notify.success('Dados da empresa preenchidos automaticamente!');
      };

      if (hasExistingData) {
        // Toast personalizado com confirmação
        toast((t) => (
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <CheckCircle className="h-6 w-6 text-blue-500" />
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                  Dados Encontrados na Receita Federal
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                  Deseja preencher os campos automaticamente? Isso irá sobrescrever os dados já preenchidos.
                </p>
              </div>
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => {
                  fillData();
                  toast.dismiss(t.id);
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-3 rounded-md transition-colors"
              >
                <CheckCircle className="h-4 w-4 inline mr-1" />
                Preencher
              </button>
              <button
                onClick={() => toast.dismiss(t.id)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 text-sm font-medium py-2 px-3 rounded-md transition-colors"
              >
                <XCircle className="h-4 w-4 inline mr-1" />
                Cancelar
              </button>
            </div>
          </div>
        ), {
          duration: 10000, // 10 segundos para decisão
          position: 'top-center',
          style: {
            background: '#ffffff',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '0.5rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            maxWidth: '400px',
          },
        });
      } else {
        // Se não há dados existentes, preenche diretamente
        fillData();
      }

    } catch (err) {
      console.error('Erro ao consultar CNPJ:', err);
      setError(err.message || 'Erro ao consultar CNPJ');
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyFound = (companyData) => {
    // Verificar se há dados existentes que serão sobrescritos
    const hasExistingData = formData.people.name || formData.people.trade_name ||
                           formData.phones.some(p => p.number) ||
                           formData.emails.some(e => e.email_address) ||
                           formData.addresses.some(a => a.street);

    const fillData = () => {
      // LIMPAR formulário antes de preencher
      const cleanFormData = {
        people: {
          person_type: 'PJ',
          name: '',
          trade_name: '',
          tax_id: formData.people.tax_id, // Manter apenas o CNPJ
          incorporation_date: '',
          legal_nature: '',
          status: 'active',
          tax_regime: 'simples_nacional',
          description: ''
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
          country: 'BR',
          type: 'commercial',
          is_principal: true
        }]
      };

      // Preencher com dados da consulta
      console.log('=== [COMPANY FOUND] Atribuindo dados ao formData ===');
      console.log('Dados da empresa recebidos:', companyData);
      console.log('Metadata da empresa:', companyData.people?.metadata);

      setFormData({
        people: {
          ...cleanFormData.people,
          ...companyData.people
          // ❌ REMOVER metadata daqui - vai para company
        },
        company: {
          ...cleanFormData.company,
          // ✅ METADATA VAI PARA COMPANY!
          metadata: companyData.people?.metadata || cleanFormData.company.metadata || {}
        },
        phones: companyData.phones?.length > 0 ? companyData.phones : cleanFormData.phones,
        emails: companyData.emails?.length > 0 ? companyData.emails : cleanFormData.emails,
        addresses: companyData.addresses?.length > 0 ? companyData.addresses : cleanFormData.addresses
      });

      console.log('FormData após atribuição (handleCompanyFound):', formData);

      // Limpar erro se houver
      setError(null);

      // Feedback visual de sucesso
      notify.success('Dados da empresa preenchidos automaticamente!');
    };

    if (hasExistingData) {
      // Toast personalizado com confirmação
      toast((t) => (
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <CheckCircle className="h-6 w-6 text-blue-500" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                Dados Encontrados na Receita Federal
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                Deseja preencher os campos automaticamente? Isso irá sobrescrever os dados já preenchidos.
              </p>
            </div>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={() => {
                fillData();
                toast.dismiss(t.id);
              }}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-3 rounded-md transition-colors"
            >
              <CheckCircle className="h-4 w-4 inline mr-1" />
              Preencher
            </button>
            <button
              onClick={() => toast.dismiss(t.id)}
              className="flex-1 bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 text-sm font-medium py-2 px-3 rounded-md transition-colors"
            >
              <XCircle className="h-4 w-4 inline mr-1" />
              Cancelar
            </button>
          </div>
        </div>
      ), {
        duration: 10000, // 10 segundos para decisão
        position: 'top-center',
        style: {
          background: '#ffffff',
          color: '#374151',
          border: '1px solid #d1d5db',
          borderRadius: '0.5rem',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          maxWidth: '400px',
        },
      });
    } else {
      // Se não há dados existentes, preenche diretamente
      fillData();
    }
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
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-foreground">
            {isEditing ? 'Editar Empresa' : 'Nova Empresa'}
          </h1>
          <p className="text-muted-foreground">
            {isEditing ? 'Atualize as informações da empresa' : 'Cadastre uma nova empresa no sistema'}
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <Button variant="secondary" outline onClick={onCancel} icon={<X className="h-4 w-4" />} className="flex-1 sm:flex-none">
            <span className="hidden sm:inline">Cancelar</span>
            <span className="sm:hidden">Cancelar</span>
          </Button>
          <Button onClick={handleSubmit} disabled={loading} icon={<Save className="h-4 w-4" />} className="flex-1 sm:flex-none">
            <span className="hidden sm:inline">{loading ? 'Salvando...' : 'Salvar'}</span>
            <span className="sm:hidden">{loading ? 'Salvando...' : 'Salvar'}</span>
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
               label="CNPJ"
               value={formData.people.tax_id}
               onChange={(data) => updatePeople('tax_id', data.target.value)}
               onCompanyFound={handleCompanyFound}
               placeholder="00.000.000/0000-00"
               required
               disabled={loading || isEditing}
               showValidation={true}
               showConsultButton={!isEditing}
               autoConsult={false} // Desabilitado para evitar loop de login
             />

            {/* Campos principais */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Input
                label="Razão Social"
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
        {formData.company.metadata && Object.keys(formData.company.metadata).length > 0 && (
          <Card title="Informações da Receita Federal" className="bg-blue-50 dark:bg-blue-900/20">
            <div className="space-y-4">
              {/* CNAE Principal */}
              {formData.company.metadata.cnae_fiscal && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      CNAE Principal
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.company.metadata.cnae_fiscal} - {formData.company.metadata.cnae_fiscal_descricao}
                    </p>
                  </div>
                  {formData.company.metadata.porte && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Porte da Empresa
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.company.metadata.porte}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* CNAEs Secundários */}
              {formData.company.metadata.cnaes_secundarios && formData.company.metadata.cnaes_secundarios.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    CNAEs Secundários
                  </label>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {formData.company.metadata.cnaes_secundarios.map((cnae, index) => (
                      <p key={index} className="text-xs text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {cnae.code} - {cnae.text}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Informações da situação */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {formData.company.metadata.situacao && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Situação na RF
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.company.metadata.situacao}
                    </p>
                  </div>
                )}
                {formData.company.metadata.data_situacao && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Data da Situação
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.company.metadata.data_situacao}
                    </p>
                  </div>
                )}
                {formData.company.metadata.tipo && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Tipo de Estabelecimento
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {formData.company.metadata.tipo}
                    </p>
                  </div>
                )}
              </div>

              {/* Capital social e última atualização */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {formData.company.metadata.capital_social && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Capital Social
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      R$ {formData.company.metadata.capital_social}
                    </p>
                  </div>
                )}
                {formData.company.metadata.ultima_atualizacao_rf && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Última Atualização RF
                    </label>
                    <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                      {new Date(formData.company.metadata.ultima_atualizacao_rf).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                )}
              </div>

              {/* Situação especial e motivo */}
              {(formData.company.metadata.situacao_especial || formData.company.metadata.motivo_situacao) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {formData.company.metadata.situacao_especial && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Situação Especial
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.company.metadata.situacao_especial}
                      </p>
                    </div>
                  )}
                  {formData.company.metadata.motivo_situacao && (
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Motivo da Situação
                      </label>
                      <p className="text-sm text-muted-foreground bg-white dark:bg-gray-800 p-2 rounded border">
                        {formData.company.metadata.motivo_situacao}
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

      {/* Modal de Confirmação para Número do Endereço */}
      {showNumberConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Número do Endereço Não Informado
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                  Você não informou o número do endereço. Deseja salvar com "S/N" (Sem Número) ou voltar para corrigir?
                </p>

                <div className="flex gap-3">
                  <Button
                    onClick={() => handleNumberConfirmation(false)}
                    variant="secondary"
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Corrigir
                  </Button>
                  <Button
                    onClick={() => handleNumberConfirmation(true)}
                    className="flex-1"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Salvar com S/N
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyForm;