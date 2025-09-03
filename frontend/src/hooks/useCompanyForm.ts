import { useState, useCallback, useEffect } from "react";
import { companiesService } from "../services/api";
import { consultarCNPJ } from "../services/cnpjService";
import addressEnrichmentService from "../services/addressEnrichmentService";
import toast from "react-hot-toast";
import { validateEmail } from "../utils/validators";
import {
  Phone,
  Email,
  Address,
  People,
  PersonType,
  CompanyStatus,
  PhoneType,
  EmailType,
  AddressType,
} from "../types";

interface FormData {
  people: Partial<People> & {
    person_type: PersonType;
    name: string;
    trade_name?: string;
    tax_id: string;
    status: CompanyStatus;
  };
  company: {
    settings: Record<string, any>;
    metadata: Record<string, any>;
    display_order: number;
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

interface UseCompanyFormProps {
  companyId?: number;
  onSave?: () => void;
}

export const useCompanyForm = ({ companyId, onSave }: UseCompanyFormProps) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    people: {
      person_type: PersonType.PJ,
      name: "",
      trade_name: "",
      tax_id: "",
      secondary_tax_id: "",
      incorporation_date: "",
      tax_regime: "simples_nacional",
      legal_nature: "ltda",
      municipal_registration: "",
      website: "",
      description: "",
      status: CompanyStatus.ACTIVE,
    },
    company: {
      settings: {},
      metadata: {},
      display_order: 0,
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
  const [pendingAddresses, setPendingAddresses] = useState<FormData | null>(
    null
  );

  const isEditing = Boolean(companyId);

  const loadCompany = useCallback(async (): Promise<void> => {
    if (!companyId) return;

    try {
      setLoading(true);
      const company = await companiesService.getCompany(companyId);
      // Garantir que metadados CNAE estejam disponíveis em company.metadata
      // A API retorna metadata diretamente no root da empresa
      const companyMetadata =
        company.metadata ||
        company.company?.metadata ||
        company.people?.metadata ||
        {};

      setFormData({
        people: company.people,
        company: company.company
          ? {
              ...company.company,
              metadata: companyMetadata,
            }
          : {
              settings: {},
              metadata: companyMetadata,
              display_order: 0,
            },
        phones:
          company.phones.length > 0
            ? company.phones
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
          company.emails.length > 0
            ? company.emails
            : [
                {
                  email_address: "",
                  type: EmailType.WORK,
                  is_principal: true,
                },
              ],
        addresses:
          company.addresses.length > 0
            ? company.addresses
            : [
                {
                  street: "",
                  number: "",
                  details: "",
                  neighborhood: "",
                  city: "",
                  state: "",
                  zip_code: "",
                  country: "BR",
                  type: AddressType.COMMERCIAL,
                  is_principal: true,
                },
              ],
      });
    } catch (err) {
      setError("Erro ao carregar empresa");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (companyId) {
      loadCompany();
    }
  }, [companyId, loadCompany]);

  const updatePeople = (field: keyof People, value: any): void => {
    setFormData((prev) => ({
      ...prev,
      people: { ...prev.people, [field]: value },
    }));
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

  const handleCompanyFound = async (companyData: any): Promise<void> => {
    try {
      // Verificar se CNPJ já existe no sistema
      const cleanCNPJ = companyData.people?.tax_id?.replace(/[./-]/g, "") || "";
      const existingCompany = await companiesService.getCompanyByCNPJ(
        cleanCNPJ
      );

      if (existingCompany) {
        // CNPJ já existe - mostrar mensagem de erro
        toast.error(
          "Este CNPJ já está cadastrado no sistema. Você pode editar a empresa existente.",
          {
            duration: 6000,
            icon: "⚠️",
          }
        );
        return;
      }

      // CNPJ não existe - preencher automaticamente os dados
      await fillData(companyData);
    } catch (error: any) {
      if (error.response?.status === 404) {
        // CNPJ não encontrado no sistema - pode prosseguir com preenchimento
        await fillData(companyData);
      } else {
        // Outro erro - mostrar mensagem genérica e prosseguir
        console.error("Erro ao verificar CNPJ:", error);
        toast.error(
          "Erro ao verificar CNPJ. Prosseguindo com preenchimento automático.",
          {
            duration: 4000,
            icon: "⚠️",
          }
        );
        await fillData(companyData);
      }
    }
  };

  const fillData = async (companyData: any): Promise<void> => {
    if (process.env.NODE_ENV === "development") {
      console.log("Iniciando preenchimento de dados da empresa");
    }

    // Manter CNPJ atual
    const currentCNPJ = formData.people.tax_id;

    // Preparar dados básicos
    const basicFormData: FormData = {
      people: {
        person_type: PersonType.PJ,
        name: companyData.people?.name || "",
        trade_name: companyData.people?.trade_name || "",
        tax_id: currentCNPJ,
        secondary_tax_id: companyData.people?.secondary_tax_id || "",
        incorporation_date: companyData.people?.incorporation_date || "",
        tax_regime: companyData.people?.tax_regime || "simples_nacional",
        legal_nature: companyData.people?.legal_nature || "",
        municipal_registration:
          companyData.people?.municipal_registration || "",
        website: companyData.people?.website || "",
        description: companyData.people?.description || "",
        status: companyData.people?.status || "active",
      },
      company: {
        settings: companyData.company?.settings || {},
        metadata: companyData.people?.metadata || {},
        display_order: companyData.company?.display_order || 0,
      },
      phones:
        companyData.phones && companyData.phones.length > 0
          ? companyData.phones.map((phone: any) => ({
              country_code: phone.country_code || "55",
              number: phone.number || "",
              type: phone.type || PhoneType.COMMERCIAL,
              is_principal: phone.is_principal || false,
              is_whatsapp: phone.is_whatsapp || false,
            }))
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
        companyData.emails && companyData.emails.length > 0
          ? companyData.emails.map((email: any) => ({
              email_address: email.email_address || "",
              type: email.type || EmailType.WORK,
              is_principal: email.is_principal || false,
            }))
          : [
              {
                email_address: "",
                type: EmailType.WORK,
                is_principal: true,
              },
            ],
      addresses:
        companyData.addresses && companyData.addresses.length > 0
          ? companyData.addresses.map((address: any) => ({
              street: address.street || "",
              number:
                address.number &&
                address.number !== "S/N" &&
                address.number !== "s/n"
                  ? address.number
                  : "",
              details: address.details || "",
              neighborhood: address.neighborhood || "",
              city: address.city || "",
              state: address.state || "",
              zip_code: address.zip_code || "",
              country: address.country || "BR",
              type: address.type || "commercial",
              is_principal: address.is_principal || false,
              latitude: address.latitude,
              longitude: address.longitude,
              geocoding_source: address.geocoding_source,
              geocoding_accuracy: address.geocoding_accuracy,
            }))
          : [
              {
                street: "",
                number: "",
                details: "",
                neighborhood: "",
                city: "",
                state: "",
                zip_code: "",
                country: "BR",
                type: PhoneType.COMMERCIAL,
                is_principal: true,
              },
            ],
    };

    // Atualizar formulário com dados básicos primeiro
    setFormData(basicFormData);

    // Mostrar toast inicial
    toast.success("Dados básicos carregados da Receita Federal!", {
      duration: 3000,
      icon: "📋",
    });

    // Enriquecer endereços automaticamente
    if (basicFormData.addresses && basicFormData.addresses.length > 0) {
      console.log("🔄 Iniciando enriquecimento automático de endereços...");

      try {
        // Enriquecer endereços com ViaCEP + geocoding
        const enrichedAddresses =
          await addressEnrichmentService.enriquecerMultiplosEnderecos(
            basicFormData.addresses
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
          toast.success(
            "Endereços enriquecidos com coordenadas GPS e dados oficiais!",
            {
              duration: 4000,
              icon: "🗺️",
            }
          );
        } else if (hasViaCepData) {
          toast.success(
            "Endereços enriquecidos com dados oficiais do ViaCEP!",
            {
              duration: 4000,
              icon: "🏠",
            }
          );
        } else {
          console.warn("Endereços não foram enriquecidos completamente");
          toast(
            "Dados básicos carregados, mas houve problemas no enriquecimento.",
            {
              duration: 3000,
              icon: "⚠️",
            }
          );
        }
      } catch (error) {
        console.error("Erro ao enriquecer endereços:", error);
        toast(
          "Dados básicos carregados, mas houve erro no enriquecimento de endereços.",
          {
            duration: 4000,
            icon: "⚠️",
          }
        );
      }
    } else {
      console.log("ℹ️ Nenhum endereço para enriquecer");
    }
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

  const proceedWithSave = async (dataToSave: FormData): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Limpar valores undefined/null que podem causar problemas no backend
      const sanitizeData = (obj: any): any => {
        if (obj === null || obj === undefined) return obj;
        if (typeof obj === "object") {
          const cleaned: any = {};
          for (const [key, value] of Object.entries(obj)) {
            // Processar metadata mantendo campos importantes
            if (
              key === "metadata" &&
              typeof value === "object" &&
              value !== null
            ) {
              const cleanMetadata: any = {};
              const metadata = value as any;

              // Manter TODOS os campos de metadata da Receita Federal (mesmo se null/undefined)
              const camposRF = [
                "cnae_fiscal",
                "cnae_fiscal_descricao",
                "cnaes_secundarios",
                "porte",
                "capital_social",
                "natureza_juridica",
                "situacao",
                "motivo_situacao",
                "data_situacao",
                "situacao_especial",
                "data_situacao_especial",
                "tipo",
                "efr",
                "municipio",
                "uf",
                "ultima_atualizacao_rf",
                "receita_ws_data",
                "consulta_data",
              ];

              for (const campo of camposRF) {
                if (metadata.hasOwnProperty(campo)) {
                  cleanMetadata[campo] = metadata[campo];
                }
              }

              // Manter outros campos de metadata também
              for (const [metaKey, metaValue] of Object.entries(metadata)) {
                if (!camposRF.includes(metaKey) && metaValue !== undefined) {
                  cleanMetadata[metaKey] = metaValue;
                }
              }

              cleaned[key] = cleanMetadata;
            } else if (value !== null && value !== undefined && value !== "") {
              cleaned[key] = sanitizeData(value);
            }
          }
          return cleaned;
        }
        return obj;
      };

      // Limpar campos vazios e preparar dados
      const cleanedData = {
        people: sanitizeData(dataToSave.people),
        company: sanitizeData(dataToSave.company) || {
          settings: {},
          metadata: {},
          display_order: 0,
        },
        phones: dataToSave.phones
          .filter(
            (phone) => phone.number?.trim() && phone.number.trim().length >= 8
          )
          .map((phone) =>
            sanitizeData({
              country_code: phone.country_code || "55",
              number: phone.number.trim().replace(/\D/g, ""),
              type: phone.type || PhoneType.COMMERCIAL,
              is_principal: phone.is_principal || false,
              is_whatsapp: phone.is_whatsapp || false,
            })
          )
          .slice(0, 3),
        emails: dataToSave.emails
          .filter((email) => email.email_address?.trim())
          .map((email) =>
            sanitizeData({
              email_address: email.email_address.trim(),
              type: email.type || EmailType.WORK,
              is_principal: email.is_principal || false,
            })
          ),
        addresses: dataToSave.addresses
          .filter((address) => address.street?.trim() && address.city?.trim())
          .map((address) => {
            const cleanAddress = {
              ...address,
              country: address.country || "BR",
              type: address.type || AddressType.COMMERCIAL,
              is_principal: address.is_principal || false,
              number: address.number?.trim() || "S/N",
            };
            return sanitizeData(cleanAddress);
          })
          .slice(0, 1),
      };

      // Garantir que o campo company esteja sempre presente
      if (
        !cleanedData.company ||
        Object.keys(cleanedData.company).length === 0
      ) {
        cleanedData.company = {
          settings: {},
          metadata: {},
          display_order: 0,
        };
      }

      // Verificar se os arrays têm pelo menos um item válido
      if (cleanedData.phones.length === 0) {
        setError("Pelo menos um telefone deve ser válido");
        return;
      }

       // Validate email formats
       const invalidEmails = cleanedData.emails.filter(
         (email) => !validateEmail(email.email_address)
       );

       if (invalidEmails.length > 0) {
         setError(`E-mail(s) inválido(s): ${invalidEmails.map(e => e.email_address).join(", ")}`);
         return;
       }

       if (cleanedData.emails.length === 0) {
         setError("Pelo menos um email deve ser válido");
         return;
       }

      if (cleanedData.addresses.length === 0) {
        setError("Pelo menos um endereço deve ser válido");
        return;
      }

      // Validações finais dos campos obrigatórios
      if (!cleanedData.people.person_type) {
        cleanedData.people.person_type = PersonType.PJ;
      }

      if (!cleanedData.people.status) {
        cleanedData.people.status = PersonStatus.ACTIVE;
      }

      // Salvar dados
      if (isEditing) {
        await companiesService.updateCompany(companyId!, cleanedData);
        toast.success("Empresa atualizada com sucesso!");
      } else {
        await companiesService.createCompany(cleanedData);
        toast.success("Empresa criada com sucesso!");
      }

      // Chamar callback de sucesso
      if (onSave) {
        onSave();
      }
    } catch (err: any) {
      console.error("Erro completo:", err);
      console.error("Response data:", err.response?.data);

      let errorMessage = "Erro desconhecido ao salvar empresa";

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
        errorMessage = "Empresa não encontrada.";
      } else if (err.response?.status >= 500) {
        const serverError =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          "Erro interno do servidor";
        errorMessage = `Erro interno do servidor: ${serverError}. Verifique os logs do backend.`;
        console.error("Erro 500 - Detalhes do servidor:", err.response?.data);
      } else if (err.message) {
        errorMessage = `Erro de conexão: ${err.message}`;
      }

      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    // State
    loading,
    error,
    formData,
    showNumberConfirmation,
    isEditing,

    // Actions
    setError,
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

    // Modal state
    setShowNumberConfirmation,
    setPendingAddresses,
  };
};

export default useCompanyForm;
