import React from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { ClientStatus, PersonType, Gender, MaritalStatus } from "../../types";
import {
  User,
  Building,
  CreditCard,
  Calendar,
  Search,
  Wand2,
} from "lucide-react";
import {
  suggestClientCode,
  validateClientCode,
  isClientCodeDuplicated,
} from "../../utils/clientCodeGenerator";
import {
  detectPersonTypeFromTaxId,
  formatCPF,
  formatCNPJ,
} from "../../utils/validators";
import { clientsService } from "../../services/clientsService";

interface ClientBasicDataSectionProps {
  formData: any;
  availableEstablishments: any[];
  loading: boolean;
  isEditing: boolean;
  isEstablishmentPreselected: boolean;
  onUpdateClient: (field: string, value: any) => void;
  onUpdatePerson: (field: string, value: any) => void;
  onUpdateFormData: (updates: any) => void;
  onEstablishmentSearch: () => void;
  onTaxIdChange: (value: string) => void;
}

export const ClientBasicDataSection: React.FC<ClientBasicDataSectionProps> = ({
  formData,
  availableEstablishments,
  loading,
  isEditing,
  isEstablishmentPreselected,
  onUpdateClient,
  onUpdatePerson,
  onUpdateFormData,
  onEstablishmentSearch,
  onTaxIdChange,
}) => {
  const handleClientChange = (field: string, value: any) => {
    onUpdateClient(field, value);
  };

  const handlePersonChange = (field: string, value: any) => {
    onUpdatePerson(field, value);
  };

  // Encontrar o estabelecimento selecionado
  const selectedEstablishment = availableEstablishments.find(
    (est) => est.id === formData.establishment_id
  );

  // Função para sugerir código automático do cliente
  const handleSuggestClientCode = async () => {
    if (!selectedEstablishment) {
      console.warn("⚠️ Nenhum estabelecimento selecionado para sugerir código");
      return;
    }

    try {
      console.log(
        `🎯 Gerando sugestão de código para estabelecimento ${selectedEstablishment.id}...`
      );

      // Buscar clientes existentes do estabelecimento
      const existingClients = await clientsService.getByEstablishment(
        selectedEstablishment.id
      );
      console.log(
        `📊 Encontrados ${existingClients.length} clientes existentes`
      );

      // Gerar código sugerido único para o estabelecimento
      const suggestedCode = suggestClientCode(
        selectedEstablishment,
        existingClients
      );

      console.log(`✨ Código de cliente sugerido: ${suggestedCode}`);

      // Atualizar campo de código
      handleClientChange("client_code", suggestedCode);
    } catch (error) {
      console.error("❌ Erro ao sugerir código de cliente:", error);
      throw error; // Re-throw para mostrar erro real ao usuário
    }
  };

  return (
    <>
      {/* Informações do Cliente */}
      <Card
        title="Informações do Cliente"
        icon={<Building className="h-5 w-5" />}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Estabelecimento *
            </label>
            <div className="flex gap-2">
              <Input
                value={
                  formData.establishment_id
                    ? availableEstablishments.find(
                        (e) => e.id === formData.establishment_id
                      )?.name +
                      " (" +
                      availableEstablishments.find(
                        (e) => e.id === formData.establishment_id
                      )?.establishment_code +
                      ")"
                    : ""
                }
                onChange={() => {}} // Read-only, só pode ser alterado via busca
                placeholder={
                  isEstablishmentPreselected
                    ? "Estabelecimento selecionado automaticamente"
                    : "Clique em Buscar para selecionar estabelecimento..."
                }
                className="flex-1"
                readOnly
                required={!!formData.establishment_id}
                disabled={loading || isEstablishmentPreselected}
              />
              {!isEstablishmentPreselected && (
                <Button
                  type="button"
                  variant="secondary"
                  outline
                  onClick={onEstablishmentSearch}
                  icon={<Search className="h-4 w-4" />}
                  className="shrink-0"
                  title="Buscar estabelecimento"
                  disabled={loading}
                >
                  <span className="hidden sm:inline">Buscar</span>
                </Button>
              )}
            </div>
            {isEstablishmentPreselected && (
              <p className="text-xs text-muted-foreground mt-1">
                Estabelecimento selecionado automaticamente. O campo não pode
                ser alterado.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Código do Cliente *
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  value={formData.client_code || ""}
                  onChange={(e) =>
                    handleClientChange(
                      "client_code",
                      e.target.value.toUpperCase()
                    )
                  }
                  placeholder="Ex: CLI-057-001, CLI-012-002"
                  required
                  disabled={loading}
                  icon={<CreditCard className="h-4 w-4" />}
                />
              </div>
              <Button
                type="button"
                variant="secondary"
                outline
                onClick={handleSuggestClientCode}
                disabled={loading || !selectedEstablishment}
                icon={<Wand2 className="h-4 w-4" />}
                className="shrink-0"
                title={
                  selectedEstablishment
                    ? `Sugerir código baseado no estabelecimento "${
                        selectedEstablishment.name ||
                        selectedEstablishment.person?.name
                      }"`
                    : "Selecione um estabelecimento primeiro"
                }
              >
                <span className="hidden sm:inline">Sugerir</span>
              </Button>
            </div>
            {selectedEstablishment && (
              <p className="text-xs text-muted-foreground mt-1">
                💡 Formato: CLI-
                {selectedEstablishment.code
                  ? selectedEstablishment.code.match(
                      /EST-(\d{3})-\d{3}/
                    )?.[1] || "000"
                  : "000"}
                -XXX (Ex: CLI-
                {selectedEstablishment.code
                  ? selectedEstablishment.code.match(
                      /EST-(\d{3})-\d{3}/
                    )?.[1] || "000"
                  : "000"}
                -001)
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-2">
              Status
            </label>
            <select
              value={formData.status}
              onChange={(e) =>
                handleClientChange("status", e.target.value as ClientStatus)
              }
              className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
              disabled={loading}
            >
              <option value={ClientStatus.ACTIVE}>Ativo</option>
              <option value={ClientStatus.INACTIVE}>Inativo</option>
              <option value={ClientStatus.ON_HOLD}>Em Espera</option>
              <option value={ClientStatus.ARCHIVED}>Arquivado</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Dados da Pessoa */}
      {formData.person && (
        <Card title="Dados Pessoais" icon={<User className="h-5 w-5" />}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Nome Completo *"
              value={formData.person.name}
              onChange={(e) => handlePersonChange("name", e.target.value)}
              placeholder="Digite o nome completo"
              required
              icon={<User className="h-4 w-4" />}
              disabled={loading}
            />

            <Input
              label="Nome Fantasia / Razão Social"
              value={formData.person.trade_name || ""}
              onChange={(e) => handlePersonChange("trade_name", e.target.value)}
              placeholder="Nome fantasia ou razão social"
              disabled={loading}
            />

            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                CPF/CNPJ *
              </label>
              <Input
                value={(() => {
                  const detection = detectPersonTypeFromTaxId(
                    formData.person.tax_id
                  );
                  return detection.formattedValue || formData.person.tax_id;
                })()}
                onChange={(e) => {
                  const rawValue = e.target.value.replace(/\D/g, ""); // Remove non-digits
                  const detection = detectPersonTypeFromTaxId(rawValue);

                  console.log(`🔍 Digitação detectada:`, {
                    raw: rawValue,
                    type: detection.documentType,
                    personType: detection.personType,
                    valid: detection.isValid,
                    formatted: detection.formattedValue,
                  });

                  // Atualizar tipo de pessoa automaticamente baseado no documento
                  if (
                    detection.personType &&
                    detection.personType !== formData.person.person_type
                  ) {
                    console.log(
                      `🔄 Alterando tipo de pessoa para: ${detection.personType}`
                    );
                    handlePersonChange("person_type", detection.personType);
                  }

                  onTaxIdChange(rawValue);
                }}
                placeholder="Digite CPF (000.000.000-00) ou CNPJ (00.000.000/0000-00)"
                required
                icon={<CreditCard className="h-4 w-4" />}
                disabled={loading || isEditing}
                readOnly={isEditing}
                className={`${
                  formData.person.tax_id &&
                  !detectPersonTypeFromTaxId(formData.person.tax_id).isValid &&
                  formData.person.tax_id.length >= 11
                    ? "border-red-300 focus:border-red-500"
                    : formData.person.tax_id &&
                      detectPersonTypeFromTaxId(formData.person.tax_id).isValid
                    ? "border-green-300 focus:border-green-500"
                    : ""
                } ${isEditing ? "bg-gray-50 cursor-not-allowed" : ""}`}
              />
              {formData.person.tax_id && (
                <div className="mt-1">
                  {isEditing && (
                    <p className="text-xs text-muted-foreground mb-1">
                      🔒 CPF/CNPJ não pode ser alterado após cadastro por
                      questões de segurança
                    </p>
                  )}
                  {(() => {
                    const detection = detectPersonTypeFromTaxId(
                      formData.person.tax_id
                    );
                    if (detection.documentType && detection.isValid) {
                      return (
                        <p className="text-xs text-green-600">
                          ✅ {detection.documentType} válido -{" "}
                          {detection.personType === "PF"
                            ? "Pessoa Física"
                            : "Pessoa Jurídica"}
                        </p>
                      );
                    } else if (
                      detection.documentType &&
                      !detection.isValid &&
                      formData.person.tax_id.length >= 11
                    ) {
                      return (
                        <p className="text-xs text-red-600">
                          ❌ {detection.documentType} inválido - Verifique os
                          dígitos
                        </p>
                      );
                    } else if (formData.person.tax_id.length > 0) {
                      return (
                        <p className="text-xs text-gray-500">
                          ⏳ Continue digitando... (
                          {formData.person.tax_id.length}/14 dígitos)
                        </p>
                      );
                    }
                  })()}
                </div>
              )}
            </div>

            <Input
              label="RG/IE"
              value={formData.person.secondary_tax_id || ""}
              onChange={(e) =>
                handlePersonChange("secondary_tax_id", e.target.value)
              }
              placeholder="RG ou Inscrição Estadual"
              disabled={loading}
            />

            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Tipo de Pessoa
              </label>
              <select
                value={formData.person.person_type}
                onChange={(e) =>
                  handlePersonChange(
                    "person_type",
                    e.target.value as PersonType
                  )
                }
                className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                disabled={
                  loading ||
                  (formData.person.tax_id &&
                    detectPersonTypeFromTaxId(formData.person.tax_id).isValid)
                }
              >
                <option value={PersonType.PF}>Pessoa Física</option>
                <option value={PersonType.PJ}>Pessoa Jurídica</option>
              </select>
              {formData.person.tax_id &&
                detectPersonTypeFromTaxId(formData.person.tax_id).isValid && (
                  <p className="text-xs text-muted-foreground mt-1">
                    🔒 Tipo definido automaticamente pelo documento
                  </p>
                )}
            </div>

            {formData.person.person_type === PersonType.PF && (
              <>
                <Input
                  label="Data de Nascimento"
                  type="date"
                  value={formData.person.birth_date || ""}
                  onChange={(e) =>
                    handlePersonChange("birth_date", e.target.value)
                  }
                  icon={<Calendar className="h-4 w-4" />}
                  disabled={loading}
                />

                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Gênero
                  </label>
                  <select
                    value={formData.person.gender || Gender.NOT_INFORMED}
                    onChange={(e) =>
                      handlePersonChange("gender", e.target.value as Gender)
                    }
                    className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                    disabled={loading}
                  >
                    <option value={Gender.NOT_INFORMED}>Não informado</option>
                    <option value={Gender.MALE}>Masculino</option>
                    <option value={Gender.FEMALE}>Feminino</option>
                    <option value={Gender.NON_BINARY}>Não binário</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Estado Civil
                  </label>
                  <select
                    value={
                      formData.person.marital_status ||
                      MaritalStatus.NOT_INFORMED
                    }
                    onChange={(e) =>
                      handlePersonChange(
                        "marital_status",
                        e.target.value as MaritalStatus
                      )
                    }
                    className="w-full px-3 py-2 border border-border rounded-md bg-input text-foreground focus:ring-2 focus:ring-ring focus:outline-none"
                    disabled={loading}
                  >
                    <option value={MaritalStatus.NOT_INFORMED}>
                      Não informado
                    </option>
                    <option value={MaritalStatus.SINGLE}>Solteiro(a)</option>
                    <option value={MaritalStatus.MARRIED}>Casado(a)</option>
                    <option value={MaritalStatus.DIVORCED}>
                      Divorciado(a)
                    </option>
                    <option value={MaritalStatus.WIDOWED}>Viúvo(a)</option>
                    <option value={MaritalStatus.STABLE_UNION}>
                      União estável
                    </option>
                  </select>
                </div>

                <Input
                  label="Profissão"
                  value={formData.person.occupation || ""}
                  onChange={(e) =>
                    handlePersonChange("occupation", e.target.value)
                  }
                  placeholder="Profissão ou ocupação"
                  disabled={loading}
                />
              </>
            )}

            {formData.person.person_type === PersonType.PJ && (
              <>
                <Input
                  label="Data de Constituição"
                  type="date"
                  value={formData.person.incorporation_date || ""}
                  onChange={(e) =>
                    handlePersonChange("incorporation_date", e.target.value)
                  }
                  icon={<Calendar className="h-4 w-4" />}
                  disabled={loading}
                />

                <Input
                  label="Regime Tributário"
                  value={formData.person.tax_regime || ""}
                  onChange={(e) =>
                    handlePersonChange("tax_regime", e.target.value)
                  }
                  placeholder="Ex: Simples Nacional, Lucro Presumido"
                  disabled={loading}
                />

                <Input
                  label="Natureza Jurídica"
                  value={formData.person.legal_nature || ""}
                  onChange={(e) =>
                    handlePersonChange("legal_nature", e.target.value)
                  }
                  placeholder="Ex: LTDA, SA, EIRELI"
                  disabled={loading}
                />

                <Input
                  label="Inscrição Municipal"
                  value={formData.person.municipal_registration || ""}
                  onChange={(e) =>
                    handlePersonChange("municipal_registration", e.target.value)
                  }
                  placeholder="Número da inscrição municipal"
                  disabled={loading}
                />

                <Input
                  label="Website"
                  value={formData.person.website || ""}
                  onChange={(e) =>
                    handlePersonChange("website", e.target.value)
                  }
                  placeholder="https://exemplo.com.br"
                  disabled={loading}
                />
              </>
            )}

            <div className="md:col-span-2">
              <Input
                label="Observações"
                value={formData.person.description || ""}
                onChange={(e) =>
                  handlePersonChange("description", e.target.value)
                }
                placeholder="Observações sobre o cliente"
                disabled={loading}
              />
            </div>
          </div>
        </Card>
      )}
    </>
  );
};

export default ClientBasicDataSection;
