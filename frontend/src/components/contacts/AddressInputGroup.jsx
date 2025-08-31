import React from 'react';
import { Plus, Trash2, Star, StarOff, MapPin } from 'lucide-react';
import { InputCEP } from '../inputs';
import Input from '../ui/Input';
import Button from '../ui/Button';

const AddressInputGroup = ({
  addresses = [],
  onChange,
  onAdd,
  onRemove,
  required = true,
  disabled = false,
  showValidation = true,
  minAddresses = 1,
  maxAddresses = 3,
  title = "Endereços",
  ...props
}) => {
  const handleAddressChange = (index, field, value) => {
    const updatedAddresses = addresses.map((address, i) => 
      i === index ? { ...address, [field]: value } : address
    );
    onChange?.(updatedAddresses);
  };

  const handleAddAddress = () => {
    if (addresses.length >= maxAddresses) return;
    
    const newAddress = {
      street: '',
      number: '',
      details: '',
      neighborhood: '',
      city: '',
      state: '',
      zip_code: '',
      country: 'Brasil',
      type: 'commercial',
      is_principal: addresses.length === 0 // Primeiro é principal
    };
    
    onAdd?.(newAddress);
  };

  const handleRemoveAddress = (index) => {
    if (addresses.length <= minAddresses) return;
    onRemove?.(index);
  };

  const setPrincipal = (index) => {
    const updatedAddresses = addresses.map((address, i) => ({
      ...address,
      is_principal: i === index
    }));
    onChange?.(updatedAddresses);
  };

  const handleAddressFound = (index, addressData) => {
    const updatedAddresses = addresses.map((address, i) =>
      i === index ? {
        ...address,
        // Dados básicos do endereço
        street: addressData.street || '',
        number: '', // Limpar número para usuário preencher
        details: addressData.complement || '', // Usar complemento da ViaCEP
        neighborhood: addressData.neighborhood || '',
        city: addressData.city || '',
        state: addressData.state || '',
        zip_code: addressData.zip_code || addressData.cep || '',

        // Códigos oficiais brasileiros
        ibge_city_code: addressData.ibge_city_code || null,
        gia_code: addressData.gia_code || null,
        siafi_code: addressData.siafi_code || null,
        area_code: addressData.area_code || null,

        // Campos de validação
        is_validated: addressData.is_validated || false,
        validation_source: addressData.validation_source || null,
        last_validated_at: addressData.last_validated_at || null,

        // Campos de geolocalização (futuros)
        latitude: addressData.latitude || null,
        longitude: addressData.longitude || null,
        google_place_id: addressData.google_place_id || null,
        formatted_address: addressData.formatted_address || null,
        geocoding_accuracy: addressData.geocoding_accuracy || null,
        geocoding_source: addressData.geocoding_source || null,
        api_data: addressData.api_data || null
      } : address
    );
    onChange?.(updatedAddresses);
  };

  const addressTypes = [
    { value: 'commercial', label: 'Comercial' },
    { value: 'residential', label: 'Residencial' },
    { value: 'billing', label: 'Cobrança' },
    { value: 'delivery', label: 'Entrega' },
    { value: 'other', label: 'Outro' }
  ];

  const getValidAddresses = () => {
    return addresses.filter(addr => addr.street && addr.city && addr.zip_code);
  };

  const getAddressDisplay = (address) => {
    const parts = [];
    if (address.street) parts.push(address.street);
    if (address.number) parts.push(address.number);
    if (address.neighborhood) parts.push(address.neighborhood);
    if (address.city) parts.push(address.city);
    if (address.state) parts.push(address.state);
    if (address.zip_code) parts.push(address.zip_code);
    
    return parts.join(', ');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-foreground">
          {title}
          {required && <span className="text-red-500 ml-1">*</span>}
        </h3>
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">
            {addresses.length} de {maxAddresses} endereços
          </div>
          {/* Mobile: Apenas ícone + */}
          <div className="block sm:hidden">
            <Button
              type="button"
              variant="secondary"
              outline
              size="sm"
              onClick={handleAddAddress}
              disabled={disabled || addresses.length >= maxAddresses}
              title={addresses.length >= maxAddresses ? `Máximo de ${maxAddresses} endereços atingido` : "Adicionar endereço"}
              className="w-8 h-8 p-0 flex items-center justify-center"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Desktop: Ícone + Texto */}
          <div className="hidden sm:block">
            <Button
              type="button"
              variant="secondary"
              outline
              size="sm"
              onClick={handleAddAddress}
              disabled={disabled || addresses.length >= maxAddresses}
              icon={<Plus className="h-4 w-4" />}
              title={addresses.length >= maxAddresses ? `Máximo de ${maxAddresses} endereços atingido` : "Adicionar endereço"}
            >
              Adicionar
            </Button>
          </div>
        </div>
      </div>

      {/* Lista de endereços */}
      <div className="space-y-6">
        {addresses.map((address, index) => (
          <div key={index} className="space-y-4 p-4 border border-border rounded-lg bg-card">
            {/* Header do endereço */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <h4 className="font-medium text-foreground">Endereço {index + 1}</h4>
                {address.is_principal && (
                  <Star className="h-4 w-4 text-yellow-500 fill-current" title="Endereço principal" />
                )}
              </div>

              {/* Botão principal */}
              <button
                type="button"
                onClick={() => setPrincipal(index)}
                disabled={disabled}
                className={`flex items-center text-sm p-1 rounded transition-colors ${
                  address.is_principal
                    ? 'text-yellow-600 hover:text-yellow-700'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
                title={address.is_principal ? 'Endereço principal' : 'Definir como principal'}
              >
                {address.is_principal ? (
                  <Star className="h-4 w-4 fill-current" />
                ) : (
                  <StarOff className="h-4 w-4" />
                )}
              </button>
            </div>

            {/* Campos do endereço */}
            <div className="space-y-4">
              {/* CEP e Tipo - primeira linha */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <InputCEP
                  label="CEP *"
                  value={address.zip_code}
                  onChange={(data) => handleAddressChange(index, 'zip_code', data.target.value)}
                  onAddressFound={(addressData) => handleAddressFound(index, addressData)}
                  placeholder="12345-678"
                  required={required}
                  disabled={disabled}
                  showValidation={showValidation}
                  showConsultButton={true}
                  autoConsult={false}
                />

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Tipo
                  </label>
                  <select
                    value={address.type}
                    onChange={(e) => handleAddressChange(index, 'type', e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                  >
                    {addressTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="País"
                  value={address.country}
                  onChange={(e) => handleAddressChange(index, 'country', e.target.value)}
                  placeholder="Brasil"
                  disabled={disabled}
                />
              </div>
              
              {/* Logradouro e Número - segunda linha */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Logradouro"
                  value={address.street}
                  onChange={(e) => handleAddressChange(index, 'street', e.target.value)}
                  placeholder="Rua, Avenida, etc."
                  disabled={disabled}
                />
                
                <Input
                  label="Número"
                  value={address.number}
                  onChange={(e) => handleAddressChange(index, 'number', e.target.value)}
                  placeholder="123"
                  disabled={disabled}
                />
                
                <Input
                  label="Complemento"
                  value={address.details || ''}
                  onChange={(e) => handleAddressChange(index, 'details', e.target.value)}
                  placeholder="Sala, Andar, etc."
                  disabled={disabled}
                />
              </div>

              {/* Bairro, Cidade e Estado - terceira linha */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Bairro"
                  value={address.neighborhood}
                  onChange={(e) => handleAddressChange(index, 'neighborhood', e.target.value)}
                  placeholder="Centro, Bela Vista, etc."
                  disabled={disabled}
                />
                
                <Input
                  label="Cidade"
                  value={address.city}
                  onChange={(e) => handleAddressChange(index, 'city', e.target.value)}
                  placeholder="São Paulo"
                  disabled={disabled}
                />
                
                <Input
                  label="Estado"
                  value={address.state}
                  onChange={(e) => handleAddressChange(index, 'state', e.target.value)}
                  placeholder="SP"
                  maxLength={2}
                  disabled={disabled}
                />
              </div>
            </div>

            {/* Códigos oficiais brasileiros */}
            {(address.ibge_city_code || address.gia_code || address.siafi_code || address.area_code) && (
              <div className="text-xs text-muted-foreground bg-blue-50 border border-blue-200 p-2 rounded">
                <div className="flex items-center gap-1 text-blue-700 mb-1">
                  📋 <strong>Códigos Oficiais:</strong>
                </div>
                <div className="grid grid-cols-2 gap-1 text-blue-600">
                  {address.ibge_city_code && (
                    <div><strong>IBGE:</strong> {address.ibge_city_code}</div>
                  )}
                  {address.area_code && (
                    <div><strong>DDD:</strong> {address.area_code}</div>
                  )}
                  {address.gia_code && (
                    <div><strong>GIA:</strong> {address.gia_code}</div>
                  )}
                  {address.siafi_code && (
                    <div><strong>SIAFI:</strong> {address.siafi_code}</div>
                  )}
                </div>
                {address.validation_source && (
                  <div className="mt-1 flex items-center gap-1 text-green-600">
                    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Validado via {address.validation_source === 'viacep' ? 'ViaCEP' : address.validation_source}
                  </div>
                )}
              </div>
            )}

            {/* Preview do endereço */}
            {getAddressDisplay(address) && (
              <div className="text-xs text-muted-foreground bg-muted/30 p-2 rounded border">
                <strong>Endereço completo:</strong> {getAddressDisplay(address)}
              </div>
            )}

            {/* Linha do botão remover */}
            <div className="flex justify-start pt-2 border-t border-border mt-4">
              <Button
                type="button"
                variant="danger"
                outline
                size="sm"
                onClick={() => handleRemoveAddress(index)}
                disabled={addresses.length <= minAddresses || disabled}
                icon={<Trash2 className="h-4 w-4" />}
                title={addresses.length <= minAddresses ? `Deve ter pelo menos ${minAddresses} endereço(s)` : "Remover endereço"}
              >
                Remover
              </Button>
            </div>
          </div>
        ))}
      </div>



      {/* Validações e dicas */}
      {required && getValidAddresses().length === 0 && (
        <p className="text-sm text-red-600">
          Pelo menos um endereço é obrigatório
        </p>
      )}

      {addresses.length > 0 && !addresses.some(a => a.is_principal && a.street && a.city) && (
        <p className="text-sm text-orange-600">
          Selecione um endereço como principal
        </p>
      )}

      {!required && addresses.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Nenhum endereço cadastrado
        </p>
      )}


    </div>
  );
};

export default AddressInputGroup;