import React, { FormEvent } from "react";
import Button from "../ui/Button";
import { FormErrorBoundary } from "../error";
import Card from "../ui/Card";
import { Save, X } from "lucide-react";
import {
  PhoneInputGroup,
  EmailInputGroup,
  AddressInputGroup,
} from "../contacts";
import {
  EstablishmentBasicDataSection,
  AddressNumberConfirmationModal,
} from "./EstablishmentFormSections";
import { useEstablishmentForm } from "../../hooks/useEstablishmentForm";

interface EstablishmentFormProps {
  establishmentId?: number;
  companyId?: number;
  onSave?: () => void;
  onCancel?: () => void;
  onNavigateToClients?: (
    establishmentId: number,
    establishmentCode: string
  ) => void;
}

const EstablishmentForm: React.FC<EstablishmentFormProps> = React.memo(
  ({ establishmentId, companyId, onSave, onCancel, onNavigateToClients }) => {
    return (
      <FormErrorBoundary formName="EstablishmentForm">
        <EstablishmentFormContent
          establishmentId={establishmentId}
          companyId={companyId}
          onSave={onSave}
          onCancel={onCancel}
          onNavigateToClients={onNavigateToClients}
        />
      </FormErrorBoundary>
    );
  }
);

const EstablishmentFormContent: React.FC<EstablishmentFormProps> = ({
  establishmentId,
  companyId,
  onSave,
  onCancel,
  onNavigateToClients,
}) => {
  const {
    loading,
    error,
    formData,
    companies,
    showNumberConfirmation,
    isEditing,
    isCompanyPreselected,
    updatePerson,
    updateEstablishment,
    updateFormData,
    handlePhonesChange,
    handlePhoneAdd,
    handlePhoneRemove,
    handleEmailsChange,
    handleEmailAdd,
    handleEmailRemove,
    handleAddressesChange,
    handleAddressAdd,
    handleAddressRemove,
    handleNumberConfirmation,
    proceedWithSave,
    setShowNumberConfirmation,
    setPendingAddresses,
  } = useEstablishmentForm({
    establishmentId,
    companyId,
    onSave,
    onNavigateToClients,
  });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    // Verificar se há endereços sem número
    const addressesWithoutNumber = formData.addresses.filter(
      (address) =>
        address.street?.trim() &&
        address.city?.trim() &&
        !address.number?.trim()
    );

    if (addressesWithoutNumber.length > 0) {
      // Mostrar modal de confirmação para endereços sem número
      setPendingAddresses(formData);
      setShowNumberConfirmation(true);
    } else {
      // Prosseguir direto com o salvamento
      await proceedWithSave(formData);
    }
  };

  return (
    <div className="space-y-6">
      <form
        onSubmit={handleSubmit}
        className="space-y-6"
        aria-labelledby="form-title"
        aria-describedby="form-description"
        noValidate
      >
        {/* Header */}
        <header
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-4"
          role="banner"
        >
          <div className="min-w-0">
            <h1
              id="form-title"
              className="text-2xl font-bold text-foreground"
              tabIndex={-1}
            >
              {isEditing ? "Editar Estabelecimento" : "Novo Estabelecimento"}
            </h1>
            <p className="text-muted-foreground" id="form-description">
              {isEditing
                ? "Atualize as informações do estabelecimento"
                : "Cadastre um novo estabelecimento no sistema"}
            </p>
          </div>
          <div
            className="flex gap-3 shrink-0"
            role="group"
            aria-label="Ações do formulário"
          >
            <Button
              variant="secondary"
              outline
              onClick={onCancel}
              icon={<X className="h-4 w-4" />}
              className="flex-1 sm:flex-none"
              aria-label="Cancelar edição e fechar formulário"
            >
              <span className="hidden sm:inline">Cancelar</span>
              <span className="sm:hidden">Cancelar</span>
            </Button>
            <Button
              type="submit"
              disabled={loading}
              icon={<Save className="h-4 w-4" />}
              className="flex-1 sm:flex-none"
              aria-label={
                loading
                  ? "Salvando estabelecimento, aguarde..."
                  : isEditing
                  ? "Salvar alterações do estabelecimento"
                  : "Salvar novo estabelecimento"
              }
            >
              <span className="hidden sm:inline">
                {loading ? "Salvando..." : "Salvar"}
              </span>
              <span className="sm:hidden">
                {loading ? "Salvando..." : "Salvar"}
              </span>
            </Button>
          </div>
        </header>

        {error && (
          <div
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            role="alert"
            aria-live="polite"
            id="form-error"
          >
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Dados do Estabelecimento */}
        <EstablishmentBasicDataSection
          formData={formData}
          companies={companies}
          loading={loading}
          isEditing={isEditing}
          isCompanyPreselected={isCompanyPreselected}
          onUpdatePerson={updatePerson}
          onUpdateEstablishment={updateEstablishment}
          onUpdateFormData={updateFormData}
          onUpdatePhones={handlePhonesChange}
          onUpdateEmails={handleEmailsChange}
          onUpdateAddresses={handleAddressesChange}
        />

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
      <AddressNumberConfirmationModal
        show={showNumberConfirmation}
        onConfirm={handleNumberConfirmation}
      />
    </div>
  );
};

EstablishmentForm.displayName = "EstablishmentForm";

export default EstablishmentForm;
