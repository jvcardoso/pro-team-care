import React, { FormEvent } from 'react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { Save, X } from 'lucide-react';
import { PhoneInputGroup, EmailInputGroup, AddressInputGroup } from '../contacts';
import { CompanyBasicDataSection, CompanyReceitaFederalSection, AddressNumberConfirmationModal } from './CompanyFormSections';
import { useCompanyForm } from '../../hooks/useCompanyForm';

interface CompanyFormProps {
  companyId?: number;
  onSave?: () => void;
  onCancel?: () => void;
}

const CompanyForm: React.FC<CompanyFormProps> = ({ companyId, onSave, onCancel }) => {
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
    setPendingAddresses
  } = useCompanyForm({ companyId, onSave });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    
    // Verificar se há endereços sem número
    const addressesWithoutNumber = formData.addresses.filter(address => 
      address.street?.trim() && address.city?.trim() && !address.number?.trim()
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
        <CompanyBasicDataSection
          formData={formData}
          loading={loading}
          isEditing={isEditing}
          onUpdatePeople={updatePeople}
          onCompanyFound={handleCompanyFound}
        />

        {/* Informações da Receita Federal */}
        <CompanyReceitaFederalSection metadata={formData.company.metadata || {}} />

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

export default CompanyForm;