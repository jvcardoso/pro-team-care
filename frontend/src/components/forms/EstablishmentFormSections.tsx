import React, { useState } from "react";
import Card from "../ui/Card";
import Input from "../ui/Input";
import Button from "../ui/Button";
import CompanySearchInput from "../search/CompanySearchInput";
import CompanyDataCopyModal from "../ui/CompanyDataCopyModal";
import { mapCompanyDataToEstablishment } from "../../utils/companyDataMapper";
import { formatTaxId } from "../../utils/formatters";
import { establishmentsService } from "../../services/api";
import {
  suggestEstablishmentCode,
  validateEstablishmentCode,
} from "../../utils/establishmentCodeGenerator";
import { Building, User, Check, X, Wand2 } from "lucide-react";

interface Company {
  id: number;
  person_name?: string;
  person?: { name: string };
}

interface EstablishmentFormData {
  person: {
    name: string;
    tax_id: string;
    person_type: string;
    status: string;
    description: string;
  };
  establishment: {
    company_id: number;
    code: string;
    type: string;
    category: string;
    is_active: boolean;
    is_principal: boolean;
    display_order: number;
    settings: Record<string, any>;
    operating_hours: Record<string, any>;
    service_areas: Record<string, any>;
  };
}

interface EstablishmentBasicDataSectionProps {
  formData: EstablishmentFormData & {
    addresses: any[];
    phones: any[];
    emails: any[];
  };
  companies: Company[];
  loading: boolean;
  isEditing: boolean;
  isCompanyPreselected?: boolean;
  onUpdatePerson: (field: string, value: any) => void;
  onUpdateEstablishment: (field: string, value: any) => void;
  onUpdateFormData?: (newFormData: any) => void;
  onUpdatePhones?: (phones: any[]) => void;
  onUpdateEmails?: (emails: any[]) => void;
  onUpdateAddresses?: (addresses: any[]) => void;
}

export const EstablishmentBasicDataSection: React.FC<
  EstablishmentBasicDataSectionProps
