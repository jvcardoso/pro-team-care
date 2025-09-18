import { useState, useCallback, useEffect } from "react";
import { establishmentsService, companiesService } from "../services/api";
import { validateEmail } from "../utils/validators";
import { notify } from "../utils/notifications";
import addressEnrichmentService from "../services/addressEnrichmentService";
import {
  Phone,
  Email,
  Address,
  PersonType,
  PhoneType,
  EmailType,
  AddressType,
} from "../types";

interface EstablishmentFormData {
  person: {
    name: string;
    tax_id: string;
    person_type: PersonType;
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
    metadata: Record<string, any>;
    operating_hours: Record<string, any>;
    service_areas: Record<string, any>;
  };
  phones: Array<
    Partial<Phone> & {
      country_code: string;
      number: string;
      type: PhoneType;
      is_principal: boolean;
      is_whatsapp: boolean;
    }
  >;
  emails: Array<
    Partial<Email> & {
      email_address: string;
      type: EmailType;
      is_principal: boolean;
    }
  >;
  addresses: Array<
    Partial<Address> & {
      street: string;
      number: string;
      city: string;
      type: AddressType;
      is_principal: boolean;
    }
  >;
}

interface Company {
  id: number;
  person_name?: string;
  person?: { name: string };
}

interface UseEstablishmentFormProps {
  establishmentId?: number;
  companyId?: number;
  onSave?: () => void;
}

