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
  CompanyBasicDataSection,
  CompanyReceitaFederalSection,
  AddressNumberConfirmationModal,
} from "./CompanyFormSections";
import { useCompanyForm } from "../../hooks/useCompanyForm";

interface CompanyFormProps {
  companyId?: number;
  onSave?: () => void;
  onCancel?: () => void;
  onRedirectToDetails?: (companyId: number) => void;
}

const CompanyForm: React.FC<CompanyFormProps> = React.memo(
  ({ companyId, onSave, onCancel, onRedirectToDetails }) => {
    return (
      <FormErrorBoundary formName="CompanyForm">
        <CompanyFormContent
          companyId={companyId}
          onSave={onSave}
          onCancel={onCancel}
          onRedirectToDetails={onRedirectToDetails}
        />
      </FormErrorBoundary>
    );
  }
);

const CompanyFormContent: React.FC<CompanyFormProps> = ({
  companyId,
  onSave,
  onCancel,
  onRedirectToDetails,
}) => {
  const {
    loading,
    error,
    formData,
    showNumberConfirmation,
    isEditing,
    updatePeople,
    handlePhonesChange,
    handlePhoneAdd,
    handlePhoneRemove,
    handleEmailsChange,
    handleEmailAdd,
    handleEmailRemove,
    handleAddressesChange,
    handleAddressAdd,
    handleAddressRemove,
    handleCompanyFound,
    handleNumberConfirmation,
    proceedWithSave,
    setShowNumberConfirmation,
    setPendingAddresses,
  } = useCompanyForm({ companyId, onSave, onRedirectToDetails });

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
              {isEditing ? "Editar Empresa" : "Nova Empresa"}
            </h1>
            <p className="text-muted-foreground" id="form-description">
              {isEditing
                ? "Atualize as informações da empresa"
                : "Cadastre uma nova empresa no sistema"}
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
                  ? "Salvando empresa, aguarde..."
                  : isEditing
                  ? "Salvar alterações da empresa"
                  : "Salvar nova empresa"
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
        {/* Dados da Empresa */}
        <CompanyBasicDataSection
          formData={formData}
          loading={loading}
          isEditing={isEditing}
          onUpdatePeople={updatePeople}
          onCompanyFound={handleCompanyFound}
        />

        {/* Informações da Receita Federal */}
        <CompanyReceitaFederalSection
          metadata={formData.company.metadata || {}}
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

        {/* Convite para Gestor da Empresa */}
        {!isEditing && (
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                Convite para Gestor da Empresa (Opcional)
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Informe o email de um gestor para receber acesso ao sistema. Um
                email de ativação será enviado automaticamente.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Email do Gestor
                  </label>
                  <input
                    type="email"
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
                    placeholder="gestor@empresa.com.br"
                    value={formData.managerEmail || ""}
                    onChange={(e) =>
                      updatePeople({ managerEmail: e.target.value })
                    }
                    disabled={loading}
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    O gestor receberá um email para ativar a conta e definir uma
                    senha.
                  </p>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-blue-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        Como funciona?
                      </h4>
                      <div className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                        <ul className="list-disc list-inside space-y-1">
                          <li>
                            Se informado, um usuário será criado automaticamente
                          </li>
                          <li>
                            Um email de ativação será enviado para o gestor
                          </li>
                          <li>
                            O gestor poderá ativar a conta e definir sua senha
                          </li>
                          <li>
                            Você pode adicionar mais gestores depois na área de
                            usuários
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}
      </form>

      {/* Modal de Confirmação para Número do Endereço */}
      <AddressNumberConfirmationModal
        show={showNumberConfirmation}
        onConfirm={handleNumberConfirmation}
      />
    </div>
  );
};

CompanyForm.displayName = "CompanyForm";

export default CompanyForm;