> = ({
  formData,
  companies,
  loading,
  isEditing,
  isCompanyPreselected = false,
  onUpdatePerson,
  onUpdateEstablishment,
  onUpdateFormData,
  onUpdatePhones,
  onUpdateEmails,
  onUpdateAddresses,
}) => {
  // Estado para controlar o modal de cópia de dados
  const [showDataCopyModal, setShowDataCopyModal] = useState(false);
  const [pendingCompanyForCopy, setPendingCompanyForCopy] =
    useState<Company | null>(null);

  // Encontrar a empresa selecionada para exibir no componente
  const selectedCompany = companies.find(
    (company) => company.id === formData.establishment.company_id
  );

  // Função para verificar se a empresa já tem estabelecimento principal
  const checkCompanyHasPrincipalEstablishment = async (
    companyId: number
  ): Promise<boolean> => {
    try {
      console.log(
        `🔍 Verificando se empresa ${companyId} já tem estabelecimento principal...`
      );

      const response = await establishmentsService.getEstablishmentsByCompany(
        companyId
      );
      const establishments = response?.establishments || response || [];

      // Verificar se algum estabelecimento é principal
      const hasPrincipal = establishments.some(
        (est: any) => est.is_principal === true
      );

      console.log(
        `✅ Empresa ${companyId} ${
          hasPrincipal ? "JÁ TEM" : "NÃO TEM"
        } estabelecimento principal`
      );
      return hasPrincipal;
    } catch (error) {
      console.warn(
        `⚠️ Erro ao verificar estabelecimento principal da empresa ${companyId}:`,
        error
      );
      // Em caso de erro, assumir que não tem principal para permitir criação
      return false;
    }
  };

  // Função para sugerir código automático
  const handleSuggestCode = async () => {
    if (!selectedCompany) {
      console.warn("⚠️ Nenhuma empresa selecionada para sugerir código");
      return;
    }

    try {
      console.log(
        `🎯 Gerando sugestão de código para empresa ${selectedCompany.id}...`
      );

      // Buscar estabelecimentos existentes da empresa
      const response = await establishmentsService.getEstablishmentsByCompany(
        selectedCompany.id
      );
      const existingEstablishments = response?.establishments || response || [];

      // Gerar código sugerido
      const suggestedCode = suggestEstablishmentCode(
        selectedCompany,
        existingEstablishments
      );

      console.log(`✨ Código sugerido: ${suggestedCode}`);

      // Atualizar campo de código
      onUpdateEstablishment("code", suggestedCode);
    } catch (error) {
      console.error("❌ Erro ao sugerir código:", error);

      // Fallback: gerar código simples baseado apenas na empresa
      const fallbackCode = suggestEstablishmentCode(selectedCompany, []);
      onUpdateEstablishment("code", fallbackCode);

      console.log(`🔄 Usando código fallback: ${fallbackCode}`);
    }
  };

  // Função para mostrar modal de confirmação de cópia
  const handleCompanyDataCopyRequest = (company: any) => {
    setPendingCompanyForCopy(company);
    setShowDataCopyModal(true);
  };

  // Função para executar cópia de dados da empresa para o formulário
  const handleCompanyDataCopy = (company: any) => {
    try {
      console.log("🔄 Iniciando cópia de dados da empresa:", company);
      console.log("📊 Empresa tem endereços:", company.addresses?.length || 0);

      const mappedData = mapCompanyDataToEstablishment(company, {
        person: formData.person,
        establishment: formData.establishment,
        phones: formData.phones,
        emails: formData.emails,
        addresses: formData.addresses,
      });

      console.log("📋 Dados mapeados:", {
        phones: mappedData.phones?.length || 0,
        emails: mappedData.emails?.length || 0,
        addresses: mappedData.addresses?.length || 0,
      });

      // Se temos uma função para atualizar todo o formData, usamos ela
      if (onUpdateFormData) {
        console.log("✅ Usando onUpdateFormData para atualizar tudo");
        onUpdateFormData(mappedData);
        return;
      }

      // Caso contrário, atualizamos campo por campo
      Object.keys(mappedData.person).forEach((key) => {
        onUpdatePerson(key, mappedData.person[key]);
      });

      Object.keys(mappedData.establishment).forEach((key) => {
        onUpdateEstablishment(key, mappedData.establishment[key]);
      });

      // Atualizar arrays usando as funções específicas
      if (mappedData.phones && mappedData.phones.length > 0 && onUpdatePhones) {
        console.log("📞 Atualizando telefones:", mappedData.phones.length);
        onUpdatePhones(mappedData.phones);
      }

      if (mappedData.emails && mappedData.emails.length > 0 && onUpdateEmails) {
        console.log("📧 Atualizando emails:", mappedData.emails.length);
        onUpdateEmails(mappedData.emails);
      }

      if (
        mappedData.addresses &&
        mappedData.addresses.length > 0 &&
        onUpdateAddresses
      ) {
        console.log(
          "🏠 Atualizando endereços:",
          mappedData.addresses.length,
          mappedData.addresses
        );
        onUpdateAddresses(mappedData.addresses);
      } else {
        console.log(
          "❌ Nenhum endereço para atualizar ou onUpdateAddresses não disponível"
        );
      }
    } catch (error) {
      console.error("Erro ao copiar dados da empresa:", error);
    }
  };

  const typeOptions = [
    { value: "matriz", label: "Matriz" },
    { value: "filial", label: "Filial" },
    { value: "unidade", label: "Unidade" },
    { value: "posto", label: "Posto" },
  ];

  const categoryOptions = [
    { value: "clinica", label: "Clínica" },
    { value: "hospital", label: "Hospital" },
    { value: "laboratorio", label: "Laboratório" },
    { value: "farmacia", label: "Farmácia" },
    { value: "consultorio", label: "Consultório" },
    { value: "upa", label: "UPA" },
    { value: "ubs", label: "UBS" },
    { value: "outro", label: "Outro" },
  ];

  return (
    <>
      <Card
        title="Dados do Estabelecimento"
        icon={<Building className="h-5 w-5" />}
      >
        <div className="space-y-6">
          {/* Dados Básicos */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isEditing || isCompanyPreselected ? (
              // Modo edição ou empresa pré-selecionada: mostrar empresa como read-only
              <div>
                <label className="block text-sm font-medium text-muted-foreground mb-2">
                  Empresa *
                </label>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Input
                      value={
                        selectedCompany?.people?.name ||
                        selectedCompany?.person?.name ||
                        selectedCompany?.name ||
                        selectedCompany?.person_name ||
                        `Empresa ID ${formData.establishment.company_id}` ||
                        "Carregando empresa..."
                      }
                      disabled={true}
                      readOnly={true}
                      placeholder="Empresa vinculada"
                      icon={<Building className="h-4 w-4" />}
                    />
                  </div>
                  {isCompanyPreselected && selectedCompany && (
                    <Button
                      type="button"
                      variant="secondary"
                      outline
                      onClick={() =>
                        handleCompanyDataCopyRequest(selectedCompany)
                      }
                      disabled={loading}
                      icon={<Wand2 className="h-4 w-4" />}
                      className="shrink-0"
                      title="Copiar dados da empresa para o estabelecimento"
                    >
                      <span className="hidden sm:inline">Copiar Dados</span>
                      <span className="sm:hidden">Copiar</span>
                    </Button>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {isEditing
                    ? "A empresa não pode ser alterada após a criação do estabelecimento"
                    : isCompanyPreselected
                    ? "Empresa selecionada automaticamente. Use 'Copiar Dados' para preencher o formulário."
                    : "Empresa selecionada automaticamente"}
                </p>
              </div>
            ) : (
              // Modo criação: permitir seleção de empresa
              <CompanySearchInput
                value=""
                selectedCompany={selectedCompany}
                onChange={() => {}} // Não usado pois o valor vem da seleção
                onCompanySelect={async (company) => {
                  // Definir a empresa
                  onUpdateEstablishment("company_id", company.id);

                  // Verificar se a empresa já tem estabelecimento principal
                  const hasPrincipal =
                    await checkCompanyHasPrincipalEstablishment(company.id);

                  // Ajustar automaticamente o checkbox "is_principal"
                  // Se NÃO tem principal -> marcar como principal
                  // Se JÁ tem principal -> desmarcar
                  onUpdateEstablishment("is_principal", !hasPrincipal);

                  console.log(
                    `🎯 Checkbox "Estabelecimento principal" ${
                      !hasPrincipal ? "MARCADO" : "DESMARCADO"
                    } automaticamente`
                  );

                  // Sugerir código automaticamente se o campo estiver vazio
                  if (
                    !formData.establishment.code ||
                    formData.establishment.code.trim() === ""
                  ) {
                    try {
                      const response =
                        await establishmentsService.getEstablishmentsByCompany(
                          company.id
                        );
                      const existingEstablishments =
                        response?.establishments || response || [];
                      const suggestedCode = suggestEstablishmentCode(
                        company,
                        existingEstablishments
                      );

                      onUpdateEstablishment("code", suggestedCode);
                      console.log(
                        `✨ Código sugerido automaticamente: ${suggestedCode}`
                      );
                    } catch (error) {
                      console.warn(
                        "⚠️ Erro ao sugerir código automaticamente:",
                        error
                      );
                    }
                  }
                }}
                placeholder="Selecione uma empresa"
                disabled={loading}
                required={true}
                enableDataCopy={true}
                onDataCopyConfirm={handleCompanyDataCopy}
              />
            )}

            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Código do Estabelecimento *
              </label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <Input
                    value={formData.establishment.code}
                    onChange={(e) =>
                      onUpdateEstablishment(
                        "code",
                        e.target.value.toUpperCase()
                      )
                    }
                    placeholder="Ex: EST-057-001, EST-012-002"
                    required
                    disabled={loading}
                    icon={<Building className="h-4 w-4" />}
                  />
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  outline
                  onClick={handleSuggestCode}
                  disabled={loading || !selectedCompany}
                  icon={<Wand2 className="h-4 w-4" />}
                  className="shrink-0"
                  title={
                    selectedCompany
                      ? `Sugerir código baseado em "${
                          selectedCompany.name || selectedCompany.people?.name
                        }"`
                      : "Selecione uma empresa primeiro"
                  }
                >
                  <span className="hidden sm:inline">Sugerir</span>
                </Button>
              </div>
              {selectedCompany && (
                <p className="text-xs text-muted-foreground mt-1">
                  💡 Formato: EST-
                  {String(selectedCompany.id || 0).padStart(3, "0")}-XXX (Ex:
                  EST-{String(selectedCompany.id || 0).padStart(3, "0")}-001)
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Tipo *
              </label>
              <select
                value={formData.establishment.type}
                onChange={(e) => onUpdateEstablishment("type", e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                required
                disabled={loading}
              >
                {typeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Categoria *
              </label>
              <select
                value={formData.establishment.category}
                onChange={(e) =>
                  onUpdateEstablishment("category", e.target.value)
                }
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                required
                disabled={loading}
              >
                {categoryOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Dados da Pessoa Jurídica */}
          <div>
            <h3 className="text-lg font-medium text-foreground mb-4 flex items-center gap-2">
              <User className="h-5 w-5" />
              Dados da Pessoa Jurídica
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Nome do Estabelecimento *"
                value={formData.person.name}
                onChange={(e) => onUpdatePerson("name", e.target.value)}
                placeholder="Nome completo do estabelecimento"
                required
                disabled={loading}
                icon={<Building className="h-4 w-4" />}
              />

              <Input
                label="CNPJ *"
                value={formatTaxId(formData.person.tax_id)}
                onChange={(e) =>
                  onUpdatePerson("tax_id", e.target.value.replace(/\D/g, ""))
                }
                placeholder="00.000.000/0000-00"
                required
                disabled={loading || isEditing}
                readOnly={isEditing}
                icon={<User className="h-4 w-4" />}
                maxLength={18}
                helper={
                  isEditing
                    ? "O CNPJ não pode ser alterado após a criação do estabelecimento"
                    : undefined
                }
              />
            </div>

            <div className="mt-4">
              <Input
                label="Observações"
                value={formData.person.description || ""}
                onChange={(e) => onUpdatePerson("description", e.target.value)}
                placeholder="Informações adicionais sobre o estabelecimento (opcional)"
                disabled={loading}
                multiline
                rows={3}
              />
            </div>
          </div>

          {/* Configurações */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-border">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.establishment.is_active}
                onChange={(e) =>
                  onUpdateEstablishment("is_active", e.target.checked)
                }
                className="w-4 h-4 text-primary bg-input border-border rounded focus:ring-ring focus:ring-2"
                disabled={loading}
              />
              <label
                htmlFor="is_active"
                className="text-sm font-medium text-foreground"
              >
                Estabelecimento ativo
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_principal"
                checked={formData.establishment.is_principal}
                onChange={(e) =>
                  onUpdateEstablishment("is_principal", e.target.checked)
                }
                className="w-4 h-4 text-primary bg-input border-border rounded focus:ring-ring focus:ring-2"
                disabled={loading}
              />
              <label
                htmlFor="is_principal"
                className="text-sm font-medium text-foreground"
              >
                Estabelecimento principal da empresa
              </label>
            </div>
          </div>
        </div>
      </Card>

      {/* Modal de confirmação de cópia de dados */}
      {showDataCopyModal && pendingCompanyForCopy && (
        <CompanyDataCopyModal
          isOpen={showDataCopyModal}
          company={pendingCompanyForCopy}
          onConfirm={(shouldCopy) => {
            if (shouldCopy) {
              handleCompanyDataCopy(pendingCompanyForCopy);
            }
            setShowDataCopyModal(false);
            setPendingCompanyForCopy(null);
          }}
          onCancel={() => {
            setShowDataCopyModal(false);
            setPendingCompanyForCopy(null);
          }}
        />
      )}
    </>
  );
};

interface AddressNumberConfirmationModalProps {
  show: boolean;
  onConfirm: (confirmed: boolean) => void;
}

export const AddressNumberConfirmationModal: React.FC<
  AddressNumberConfirmationModalProps
> = ({ show, onConfirm }) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-medium text-foreground mb-4">
          Endereço sem número
        </h3>
        <p className="text-muted-foreground mb-6">
          Alguns endereços não possuem número informado. Deseja continuar
          salvando os endereços como "S/N" (Sem Número)?
        </p>
        <div className="flex gap-3 justify-end">
          <Button
            variant="secondary"
            outline
            onClick={() => onConfirm(false)}
            icon={<X className="h-4 w-4" />}
          >
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={() => onConfirm(true)}
            icon={<Check className="h-4 w-4" />}
          >
            Continuar
          </Button>
        </div>
      </div>
    </div>
  );
};
