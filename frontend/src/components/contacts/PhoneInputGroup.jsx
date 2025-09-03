import React, { useState } from "react";
import { Plus, Trash2, Star, StarOff, Phone, Settings } from "lucide-react";
import { InputPhone, InputWhatsApp } from "../inputs";
import Input from "../ui/Input";
import Button from "../ui/Button";
import { PhoneType, PhoneTypeLabels } from "../../types";

const PhoneInputGroup = ({
  phones = [],
  onChange,
  onAdd,
  onRemove,
  required = true,
  disabled = false,
  showValidation = true,
  minPhones = 1,
  maxPhones = 5,
  title = "Telefones",
  showAdvancedFields = false,
  ...props
}) => {
  const [advancedMode, setAdvancedMode] = useState(showAdvancedFields);
  const handlePhoneChange = (index, field, value) => {
    const updatedPhones = phones.map((phone, i) =>
      i === index ? { ...phone, [field]: value } : phone
    );
    onChange?.(updatedPhones);
  };

  const handleAddPhone = () => {
    if (phones.length >= maxPhones) return;

    const newPhone = {
      country_code: "55",
      number: "",
      extension: "",
      type: PhoneType.COMMERCIAL, // 🔄 Enum sincronizado
      is_principal: phones.length === 0,
      is_active: true,
      phone_name: "",
      is_whatsapp: false,
      whatsapp_verified: false,
      whatsapp_business: false,
      whatsapp_name: "",
      accepts_whatsapp_marketing: true,
      accepts_whatsapp_notifications: true,
      whatsapp_preferred_time_start: "09:00",
      whatsapp_preferred_time_end: "18:00",
      carrier: "",
      line_type: "postpaid",
      contact_priority: 5,
      can_receive_calls: true,
      can_receive_sms: true,
    };

    onAdd?.(newPhone);
  };

  const handleRemovePhone = (index) => {
    if (phones.length <= minPhones) return;
    onRemove?.(index);
  };

  const setPrincipal = (index) => {
    const updatedPhones = phones.map((phone, i) => ({
      ...phone,
      is_principal: i === index,
    }));
    onChange?.(updatedPhones);
  };

  const phoneTypes = [
    { value: "commercial", label: "Comercial" },
    { value: "mobile", label: "Celular" },
    { value: "residential", label: "Residencial" },
    { value: "fax", label: "Fax" },
    { value: "other", label: "Outro" },
  ];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="flex items-center text-lg font-medium text-foreground">
          {title}
          {required && (
            <Star className="h-3 w-3 text-red-500 ml-1 fill-current" />
          )}
        </h3>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setAdvancedMode(!advancedMode)}
            className="flex items-center text-xs text-blue-600 hover:text-blue-700 focus:outline-none"
            disabled={disabled}
          >
            <Settings className="h-3 w-3 mr-1" />
            {advancedMode ? "Modo Simples" : "Modo Avançado"}
          </button>
          <div className="text-sm text-muted-foreground">
            {phones.length} de {maxPhones} telefones
          </div>
          {/* Mobile: Apenas ícone + */}
          <div className="block sm:hidden">
            <Button
              type="button"
              variant="secondary"
              outline
              size="sm"
              onClick={handleAddPhone}
              disabled={disabled || phones.length >= maxPhones}
              title={
                phones.length >= maxPhones
                  ? `Máximo de ${maxPhones} telefones atingido`
                  : "Adicionar telefone"
              }
              className="w-10 h-10 p-0 flex items-center justify-center"
            >
              <Plus className="h-5 w-5" />
            </Button>
          </div>

          {/* Desktop: Ícone + Texto */}
          <div className="hidden sm:block">
            <Button
              type="button"
              variant="secondary"
              outline
              size="sm"
              onClick={handleAddPhone}
              disabled={disabled || phones.length >= maxPhones}
              icon={<Plus className="h-4 w-4" />}
              title={
                phones.length >= maxPhones
                  ? `Máximo de ${maxPhones} telefones atingido`
                  : "Adicionar telefone"
              }
            >
              Adicionar
            </Button>
          </div>
        </div>
      </div>

      {/* Lista de telefones */}
      <div className="space-y-4">
        {phones.map((phone, index) => (
          <div
            key={index}
            className="space-y-4 p-4 border border-border rounded-lg bg-card"
          >
            {/* Linha dos inputs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              {/* Número do telefone */}
              <div className="md:col-span-1">
                <InputPhone
                  label={`Telefone ${index + 1}`}
                  value={phone.number}
                  onChange={(data) =>
                    handlePhoneChange(index, "number", data.target.value)
                  }
                  placeholder="(11) 99999-9999"
                  required={required}
                  disabled={disabled}
                  showValidation={showValidation}
                />
              </div>

              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Tipo
                </label>
                <select
                  value={phone.type}
                  onChange={(e) =>
                    handlePhoneChange(index, "type", e.target.value)
                  }
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  {phoneTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Configurações básicas */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">
                  Configurações
                </label>

                {/* Principal */}
                <label className="flex items-center text-sm">
                  <input
                    type="radio"
                    name="principal_phone"
                    checked={phone.is_principal}
                    onChange={() => setPrincipal(index)}
                    disabled={disabled}
                    className="mr-2"
                  />
                  <Star
                    className={`h-3 w-3 mr-1 ${
                      phone.is_principal
                        ? "text-yellow-500 fill-current"
                        : "text-muted-foreground"
                    }`}
                  />
                  Principal
                </label>

                {/* Ativo */}
                {advancedMode && (
                  <label className="flex items-center text-sm">
                    <input
                      type="checkbox"
                      checked={phone.is_active !== false}
                      onChange={(e) =>
                        handlePhoneChange(index, "is_active", e.target.checked)
                      }
                      disabled={disabled}
                      className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
                    />
                    Ativo
                  </label>
                )}
              </div>
            </div>

            {/* Campos avançados */}
            {advancedMode && (
              <div className="space-y-4 pt-4 border-t border-border">
                {/* Linha 1: Ramal, Nome do Contato, Operadora */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="Ramal"
                    value={phone.extension || ""}
                    onChange={(e) =>
                      handlePhoneChange(index, "extension", e.target.value)
                    }
                    placeholder="1234"
                    disabled={disabled}
                    size="sm"
                  />
                  <Input
                    label="Nome do Contato"
                    value={phone.phone_name || ""}
                    onChange={(e) =>
                      handlePhoneChange(index, "phone_name", e.target.value)
                    }
                    placeholder="João da Silva"
                    disabled={disabled}
                    size="sm"
                  />
                  <Input
                    label="Operadora"
                    value={phone.carrier || ""}
                    onChange={(e) =>
                      handlePhoneChange(index, "carrier", e.target.value)
                    }
                    placeholder="Vivo, Tim, Claro..."
                    disabled={disabled}
                    size="sm"
                  />
                </div>

                {/* Linha 2: Tipo de Linha, Prioridade */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Tipo de Linha
                    </label>
                    <select
                      value={phone.line_type || "postpaid"}
                      onChange={(e) =>
                        handlePhoneChange(index, "line_type", e.target.value)
                      }
                      disabled={disabled}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                    >
                      <option value="postpaid">Pós-pago</option>
                      <option value="prepaid">Pré-pago</option>
                      <option value="corporate">Corporativo</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Prioridade (1-10)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={phone.contact_priority || 5}
                      onChange={(e) =>
                        handlePhoneChange(
                          index,
                          "contact_priority",
                          parseInt(e.target.value)
                        )
                      }
                      disabled={disabled}
                      className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                    />
                  </div>
                </div>

                {/* Linha 3: Configurações de contato */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-foreground">
                      Pode receber
                    </label>
                    <label className="flex items-center text-sm">
                      <input
                        type="checkbox"
                        checked={phone.can_receive_calls !== false}
                        onChange={(e) =>
                          handlePhoneChange(
                            index,
                            "can_receive_calls",
                            e.target.checked
                          )
                        }
                        disabled={disabled}
                        className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
                      />
                      Chamadas
                    </label>
                    <label className="flex items-center text-sm">
                      <input
                        type="checkbox"
                        checked={phone.can_receive_sms !== false}
                        onChange={(e) =>
                          handlePhoneChange(
                            index,
                            "can_receive_sms",
                            e.target.checked
                          )
                        }
                        disabled={disabled}
                        className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
                      />
                      SMS
                    </label>
                  </div>
                </div>

                {/* WhatsApp Avançado */}
                <InputWhatsApp
                  phone={phone}
                  onChange={(updatedPhone) => {
                    const updatedPhones = phones.map((p, i) =>
                      i === index ? updatedPhone : p
                    );
                    onChange?.(updatedPhones);
                  }}
                  disabled={disabled}
                  showAdvancedFields={true}
                />
              </div>
            )}

            {/* WhatsApp básico (modo simples) */}
            {!advancedMode && (
              <InputWhatsApp
                phone={phone}
                onChange={(updatedPhone) => {
                  const updatedPhones = phones.map((p, i) =>
                    i === index ? updatedPhone : p
                  );
                  onChange?.(updatedPhones);
                }}
                disabled={disabled}
                showAdvancedFields={false}
              />
            )}

            {/* Linha do botão remover */}
            <div className="flex justify-start pt-2 border-t border-border">
              <Button
                type="button"
                variant="danger"
                outline
                size="sm"
                onClick={() => handleRemovePhone(index)}
                disabled={phones.length <= minPhones || disabled}
                icon={<Trash2 className="h-4 w-4" />}
                title={
                  phones.length <= minPhones
                    ? `Deve ter pelo menos ${minPhones} telefone(s)`
                    : "Remover telefone"
                }
              >
                Remover
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Validações e dicas */}
      {required && phones.length === 0 && (
        <p className="text-sm text-red-600">
          Pelo menos um telefone é obrigatório
        </p>
      )}

      {phones.length > 0 && !phones.some((p) => p.is_principal) && (
        <p className="text-sm text-orange-600">
          Selecione um telefone como principal
        </p>
      )}

      {!required && phones.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Nenhum telefone cadastrado
        </p>
      )}
    </div>
  );
};

export default PhoneInputGroup;
