import React, { FormEvent, useState } from "react";
import Button from "../ui/Button";
import { FormErrorBoundary } from "../error";
import Card from "../ui/Card";
import { Save, X } from "lucide-react";
import {
  PhoneInputGroup,
  EmailInputGroup,
  AddressInputGroup,
} from "../contacts";
import { ClientBasicDataSection } from "./ClientFormSections";
import EstablishmentSearchModal from "../search/EstablishmentSearchModal";
import ClientDataCopyModal from "../ui/ClientDataCopyModal";
import { useClientForm } from "../../hooks/useClientForm";
import { ClientDetailed, ClientFormProps } from "../../types";

interface ClientFormProps {
  initialData?: ClientDetailed;
  onSubmit?: (data: any) => Promise<void>;
  onCancel?: () => void;
  onSave?: () => void; // Callback chamado após sucesso
  isLoading?: boolean;
  mode?: "create" | "edit";
  establishmentId?: number;
  establishmentCode?: string;
}

const ClientForm: React.FC<ClientFormProps> = React.memo(
  ({
    initialData,
    onSubmit,
    onCancel,
    onSave,
    isLoading = false,
    mode = "create",
    establishmentId,
    establishmentCode,
  }) => {
    return (
      <FormErrorBoundary formName="ClientForm">
        <ClientFormContent
          initialData={initialData}
          onSubmit={onSubmit}
          onCancel={onCancel}
          onSave={onSave}
          isLoading={isLoading}
          mode={mode}
          establishmentId={establishmentId}
          establishmentCode={establishmentCode}
        />
      </FormErrorBoundary>
    );
  }
);

