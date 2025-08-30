import React, { useState } from 'react';
import { InputPhone, InputCEP, InputEmail } from '../components/inputs';

const InputsDemo = () => {
  const [formData, setFormData] = useState({
    phone: '11999887766', // Telefone de teste pré-carregado
    cep: '01310100', // CEP de teste pré-carregado
    email: 'teste@exemplo.com' // Email de teste pré-carregado
  });
  
  const [addressData, setAddressData] = useState(null);

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
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                  <strong>Endereço:</strong><br />
                  {addressData.street}<br />
                  {addressData.neighborhood}, {addressData.city} - {addressData.state}
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

          {/* JSON Debug */}
          <div className="mt-8 p-4 bg-gray-100 rounded">
            <h3 className="font-semibold mb-2">Dados do Formulário:</h3>
            <pre className="text-sm text-gray-700">
              {JSON.stringify({ formData, addressData }, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InputsDemo;