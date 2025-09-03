import React from "react";
import { Plus, Trash2, Star, StarOff } from "lucide-react";
import { InputEmail } from "../inputs";
import Button from "../ui/Button";

const EmailInputGroup = ({
  emails = [],
  onChange,
  onAdd,
  onRemove,
  required = true,
  disabled = false,
  showValidation = true,
  minEmails = 1,
  maxEmails = 5,
  title = "E-mails",
  ...props
}) => {
  const handleEmailChange = (index, field, value) => {
    const updatedEmails = emails.map((email, i) =>
      i === index ? { ...email, [field]: value } : email
    );
    onChange?.(updatedEmails);
  };

  const handleAddEmail = () => {
    if (emails.length >= maxEmails) return;

    const newEmail = {
      email_address: "",
      type: "work",
      is_principal: emails.length === 0, // Primeiro é principal
      is_newsletter: false,
    };

    onAdd?.(newEmail);
  };

  const handleRemoveEmail = (index) => {
    if (emails.length <= minEmails) return;
    onRemove?.(index);
  };

  const setPrincipal = (index) => {
    const updatedEmails = emails.map((email, i) => ({
      ...email,
      is_principal: i === index,
    }));
    onChange?.(updatedEmails);
  };

  const emailTypes = [
    { value: "work", label: "Trabalho" },
    { value: "personal", label: "Pessoal" },
    { value: "billing", label: "Cobrança" },
    { value: "support", label: "Suporte" },
    { value: "marketing", label: "Marketing" },
    { value: "other", label: "Outro" },
  ];

  const getValidEmails = () => {
    return emails.filter(
      (email) => email.email_address && email.email_address.trim()
    );
  };

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
          <div className="text-sm text-muted-foreground">
            {emails.length} de {maxEmails} e-mails
          </div>
          {/* Mobile: Apenas ícone + */}
          <div className="block sm:hidden">
            <Button
              type="button"
              variant="secondary"
              outline
              size="sm"
              onClick={handleAddEmail}
              disabled={disabled || emails.length >= maxEmails}
              title={
                emails.length >= maxEmails
                  ? `Máximo de ${maxEmails} e-mails atingido`
                  : "Adicionar e-mail"
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
              onClick={handleAddEmail}
              disabled={disabled || emails.length >= maxEmails}
              icon={<Plus className="h-4 w-4" />}
              title={
                emails.length >= maxEmails
                  ? `Máximo de ${maxEmails} e-mails atingido`
                  : "Adicionar e-mail"
              }
            >
              Adicionar
            </Button>
          </div>
        </div>
      </div>

      {/* Lista de e-mails */}
      <div className="space-y-4">
        {emails.map((email, index) => (
          <div
            key={index}
            className="space-y-4 p-4 border border-border rounded-lg bg-card"
          >
            {/* Linha dos inputs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              {/* Endereço de e-mail */}
              <div className="md:col-span-1">
                <InputEmail
                  label={`E-mail ${index + 1}`}
                  value={email.email_address}
                  onChange={(data) =>
                    handleEmailChange(index, "email_address", data.target.value)
                  }
                  placeholder="contato@empresa.com"
                  required={required && index === 0} // Apenas o primeiro é obrigatório se required=true
                  disabled={disabled}
                  showValidation={showValidation}
                  showIcon={true}
                />
              </div>

              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Tipo
                </label>
                <select
                  value={email.type}
                  onChange={(e) =>
                    handleEmailChange(index, "type", e.target.value)
                  }
                  disabled={disabled}
                  className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                >
                  {emailTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Configurações */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">
                  Configurações
                </label>

                {/* Principal */}
                <div className="flex items-center">
                  <button
                    type="button"
                    onClick={() => setPrincipal(index)}
                    disabled={disabled}
                    className={`flex items-center text-sm p-1 rounded transition-colors ${
                      email.is_principal
                        ? "text-yellow-600 hover:text-yellow-700"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                    title={
                      email.is_principal
                        ? "E-mail principal"
                        : "Definir como principal"
                    }
                  >
                    {email.is_principal ? (
                      <Star className="h-4 w-4 mr-1 fill-current" />
                    ) : (
                      <StarOff className="h-4 w-4 mr-1" />
                    )}
                    Principal
                  </button>
                </div>

                {/* Newsletter */}
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={email.is_newsletter || false}
                    onChange={(e) =>
                      handleEmailChange(
                        index,
                        "is_newsletter",
                        e.target.checked
                      )
                    }
                    disabled={disabled}
                    className="mr-2 rounded"
                  />
                  Newsletter
                </label>
              </div>
            </div>

            {/* Linha do botão remover */}
            <div className="flex justify-start pt-2 border-t border-border">
              <Button
                type="button"
                variant="danger"
                outline
                size="sm"
                onClick={() => handleRemoveEmail(index)}
                disabled={emails.length <= minEmails || disabled}
                icon={<Trash2 className="h-4 w-4" />}
                title={
                  emails.length <= minEmails
                    ? `Deve ter pelo menos ${minEmails} e-mail(s)`
                    : "Remover e-mail"
                }
              >
                Remover
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Validações e dicas */}
      {required && getValidEmails().length === 0 && (
        <p className="text-sm text-red-600">
          Pelo menos um e-mail é obrigatório
        </p>
      )}

      {emails.length > 0 &&
        !emails.some((e) => e.is_principal && e.email_address) && (
          <p className="text-sm text-orange-600">
            Selecione um e-mail como principal
          </p>
        )}

      {!required && emails.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Nenhum e-mail cadastrado
        </p>
      )}
    </div>
  );
};

export default EmailInputGroup;