const ClientFormContent: React.FC<ClientFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  onSave,
  isLoading: parentLoading = false,
  mode = "create",
  establishmentId,
  establishmentCode,
}) => {
  const {
    loading,
    error,
    formData,
    availableEstablishments,
    isEditing,
    setError,
    setFormData,
    updatePerson,
    updateClient,
    handleTaxIdChange,
    handlePhonesChange,
    handlePhoneAdd,
    handlePhoneRemove,
    handleEmailsChange,
    handleEmailAdd,
    handleEmailRemove,
    handleAddressesChange,
    handleAddressAdd,
    handleAddressRemove,
    proceedWithSave,
    save,
  } = useClientForm({
    clientId: initialData?.id,
    onSave,
    establishmentId,
    establishmentCode,
  });

  const isFormLoading = loading || parentLoading;

  // Modal states
  const [showEstablishmentSearchModal, setShowEstablishmentSearchModal] =
    useState(false);
  const [showDataCopyModal, setShowDataCopyModal] = useState(false);
  const [selectedEstablishment, setSelectedEstablishment] = useState(null);

  // Handlers for establishment selection
  const handleEstablishmentSearch = () => {
    setShowEstablishmentSearchModal(true);
  };

  const handleEstablishmentSelect = (establishment) => {
    setSelectedEstablishment(establishment);
    setShowEstablishmentSearchModal(false);
    setShowDataCopyModal(true);
  };

  const handleDataCopyConfirm = (shouldCopy) => {
    if (selectedEstablishment) {
      // Set establishment ID
      setFormData((prev) => ({
        ...prev,
        establishment_id: selectedEstablishment.id,
      }));

      if (shouldCopy && selectedEstablishment.person) {
        // Copy data from establishment to client form
        const establishmentPerson = selectedEstablishment.person;

        // Update person data
        if (establishmentPerson.name) {
          updatePerson("name", establishmentPerson.name);
        }
        if (establishmentPerson.tax_id) {
          // Garantir que tax_id seja limpo (sem formatação) antes de usar
          const cleanTaxId = establishmentPerson.tax_id.replace(/\D/g, "");
          handleTaxIdChange(cleanTaxId);
        }
        if (establishmentPerson.trade_name) {
          updatePerson("trade_name", establishmentPerson.trade_name);
        }
        if (establishmentPerson.description) {
          updatePerson("description", establishmentPerson.description);
        }

        // Copy phones
        if (
          selectedEstablishment.phones &&
          selectedEstablishment.phones.length > 0
        ) {
          selectedEstablishment.phones.forEach((phone, index) => {
            if (index === 0) {
              // Update first phone
              handlePhonesChange([
                {
                  country_code: phone.country_code || "55",
                  area_code: phone.area_code || "",
                  number: phone.number || "",
                  extension: phone.extension || "",
                  type: phone.type || "MOBILE",
                  is_principal: phone.is_principal || false,
                  is_whatsapp: phone.is_whatsapp || false,
                  description: phone.description || "",
                },
              ]);
            } else {
              // Add additional phones
              handlePhoneAdd({
                country_code: phone.country_code || "55",
                area_code: phone.area_code || "",
                number: phone.number || "",
                extension: phone.extension || "",
                type: phone.type || "MOBILE",
                is_principal: phone.is_principal || false,
                is_whatsapp: phone.is_whatsapp || false,
                description: phone.description || "",
              });
            }
          });
        }

        // Copy emails
        if (
          selectedEstablishment.emails &&
          selectedEstablishment.emails.length > 0
        ) {
          selectedEstablishment.emails.forEach((email, index) => {
            if (index === 0) {
              // Update first email
              handleEmailsChange([
                {
                  email_address: email.email_address || "",
                  type: email.type || "PERSONAL",
                  is_principal: email.is_principal || false,
                  is_verified: email.is_verified || false,
                  description: email.description || "",
                },
              ]);
            } else {
              // Add additional emails
              handleEmailAdd({
                email_address: email.email_address || "",
                type: email.type || "PERSONAL",
                is_principal: email.is_principal || false,
                is_verified: email.is_verified || false,
                description: email.description || "",
              });
            }
          });
        }

        // Copy addresses
        if (
          selectedEstablishment.addresses &&
          selectedEstablishment.addresses.length > 0
        ) {
          selectedEstablishment.addresses.forEach((address, index) => {
            if (index === 0) {
              // Update first address
              handleAddressesChange([
                {
                  street: address.street || "",
                  number: address.number || "",
                  complement: address.complement || "",
                  neighborhood: address.neighborhood || "",
                  city: address.city || "",
                  state: address.state || "",
                  zip_code: address.zip_code || "",
                  country: address.country || "BR",
                  type: address.type || "RESIDENTIAL",
                  is_principal: address.is_principal || false,
                  latitude: address.latitude,
                  longitude: address.longitude,
                  ibge_city_code: address.ibge_city_code,
                  gia_code: address.gia_code,
                  siafi_code: address.siafi_code,
                  area_code: address.area_code,
                  description: address.description || "",
                },
              ]);
            } else {
              // Add additional addresses
              handleAddressAdd({
                street: address.street || "",
                number: address.number || "",
                complement: address.complement || "",
                neighborhood: address.neighborhood || "",
                city: address.city || "",
                state: address.state || "",
                zip_code: address.zip_code || "",
                country: address.country || "BR",
                type: address.type || "RESIDENTIAL",
                is_principal: address.is_principal || false,
                latitude: address.latitude,
                longitude: address.longitude,
                ibge_city_code: address.ibge_city_code,
                gia_code: address.gia_code,
                siafi_code: address.siafi_code,
                area_code: address.area_code,
                description: address.description || "",
              });
            }
          });
        }
      }
    }

    setShowDataCopyModal(false);
    setSelectedEstablishment(null);
  };

  const handleDataCopyCancel = () => {
    setShowDataCopyModal(false);
    setSelectedEstablishment(null);
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    try {
      // SEMPRE usar a função save do useClientForm que contém nossa lógica de verificação
      await save();
    } catch (err) {
      console.error("Error saving client:", err);
    }
  };

  const updateFormData = (updates: Partial<typeof formData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
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
              {isEditing ? "Editar Cliente" : "Novo Cliente"}
            </h1>
            <p className="text-muted-foreground" id="form-description">
              {isEditing
                ? "Atualize as informações do cliente"
                : "Cadastre um novo cliente no sistema"}
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
                  ? "Salvando cliente, aguarde..."
                  : isEditing
                  ? "Salvar alterações do cliente"
                  : "Salvar novo cliente"
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

        {/* Dados do Cliente */}
        <ClientBasicDataSection
          formData={formData}
          availableEstablishments={availableEstablishments}
          loading={loading}
          isEditing={isEditing}
          isEstablishmentPreselected={!!establishmentId}
          onUpdateClient={updateClient}
          onUpdatePerson={updatePerson}
          onUpdateFormData={updateFormData}
          onEstablishmentSearch={handleEstablishmentSearch}
          onTaxIdChange={handleTaxIdChange}
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

      {/* Modals */}
      <EstablishmentSearchModal
        isOpen={showEstablishmentSearchModal}
        onClose={() => setShowEstablishmentSearchModal(false)}
        onEstablishmentSelect={handleEstablishmentSelect}
      />

      <ClientDataCopyModal
        isOpen={showDataCopyModal}
        establishment={selectedEstablishment}
        onConfirm={handleDataCopyConfirm}
        onCancel={handleDataCopyCancel}
      />
    </div>
  );
};

export default ClientForm;
