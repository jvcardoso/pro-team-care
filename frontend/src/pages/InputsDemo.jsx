import React, { useState } from 'react';
import { InputPhone, InputCEP, InputEmail } from '../components/inputs';

const InputsDemo = () => {
  const [formData, setFormData] = useState({
    phone: '11999887766', // Telefone de teste pré-carregado
    cep: '01310100', // CEP de teste pré-carregado
    email: 'teste@exemplo.com' // Email de teste pré-carregado
  });
  
  const [addressData, setAddressData] = useState(null);
  const [companyForm, setCompanyForm] = useState({
    name: '',
    trade_name: '',
    tax_id: '',
    address: {
      street: '',
      number: '',
      neighborhood: '',
      city: '',
      state: '',
      zip_code: '',
      ibge_city_code: null,
      gia_code: null,
      siafi_code: null,
      area_code: null
    }
  });

  // Dados mockados para demonstração (evita problemas de autenticação)
  const mockCompanyData = {
    people: {
      name: "Empresa Exemplo Ltda",
      trade_name: "Empresa Exemplo",
      tax_id: "12345678000123",
      incorporation_date: "2020-01-15",
      legal_nature: "Sociedade Limitada",
      status: "active",
      tax_regime: "simples_nacional"
    },
    phones: [{
      country_code: "55",
      number: "11999887766",
      type: "commercial",
      is_principal: true,
      is_whatsapp: false
    }],
    emails: [{
      email_address: "contato@empresaexemplo.com.br",
      type: "work",
      is_principal: true
    }],
    addresses: [{
      street: "Rua das Flores",
      number: "123",
      neighborhood: "Centro",
      city: "São Paulo",
      state: "SP",
      zip_code: "01310100",
      country: "Brasil",
      type: "commercial",
      is_principal: true
    }]
  };

  const handlePhoneChange = (data) => {
    setFormData(prev => ({ ...prev, phone: data.target.value }));
    console.log('Phone:', data);
  };

  const handleCEPChange = (data) => {
    setFormData(prev => ({ ...prev, cep: data.target.value }));
    console.log('CEP:', data);
  };

  const handleAddressFound = (address) => {
    setAddressData(address);
    console.log('Address found:', address);

    // Exemplo: Preencher formulário de empresa automaticamente
    setCompanyForm(prev => ({
      ...prev,
      address: {
        ...prev.address,
        street: address.street || '',
        neighborhood: address.neighborhood || '',
        city: address.city || '',
        state: address.state || '',
        zip_code: address.zip_code || '',
        ibge_city_code: address.ibge_city_code || null,
        gia_code: address.gia_code || null,
        siafi_code: address.siafi_code || null,
        area_code: address.area_code || null
      }
    }));
  };

  const handleEmailChange = (data) => {
    setFormData(prev => ({ ...prev, email: data.target.value }));
    console.log('Email:', data);
  };

  // Simular carregamento de dados de edição
  const loadTestData = () => {
    setFormData({
      phone: '21987654321',
      cep: '20040020',
      email: 'usuario.carregado@empresa.com.br'
    });
    console.log('Dados de teste carregados');
  };

  const clearData = () => {
    setFormData({
      phone: '',
      cep: '',
      email: ''
    });
    setAddressData(null);
    console.log('Dados limpos');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">
            Demonstração dos Componentes de Input
          </h1>
          
          {/* Botões de teste */}
          <div className="flex gap-4 mb-8">
            <button
              onClick={loadTestData}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Carregar Dados de Teste
            </button>
            <button
              onClick={clearData}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Limpar Dados
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* InputPhone Demo */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">InputPhone</h2>
              <InputPhone
                label="Telefone"
                value={formData.phone}
                onChange={handlePhoneChange}
                required
                placeholder="(11) 99999-9999"
              />
              <div className="text-sm text-gray-600">
                <strong>Valor:</strong> {formData.phone}
              </div>
            </div>

            {/* InputCEP Demo */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">InputCEP</h2>
              <InputCEP
                label="CEP"
                value={formData.cep}
                onChange={handleCEPChange}
                onAddressFound={handleAddressFound}
                required
                placeholder="12345-678"
                showConsultButton={true}
              />
              <div className="text-sm text-gray-600">
                <strong>Valor:</strong> {formData.cep}
              </div>
               {addressData && (
                 <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded space-y-2">
                   <div>
                     <strong>Endereço:</strong><br />
                     {addressData.street}<br />
                     {addressData.neighborhood}, {addressData.city} - {addressData.state}
                   </div>

                   {/* Códigos oficiais brasileiros */}
                   {(addressData.ibge_city_code || addressData.gia_code || addressData.siafi_code || addressData.area_code) && (
                     <div className="mt-2 p-2 bg-blue-50 rounded text-xs">
                       <div className="flex items-center gap-1 text-blue-700 mb-1">
                         📋 <strong>Códigos Oficiais:</strong>
                       </div>
                       <div className="grid grid-cols-2 gap-1 text-blue-600">
                         {addressData.ibge_city_code && (
                           <div><strong>IBGE:</strong> {addressData.ibge_city_code}</div>
                         )}
                         {addressData.area_code && (
                           <div><strong>DDD:</strong> {addressData.area_code}</div>
                         )}
                         {addressData.gia_code && (
                           <div><strong>GIA:</strong> {addressData.gia_code}</div>
                         )}
                         {addressData.siafi_code && (
                           <div><strong>SIAFI:</strong> {addressData.siafi_code}</div>
                         )}
                       </div>
                     </div>
                   )}

                   {/* Status de validação */}
                   {addressData.validation_source && (
                     <div className="mt-2 flex items-center gap-2 text-xs text-green-600">
                       <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                         <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                       </svg>
                       Validado via {addressData.validation_source === 'viacep' ? 'ViaCEP' : addressData.validation_source}
                       {addressData.last_validated_at && (
                         <span className="text-gray-500">
                           • {new Date(addressData.last_validated_at).toLocaleString('pt-BR')}
                         </span>
                       )}
                     </div>
                   )}
                 </div>
               )}
            </div>

            {/* InputEmail Demo */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-800">InputEmail</h2>
              <InputEmail
                label="E-mail"
                value={formData.email}
                onChange={handleEmailChange}
                required
                placeholder="usuario@exemplo.com"
                showIcon={true}
              />
              <div className="text-sm text-gray-600">
                <strong>Valor:</strong> {formData.email}
              </div>
            </div>
          </div>

          {/* Exemplo: Cadastro de Empresa com CEP */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold mb-4 text-blue-800">📋 Exemplo: Cadastro de Empresa com CEP</h3>
            <p className="text-sm text-blue-700 mb-4">
              Quando você informa um CEP no cadastro de empresa, o sistema automaticamente consulta a ViaCEP e preenche os dados do endereço, incluindo códigos oficiais brasileiros.
            </p>

            {/* Demonstração CNPJ com dados mockados */}
            <div className="mb-6 p-4 bg-white rounded border border-blue-200">
              <h4 className="font-medium text-blue-800 mb-3">🏢 Demonstração CNPJ (Dados Mockados)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-blue-700 mb-1">CNPJ</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value="12.345.678/0001-23"
                      readOnly
                      className="flex-1 px-3 py-2 border border-blue-300 rounded-md bg-blue-50 text-blue-900"
                    />
                    <button
                      onClick={() => {
                        setCompanyForm(prev => ({
                          ...prev,
                          name: mockCompanyData.people.name,
                          trade_name: mockCompanyData.people.trade_name,
                          tax_id: mockCompanyData.people.tax_id,
                          address: mockCompanyData.addresses[0]
                        }));
                        toast.success('✅ Dados da empresa preenchidos (mock)!', {
                          duration: 3000,
                          icon: '🏢',
                        });
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      🏢 Preencher
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-blue-700 mb-1">Razão Social</label>
                  <input
                    type="text"
                    value={companyForm.name}
                    onChange={(e) => setCompanyForm(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Será preenchido automaticamente"
                    className="w-full px-3 py-2 border border-blue-300 rounded-md bg-white text-blue-900"
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-blue-800">Razão Social</label>
                <input
                  type="text"
                  value={companyForm.name}
                  onChange={(e) => setCompanyForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Digite a razão social"
                  className="w-full px-3 py-2 border border-blue-300 rounded-md bg-white text-blue-900 placeholder-blue-400"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-blue-800">CNPJ</label>
                <input
                  type="text"
                  value={companyForm.tax_id}
                  onChange={(e) => setCompanyForm(prev => ({ ...prev, tax_id: e.target.value }))}
                  placeholder="00.000.000/0000-00"
                  className="w-full px-3 py-2 border border-blue-300 rounded-md bg-white text-blue-900 placeholder-blue-400"
                />
              </div>
            </div>

            <div className="mt-4 p-3 bg-white rounded border border-blue-200">
              <h4 className="font-medium text-blue-800 mb-2">📍 Endereço (Preenchido Automaticamente)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 text-sm">
                <div>
                  <span className="font-medium text-blue-700">Logradouro:</span>
                  <p className="text-blue-900">{companyForm.address.street || 'Não informado'}</p>
                </div>
                <div>
                  <span className="font-medium text-blue-700">Bairro:</span>
                  <p className="text-blue-900">{companyForm.address.neighborhood || 'Não informado'}</p>
                </div>
                <div>
                  <span className="font-medium text-blue-700">Cidade:</span>
                  <p className="text-blue-900">{companyForm.address.city || 'Não informado'}</p>
                </div>
                <div>
                  <span className="font-medium text-blue-700">Estado:</span>
                  <p className="text-blue-900">{companyForm.address.state || 'Não informado'}</p>
                </div>
              </div>

              {(companyForm.address.ibge_city_code || companyForm.address.area_code) && (
                <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
                  <h5 className="font-medium text-blue-800 mb-1">📊 Códigos Oficiais (ViaCEP):</h5>
                  <div className="flex flex-wrap gap-4 text-xs text-blue-700">
                    {companyForm.address.ibge_city_code && (
                      <span><strong>IBGE:</strong> {companyForm.address.ibge_city_code}</span>
                    )}
                    {companyForm.address.area_code && (
                      <span><strong>DDD:</strong> {companyForm.address.area_code}</span>
                    )}
                    {companyForm.address.gia_code && (
                      <span><strong>GIA:</strong> {companyForm.address.gia_code}</span>
                    )}
                    {companyForm.address.siafi_code && (
                      <span><strong>SIAFI:</strong> {companyForm.address.siafi_code}</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* JSON Debug */}
          <div className="mt-8 p-4 bg-gray-100 rounded">
            <h3 className="font-semibold mb-2">Dados do Formulário:</h3>
            <pre className="text-sm text-gray-700">
              {JSON.stringify({ formData, addressData, companyForm }, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InputsDemo;