export const useEstablishmentForm = ({
  establishmentId,
  companyId,
  onSave,
}: UseEstablishmentFormProps) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [formData, setFormData] = useState<EstablishmentFormData>({
    person: {
      name: "",
      tax_id: "",
      person_type: PersonType.PJ,
      status: "active",
      description: "",
    },
    establishment: {
      company_id: companyId || 0,
      code: "",
      type: "filial",
      category: "clinica",
      is_active: true,
      is_principal: false,
      display_order: 0,
      settings: {},
      metadata: {},
      operating_hours: {},
      service_areas: {},
    },
    phones: [
      {
        country_code: "55",
        number: "",
        type: PhoneType.COMMERCIAL,
        is_principal: true,
        is_whatsapp: false,
      },
    ],
    emails: [
      {
        email_address: "",
        type: EmailType.WORK,
        is_principal: true,
      },
    ],
    addresses: [
      {
        street: "",
        number: "",
        details: "",
        neighborhood: "",
        city: "",
        state: "",
        zip_code: "",
        country: "Brasil",
        type: AddressType.COMMERCIAL,
        is_principal: true,
      },
    ],
  });

  const [showNumberConfirmation, setShowNumberConfirmation] =
    useState<boolean>(false);
  const [pendingAddresses, setPendingAddresses] =
    useState<EstablishmentFormData | null>(null);

  const isEditing = Boolean(establishmentId);

  // Carregar empresas
  const loadCompanies = useCallback(async (): Promise<void> => {
    try {
      const response = await companiesService.getCompanies({
        is_active: true,
        page: 1,
        size: 100,
      });
      const companiesData = response?.companies || response?.data || [];
      setCompanies(companiesData);
    } catch (err) {
      console.error("Error loading companies:", err);
      setError("Erro ao carregar empresas");
    }
  }, []);

  // Carregar estabelecimento para edição
  const loadEstablishment = useCallback(async (): Promise<void> => {
    if (!establishmentId) return;

    try {
      setLoading(true);
      const establishment = await establishmentsService.getEstablishment(
        establishmentId
      );

      setFormData({
        person: {
          name: establishment.person?.name || "",
          tax_id: establishment.person?.tax_id || "",
          person_type: PersonType.PJ,
          status: establishment.person?.status || "active",
          description: establishment.person?.description || "",
        },
        establishment: {
          company_id: establishment.company_id || 0,
          code: establishment.code || "",
          type: establishment.type || "filial",
          category: establishment.category || "clinica",
          is_active: establishment.is_active ?? true,
          is_principal: establishment.is_principal || false,
          display_order: establishment.display_order || 0,
          settings: establishment.settings || {},
          metadata: establishment.metadata || {},
          operating_hours: establishment.operating_hours || {},
          service_areas: establishment.service_areas || {},
        },
        phones:
          establishment.phones && establishment.phones.length > 0
            ? establishment.phones
            : [
                {
                  country_code: "55",
                  number: "",
                  type: PhoneType.COMMERCIAL,
                  is_principal: true,
                  is_whatsapp: false,
                },
              ],
        emails:
          establishment.emails && establishment.emails.length > 0
            ? establishment.emails
            : [
                {
                  email_address: "",
                  type: EmailType.WORK,
                  is_principal: true,
                },
              ],
        addresses:
          establishment.addresses && establishment.addresses.length > 0
            ? establishment.addresses
            : [
                {
                  street: "",
                  number: "",
                  details: "",
                  neighborhood: "",
                  city: "",
                  state: "",
                  zip_code: "",
                  country: "Brasil",
                  type: AddressType.COMMERCIAL,
                  is_principal: true,
                },
              ],
      });
    } catch (err) {
      setError("Erro ao carregar estabelecimento");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [establishmentId]);

  // Carregar empresa específica quando companyId é fornecido
  const loadSelectedCompany = useCallback(
    async (companyId: number): Promise<void> => {
      try {
        console.log(
          `🔍 Carregando dados da empresa ${companyId} para pré-seleção...`
        );
        const company = await companiesService.getCompany(companyId);

        // Adicionar empresa à lista se não estiver lá
        setCompanies((prev) => {
          const exists = prev.some((c) => c.id === companyId);
          if (!exists) {
            return [...prev, company];
          }
          return prev;
        });

        console.log(
          `✅ Empresa ${companyId} carregada e pré-selecionada:`,
          company.name || company.people?.name || `Empresa ${company.id}`
        );
      } catch (err) {
        console.error(`❌ Erro ao carregar empresa ${companyId}:`, err);
        // Não bloquear o formulário se não conseguir carregar a empresa
      }
    },
    []
  );

  useEffect(() => {
    loadCompanies();
    if (establishmentId) {
      loadEstablishment();
    } else if (companyId && !establishmentId) {
      // Se é criação E tem companyId, carregar empresa específica
      loadSelectedCompany(companyId);
    }
  }, [
    establishmentId,
    companyId,
    loadCompanies,
    loadEstablishment,
    loadSelectedCompany,
  ]);

  const updatePerson = (field: string, value: any): void => {
    setFormData((prev) => ({
      ...prev,
      person: { ...prev.person, [field]: value },
    }));
  };

  const updateEstablishment = (field: string, value: any): void => {
    setFormData((prev) => ({
      ...prev,
      establishment: { ...prev.establishment, [field]: value },
    }));
  };

  const updateFormData = (newFormData: EstablishmentFormData): void => {
    console.log("🔄 updateFormData chamado com:", {
      phones: newFormData.phones?.length || 0,
      emails: newFormData.emails?.length || 0,
      addresses: newFormData.addresses?.length || 0,
      addressesData: newFormData.addresses,
    });
    setFormData(newFormData);
  };

  const handlePhonesChange = (phones: Phone[]): void => {
    setFormData((prev) => ({ ...prev, phones }));
  };

  const handlePhoneAdd = (newPhone: Phone): void => {
    setFormData((prev) => ({
      ...prev,
      phones: [...prev.phones, newPhone],
    }));
  };

  const handlePhoneRemove = (index: number): void => {
    setFormData((prev) => ({
      ...prev,
      phones: prev.phones.filter((_, i) => i !== index),
    }));
  };

  const handleEmailsChange = (emails: Email[]): void => {
    setFormData((prev) => ({ ...prev, emails }));
  };

  const handleEmailAdd = (newEmail: Email): void => {
    setFormData((prev) => ({
      ...prev,
      emails: [...prev.emails, newEmail],
    }));
  };

  const handleEmailRemove = (index: number): void => {
    setFormData((prev) => ({
      ...prev,
      emails: prev.emails.filter((_, i) => i !== index),
    }));
  };

  const handleAddressesChange = (addresses: Address[]): void => {
    setFormData((prev) => ({ ...prev, addresses }));
  };

  const handleAddressAdd = (newAddress: Address): void => {
    setFormData((prev) => ({
      ...prev,
      addresses: [...prev.addresses, newAddress],
    }));
  };

  const handleAddressRemove = (index: number): void => {
    setFormData((prev) => ({
      ...prev,
      addresses: prev.addresses.filter((_, i) => i !== index),
    }));
  };

  const handleNumberConfirmation = async (
    confirmed: boolean
  ): Promise<void> => {
    setShowNumberConfirmation(false);

    if (confirmed && pendingAddresses) {
      // Usuário confirmou salvar sem número - definir S/N para endereços sem número
      const updatedAddresses = pendingAddresses.addresses.map((address) => ({
        ...address,
        number: address.number?.trim() || "S/N",
      }));

      const dataWithDefaultNumbers = {
        ...pendingAddresses,
        addresses: updatedAddresses,
      };

      // Continuar com o salvamento
      await proceedWithSave(dataWithDefaultNumbers);
    }

    setPendingAddresses(null);
  };

  const saveWithExistingPerson = async (
    dataToSave: EstablishmentFormData,
    existingCompany: any
  ): Promise<void> => {
    try {
      console.log(
        `💾 Salvando establishment com pessoa existente (person_id: ${existingCompany.person_id})`
      );

      // Preparar dados para reutilizar pessoa existente
      const cleanedData = {
        company_id: dataToSave.establishment.company_id,
        code: dataToSave.establishment.code.trim().toUpperCase(),
        type: dataToSave.establishment.type,
        category: dataToSave.establishment.category,
        is_active: dataToSave.establishment.is_active,
        is_principal: dataToSave.establishment.is_principal,
        settings: dataToSave.establishment.settings || {},
        metadata: dataToSave.establishment.metadata || {},
        operating_hours: dataToSave.establishment.operating_hours || {},
        service_areas: dataToSave.establishment.service_areas || {},
        // 🔑 Campo especial para indicar reutilização de pessoa existente
        existing_person_id: existingCompany.person_id,
      };

      console.log(
        "🚀 Dados para salvamento com pessoa existente:",
        JSON.stringify(cleanedData, null, 2)
      );

      // Salvar usando endpoint especial ou flag
      if (isEditing) {
        await establishmentsService.updateEstablishment(
          establishmentId!,
          cleanedData
        );
        notify.success("Estabelecimento atualizado com sucesso!");
      } else {
        await establishmentsService.createEstablishment(cleanedData);
        notify.success(
          "Estabelecimento criado com sucesso usando dados existentes!"
        );
      }

      // Enriquecer endereços automaticamente após salvamento bem-sucedido
      await enrichAddressesAfterSave(dataToSave);

      // Chamar callback de sucesso
      if (onSave) {
        onSave();
      }
    } catch (err: any) {
      console.error("Erro ao salvar com pessoa existente:", err);

      let errorMessage = "Erro ao salvar estabelecimento";
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
      notify.error(errorMessage);
    }
  };

  const enrichAddressesAfterSave = async (
    dataToSave: EstablishmentFormData
  ): Promise<void> => {
    // Enriquecer endereços automaticamente se existirem
    if (dataToSave.addresses && dataToSave.addresses.length > 0) {
      console.log("🔄 Iniciando enriquecimento automático de endereços...");

      try {
        // Enriquecer endereços com ViaCEP + geocoding
        const enrichedAddresses =
          await addressEnrichmentService.enriquecerMultiplosEnderecos(
            dataToSave.addresses
          );

        console.log("✅ Endereços enriquecidos:", enrichedAddresses);

        // Atualizar formulário com endereços enriquecidos
        setFormData((prevData) => ({
          ...prevData,
          addresses: enrichedAddresses,
        }));

        // Verificar se algum endereço foi enriquecido
        const hasEnrichedData = enrichedAddresses.some(
          (addr: any) => addr.latitude && addr.longitude && addr.ibge_city_code
        );

        const hasViaCepData = enrichedAddresses.some(
          (addr: any) => addr.ibge_city_code || addr.gia_code || addr.siafi_code
        );

        if (hasEnrichedData) {
          notify.success(
            "Endereços enriquecidos com coordenadas GPS e dados oficiais!"
          );
        } else if (hasViaCepData) {
          notify.success(
            "Endereços enriquecidos com dados oficiais do ViaCEP!"
          );
        } else {
          console.warn("Endereços não foram enriquecidos completamente");
          notify.info(
            "Dados básicos salvos, mas houve problemas no enriquecimento de endereços."
          );
        }
      } catch (error) {
        console.error("Erro no enriquecimento automático de endereços:", error);
        notify.info(
          "Estabelecimento salvo, mas o enriquecimento de endereços falhou."
        );
      }
    }
  };

  const proceedWithSave = async (
    dataToSave: EstablishmentFormData
  ): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Validações básicas
      if (!dataToSave.establishment.company_id) {
        setError("Empresa é obrigatória");
        return;
      }

      if (!dataToSave.establishment.code.trim()) {
        setError("Código do estabelecimento é obrigatório");
        return;
      }

      if (!dataToSave.person.name.trim()) {
        setError("Nome do estabelecimento é obrigatório");
        return;
      }

      if (!dataToSave.person.tax_id.trim()) {
        setError("CNPJ é obrigatório");
        return;
      }

      // Validação de CNPJ
      const cnpj = dataToSave.person.tax_id.replace(/\D/g, "");
      if (cnpj.length !== 14) {
        setError("CNPJ deve ter 14 dígitos");
        return;
      }

      // Verificar se há sequência de números iguais
      if (/^(\d)\1+$/.test(cnpj)) {
        setError("CNPJ inválido");
        return;
      }

      // 🔍 Verificar CNPJ duplicado apenas no modo criação
      if (!isEditing) {
        try {
          console.log(`🔍 Verificando se CNPJ ${cnpj} já existe...`);
          const existingCompany = await companiesService.getCompanyByCNPJ(cnpj);

          if (existingCompany) {
            console.log(
              `⚠️ CNPJ encontrado na empresa: ${
                existingCompany.people?.name || existingCompany.name
              }`
            );

            // Se companyId está definido (vem da página da empresa), automaticamente reutilizar dados
            if (companyId) {
              console.log(
                `🎯 Estabelecimento criado via empresa (companyId: ${companyId}). Reutilizando dados automaticamente.`
              );
              await saveWithExistingPerson(dataToSave, existingCompany);
              return;
            }

            // Caso contrário, mostrar modal de confirmação (fluxo normal)
            notify.confirm(
              "CNPJ já cadastrado",
              `O CNPJ ${
                dataToSave.person.tax_id
              } já está relacionado à empresa "${
                existingCompany.people?.name || existingCompany.name
              }".\n\nDeseja reutilizar os mesmos dados dessa empresa para criar o estabelecimento?`,
              async () => {
                // Confirmar - usar dados existentes
                console.log(
                  `✅ Usuário confirmou reutilização da pessoa existente`
                );
                await saveWithExistingPerson(dataToSave, existingCompany);
              },
              () => {
                // Cancelar - não criar estabelecimento
                console.log(`❌ Usuário cancelou. Precisa informar outro CNPJ`);
                setError(
                  "Por favor, informe um CNPJ diferente ou confirme o uso do CNPJ existente."
                );
              }
            );
            return;
          }
        } catch (cnpjCheckError: any) {
          // Se der erro 404 (CNPJ não encontrado), continuar normalmente
          if (cnpjCheckError.response?.status === 404) {
            console.log(
              `✅ CNPJ ${cnpj} não existe. Pode prosseguir com criação normal.`
            );
          } else {
            console.warn(`⚠️ Erro ao verificar CNPJ:`, cnpjCheckError);
            // Continuar mesmo com erro na verificação
          }
        }
      } else {
        console.log(`📝 Modo edição: Pulando validação de CNPJ duplicado`);
      }

      // Preparar dados para o backend conforme schema EstablishmentCreate
      const cleanedData = {
        company_id: dataToSave.establishment.company_id,
        code: dataToSave.establishment.code.trim().toUpperCase(),
        type: dataToSave.establishment.type,
        category: dataToSave.establishment.category,
        is_active: dataToSave.establishment.is_active,
        is_principal: dataToSave.establishment.is_principal,
        settings: dataToSave.establishment.settings || {},
        metadata: dataToSave.establishment.metadata || {},
        operating_hours: dataToSave.establishment.operating_hours || {},
        service_areas: dataToSave.establishment.service_areas || {},
        person: {
          name: dataToSave.person.name.trim(),
          tax_id: cnpj,
          person_type: "PJ",
          status: dataToSave.person.status,
          description: dataToSave.person.description?.trim() || null,
        },
      };

      console.log(
        "🚀 Dados que serão enviados para o backend:",
        JSON.stringify(cleanedData, null, 2)
      );

      // Salvar dados
      if (isEditing) {
        await establishmentsService.updateEstablishment(
          establishmentId!,
          cleanedData
        );
        notify.success("Estabelecimento atualizado com sucesso!");
      } else {
        await establishmentsService.createEstablishment(cleanedData);
        notify.success("Estabelecimento criado com sucesso!");
      }

      // Enriquecer endereços automaticamente após salvamento bem-sucedido
      await enrichAddressesAfterSave(dataToSave);

      // Chamar callback de sucesso
      if (onSave) {
        onSave();
      }
    } catch (err: any) {
      console.error("Erro completo:", err);

      let errorMessage = "Erro desconhecido ao salvar estabelecimento";

      if (err.response?.status === 422) {
        if (Array.isArray(err.response.data?.detail)) {
          const validationErrors = err.response.data.detail.map(
            (error: any) => {
              const field = error.loc?.join(".") || "campo";
              return `${field}: ${error.msg}`;
            }
          );
          errorMessage = `Erros de validação:\n${validationErrors.join("\n")}`;
        } else if (err.response.data?.detail) {
          errorMessage = err.response.data.detail;
        } else {
          errorMessage = "Dados inválidos. Verifique os campos obrigatórios.";
        }
      } else if (err.response?.status === 400) {
        errorMessage = "Dados inválidos. Verifique os campos obrigatórios.";
      } else if (err.response?.status === 404) {
        errorMessage = "Estabelecimento não encontrado.";
      } else if (err.response?.status >= 500) {
        const serverError =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          "Erro interno do servidor";
        errorMessage = `Erro interno do servidor: ${serverError}`;
      } else if (err.message) {
        errorMessage = `Erro de conexão: ${err.message}`;
      }

      setError(errorMessage);
      notify.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    // State
    loading,
    error,
    formData,
    companies,
    showNumberConfirmation,
    isEditing,
    isCompanyPreselected: Boolean(companyId && !establishmentId),

    // Actions
    setError,
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

    // Modal state
    setShowNumberConfirmation,
    setPendingAddresses,
  };
};
