import React, { useState } from "react";
import { MessageCircle, Check, Clock } from "lucide-react";
import Input from "../ui/Input";

const InputWhatsApp = ({
  phone,
  onChange,
  disabled = false,
  showAdvancedFields = false,
  ...props
}) => {
  const [showAdvanced, setShowAdvanced] = useState(showAdvancedFields);

  const handleWhatsAppChange = (field, value) => {
    onChange({
      ...phone,
      [field]: value,
      // Se habilita WhatsApp, marcar como verificado por padrão
      ...(field === "is_whatsapp" && value ? { whatsapp_verified: true } : {}),
    });
  };

  return (
    <div className="space-y-4">
      {/* Checkbox principal do WhatsApp */}
      <label className="flex items-center text-sm">
        <input
          type="checkbox"
          checked={phone.is_whatsapp || false}
          onChange={(e) =>
            handleWhatsAppChange("is_whatsapp", e.target.checked)
          }
          disabled={disabled}
          className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
        />
        <MessageCircle className="h-4 w-4 mr-1 text-green-600" />
        WhatsApp
      </label>

      {/* Campos avançados do WhatsApp */}
      {phone.is_whatsapp && (
        <div className="pl-6 space-y-3 border-l-2 border-green-200 dark:border-green-800">
          {/* WhatsApp Business */}
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={phone.whatsapp_business || false}
              onChange={(e) =>
                handleWhatsAppChange("whatsapp_business", e.target.checked)
              }
              disabled={disabled}
              className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
            />
            Conta Business
          </label>

          {/* Nome no WhatsApp */}
          {showAdvanced && (
            <Input
              label="Nome no WhatsApp"
              value={phone.whatsapp_name || ""}
              onChange={(e) =>
                handleWhatsAppChange("whatsapp_name", e.target.value)
              }
              placeholder="Nome exibido no WhatsApp"
              disabled={disabled}
              size="sm"
            />
          )}

          {/* Configurações de marketing */}
          <div className="space-y-2">
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={phone.accepts_whatsapp_marketing || false}
                onChange={(e) =>
                  handleWhatsAppChange(
                    "accepts_whatsapp_marketing",
                    e.target.checked
                  )
                }
                disabled={disabled}
                className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
              />
              Aceita marketing via WhatsApp
            </label>

            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={phone.accepts_whatsapp_notifications || false}
                onChange={(e) =>
                  handleWhatsAppChange(
                    "accepts_whatsapp_notifications",
                    e.target.checked
                  )
                }
                disabled={disabled}
                className="mr-2 rounded border-border focus:ring-ring focus:ring-2"
              />
              Aceita notificações via WhatsApp
            </label>
          </div>

          {/* Horário preferido (apenas se avançado) */}
          {showAdvanced && (
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  <Clock className="inline h-3 w-3 mr-1" />
                  Horário início
                </label>
                <input
                  type="time"
                  value={phone.whatsapp_preferred_time_start || "09:00"}
                  onChange={(e) =>
                    handleWhatsAppChange(
                      "whatsapp_preferred_time_start",
                      e.target.value
                    )
                  }
                  disabled={disabled}
                  className="w-full px-2 py-1 text-xs border border-border rounded bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  <Clock className="inline h-3 w-3 mr-1" />
                  Horário fim
                </label>
                <input
                  type="time"
                  value={phone.whatsapp_preferred_time_end || "18:00"}
                  onChange={(e) =>
                    handleWhatsAppChange(
                      "whatsapp_preferred_time_end",
                      e.target.value
                    )
                  }
                  disabled={disabled}
                  className="w-full px-2 py-1 text-xs border border-border rounded bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                />
              </div>
            </div>
          )}

          {/* Status de verificação */}
          {showAdvanced && phone.whatsapp_verified && (
            <div className="flex items-center text-xs text-green-600 bg-green-50 dark:bg-green-900/20 p-2 rounded">
              <Check className="h-3 w-3 mr-1" />
              WhatsApp verificado
              {phone.whatsapp_verified_at && (
                <span className="ml-1 text-muted-foreground">
                  em{" "}
                  {new Date(phone.whatsapp_verified_at).toLocaleDateString(
                    "pt-BR"
                  )}
                </span>
              )}
            </div>
          )}

          {/* Toggle campos avançados */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-blue-600 hover:text-blue-700 focus:outline-none"
            disabled={disabled}
          >
            {showAdvanced ? "Ocultar" : "Mostrar"} campos avançados
          </button>
        </div>
      )}
    </div>
  );
};

export default InputWhatsApp;
