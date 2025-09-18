import { useState, useCallback, useEffect } from "react";
import { clientsService } from "../services/clientsService";
import { establishmentsService } from "../services/api.js";
import {
  validateEmail,
  validateTaxId,
  detectPersonTypeFromTaxId,
} from "../utils/validators.js";
import { notify } from "../utils/notifications.jsx";
import {
  processDuplicationCheck as processClientDuplication,
  createClientDataWithExistingPerson,
  shouldCheckDuplication,
} from "../utils/clientDuplicationLogic.js";
import {
  ClientDetailed,
  ClientCreate,
  ClientUpdate,
  ClientFormData,
  ClientStatus,
  PersonType,
  PersonStatus,
  PhoneType,
  EmailType,
  AddressType,
  Gender,
  MaritalStatus,
} from "../types";

interface UseClientFormProps {
  clientId?: number;
  onSave?: () => void;
}

export const useClientForm = ({ clientId, onSave }: UseClientFormProps) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [availableEstablishments, setAvailableEstablishments] = useState<
    Array<{
      id: number;
      name: string;
      establishment_code: string;
    }>
  >([]);

  const [formData, setFormData] = useState<ClientFormData>({
    establishment_id: 0,
    client_code: "",
    status: ClientStatus.ACTIVE,
    person: {
      name: "",
      trade_name: "",
      tax_id: "",
      secondary_tax_id: "",
      person_type: PersonType.PF,
      birth_date: "",
      gender: Gender.NOT_INFORMED,
      marital_status: MaritalStatus.NOT_INFORMED,
      occupation: "",
      incorporation_date: "",
      tax_regime: "",
      legal_nature: "",
      municipal_registration: "",
      website: "",
      description: "",
      lgpd_consent_version: "1.0",
    },
    existing_person_id: undefined,
    phones: [
      {
        country_code: "55",
        area_code: "",
        number: "",
        extension: "",
        type: PhoneType.MOBILE,
        is_principal: true,
        is_whatsapp: false,
        description: "",
      },
    ],
    emails: [
      {
        email_address: "",
        type: EmailType.PERSONAL,
        is_principal: true,
        is_verified: false,
        description: "",
      },
    ],
    addresses: [
      {
        street: "",
        number: "",
        complement: "",
        neighborhood: "",
        city: "",
        state: "",
        zip_code: "",
        country: "BR",
        type: AddressType.RESIDENTIAL,
        is_principal: true,
        latitude: undefined,
        longitude: undefined,
        ibge_city_code: "",
        gia_code: "",
        siafi_code: "",
        area_code: "",
        description: "",
      },
    ],
  });

  const isEditing = Boolean(clientId);

  // Load available establishments on mount
  useEffect(() => {
    const loadEstablishments = async () => {
      try {
        console.log("🔍 Carregando estabelecimentos disponíveis...");
        const response = await establishmentsService.getEstablishments();
        console.log("📊 Resposta da API de establishments:", response);

        // Acessar os establishments do response correto
        const establishments =
          response.establishments || response.items || response || [];
        console.log("🏢 Establishments encontrados:", establishments);

        const mappedEstablishments = establishments.map((est: any) => {
          console.log("📋 Mapeando establishment:", est);
          return {
            id: est.id,
            name: est.person?.name || est.name || "Estabelecimento sem nome",
            establishment_code: est.code || est.establishment_code || "",
          };
        });

        console.log("✅ Establishments mapeados:", mappedEstablishments);
        setAvailableEstablishments(mappedEstablishments);
      } catch (err) {
        console.error("❌ Erro ao carregar estabelecimentos:", err);
        notify.error("Erro ao carregar estabelecimentos disponíveis");
      }
    };

    loadEstablishments();
  }, []);

  // Load client data for editing
  const loadClient = useCallback(async (): Promise<void> => {
    if (!clientId) return;

    try {
      setLoading(true);
      const client = await clientsService.getById(clientId);

      setFormData({
        establishment_id: client.establishment_id,
        client_code: client.client_code || "",
        status: client.status,
        person: {
          name: client.person.name,
          trade_name: client.person.trade_name || "",
          tax_id: client.person.tax_id,
          secondary_tax_id: client.person.secondary_tax_id || "",
          person_type: client.person.person_type,
          birth_date: client.person.birth_date || "",
          gender: client.person.gender || Gender.NOT_INFORMED,
          marital_status:
            client.person.marital_status || MaritalStatus.NOT_INFORMED,
          occupation: client.person.occupation || "",
          incorporation_date: client.person.incorporation_date || "",
          tax_regime: client.person.tax_regime || "",
          legal_nature: client.person.legal_nature || "",
          municipal_registration: client.person.municipal_registration || "",
          website: client.person.website || "",
          description: client.person.description || "",
          lgpd_consent_version: client.person.lgpd_consent_version || "1.0",
        },
        existing_person_id: client.person_id,
        phones:
          client.phones.length > 0
            ? client.phones
            : [
                {
                  country_code: "55",
                  area_code: "",
                  number: "",
                  extension: "",
                  type: PhoneType.MOBILE,
                  is_principal: true,
                  is_whatsapp: false,
                  description: "",
                },
              ],
        emails:
          client.emails.length > 0
            ? client.emails
            : [
                {
                  email_address: "",
                  type: EmailType.PERSONAL,
                  is_principal: true,
                  is_verified: false,
                  description: "",
                },
              ],
        addresses:
          client.addresses.length > 0
            ? client.addresses
            : [
                {
                  street: "",
                  number: "",
                  complement: "",
                  neighborhood: "",
                  city: "",
                  state: "",
                  zip_code: "",
                  country: "BR",
                  type: AddressType.RESIDENTIAL,
                  is_principal: true,
                  latitude: undefined,
                  longitude: undefined,
                  ibge_city_code: "",
                  gia_code: "",
                  siafi_code: "",
                  area_code: "",
                  description: "",
                },
              ],
      });
    } catch (err) {
      setError("Erro ao carregar cliente");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    if (clientId) {
      loadClient();
    }
  }, [clientId, loadClient]);

  // Handle tax ID change and determine person type
  const handleTaxIdChange = (taxId: string) => {
    const cleanTaxId = taxId.replace(/\D/g, "");

    // Detectar automaticamente o tipo de pessoa baseado no CPF/CNPJ
    const detection = detectPersonTypeFromTaxId(cleanTaxId);

    console.log(`🔍 Detectando tipo de documento: ${cleanTaxId}`);
    console.log(
      `📋 Resultado: ${detection.documentType} - ${detection.personType} - Válido: ${detection.isValid}`
    );

    setFormData((prev) => ({
      ...prev,
      person: {
        ...prev.person!,
        tax_id: cleanTaxId,
        person_type: detection.personType || PersonType.PF, // Default para PF se não detectar
      },
      existing_person_id: undefined, // Reset existing person when tax_id changes
    }));
  };

  // Update person data
  const updatePerson = (
    field: keyof NonNullable<ClientFormData["person"]>,
    value: any
  ): void => {
    setFormData((prev) => ({
      ...prev,
      person: prev.person ? { ...prev.person, [field]: value } : undefined,
    }));
  };

  // Update client data
  const updateClient = (field: string, value: any): void => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Proceed with save (alias for save function)
  const proceedWithSave = async (data: ClientFormData): Promise<void> => {
    await save();
  };

  // Handle phones
  const handlePhonesChange = (phones: ClientFormData["phones"]): void => {
    setFormData((prev) => ({ ...prev, phones }));
  };

  const handlePhoneAdd = (newPhone: ClientFormData["phones"][0]): void => {
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

  // Handle emails
  const handleEmailsChange = (emails: ClientFormData["emails"]): void => {
    setFormData((prev) => ({ ...prev, emails }));
  };

  const handleEmailAdd = (newEmail: ClientFormData["emails"][0]): void => {
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

  // Handle addresses
  const handleAddressesChange = (
    addresses: ClientFormData["addresses"]
  ): void => {
    setFormData((prev) => ({ ...prev, addresses }));
  };

  const handleAddressAdd = (
    newAddress: ClientFormData["addresses"][0]
  ): void => {
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

  // Helper functions for duplication handling
  const shouldCheckDuplication = (
    taxId: string,
    establishmentId: number
  ): boolean => {
    return !!(taxId && establishmentId > 0);
  };

  const createClientDataWithExistingPerson = (
    existingPerson: any,
    establishmentId: number,
    clientCode: string
  ) => {
    return {
      establishment_id: establishmentId,
      client_code: clientCode,
      status: ClientStatus.ACTIVE,
      existing_person_id: existingPerson.id,
    };
  };

  // Validate form data
  const validateForm = (data: ClientFormData): string[] => {
    const errors: string[] = [];

    // Basic validation
    if (!data.establishment_id || data.establishment_id <= 0) {
      errors.push("Estabelecimento é obrigatório");
    }

    // Validate client code (now required)
    if (!data.client_code?.trim()) {
      errors.push("Código do cliente é obrigatório");
    }

    if (data.person) {
      if (!data.person.name?.trim()) {
        errors.push("Nome é obrigatório");
      }

      if (!data.person.tax_id?.trim()) {
        errors.push("CPF/CNPJ é obrigatório");
      } else if (!validateTaxId(data.person.tax_id)) {
        errors.push("CPF/CNPJ inválido");
      }
    } else if (!data.existing_person_id) {
      errors.push("Dados da pessoa ou pessoa existente são obrigatórios");
    }

    // Validate phones (optional for now)
    const validPhones = data.phones.filter(
      (phone) => phone.number?.trim() && phone.number.trim().length >= 8
    );
    // Temporarily removed requirement for contacts during client creation
    // if (validPhones.length === 0) {
    //   errors.push("Pelo menos um telefone válido é obrigatório");
    // }

    // Validate emails (optional for now)
    const validEmails = data.emails.filter((email) => {
      return email.email_address?.trim() && validateEmail(email.email_address);
    });
    // Temporarily removed requirement for contacts during client creation
    // if (validEmails.length === 0) {
    //   errors.push("Pelo menos um e-mail válido é obrigatório");
    // }

    // Validate addresses (optional for now)
    const validAddresses = data.addresses.filter((address) => {
      return (
        address.street?.trim() && address.city?.trim() && address.state?.trim()
      );
    });
    // Temporarily removed requirement for contacts during client creation
    // if (validAddresses.length === 0) {
    //   errors.push("Pelo menos um endereço válido é obrigatório");
    // }

    return errors;
  };

  // Save client
  // 🎯 FUNÇÃO COPIADA DO ESTABLISHMENT (que funciona!)
  const saveWithExistingPerson = async (
    taxId: string,
    establishmentId: number
  ) => {
    try {
      console.log(
        `💾 Salvando cliente com pessoa existente para tax_id: ${taxId}`
      );

      // Buscar dados da pessoa existente via API (como faz o establishment)
      const existingClients = await clientsService.getByTaxId(taxId);

      if (existingClients && existingClients.length > 0) {
        const existingPerson = existingClients[0].person;

        console.log(`🔄 Pessoa encontrada:`, existingPerson);

        // Preparar dados para reutilizar pessoa existente (IGUAL establishment)
        const reuseData = {
          establishment_id: establishmentId,
          client_code: formData.client_code?.trim(),
          status: formData.status,
          // 🔑 Campo especial para indicar reutilização (IGUAL establishment)
          existing_person_id: existingPerson.id,
        };

        console.log(
          "🚀 Dados para salvamento com pessoa existente:",
          JSON.stringify(reuseData, null, 2)
        );

        const savedClient = await clientsService.create(reuseData);
        console.log(
          `✅ Cliente criado com sucesso reutilizando pessoa:`,
          savedClient
        );

        notify.success("Cliente criado com sucesso usando dados existentes!");

        if (onSave) {
          onSave();
        }
      } else {
        throw new Error("Pessoa não encontrada para reutilização");
      }
    } catch (err: any) {
      console.error("Erro ao salvar com pessoa existente:", err);

      let errorMessage = "Erro ao salvar cliente com dados existentes";
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
      notify.error(errorMessage);
    }
  };

  const save = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      // Validate form
      const validationErrors = validateForm(formData);
      if (validationErrors.length > 0) {
        setError(validationErrors.join("; "));
        return;
      }

      // 🔍 Nova lógica de verificação de duplicação para CPF e CNPJ
      if (
        !isEditing &&
        formData.person &&
        formData.person.tax_id &&
        formData.establishment_id > 0
      ) {
        const taxId = formData.person.tax_id;
        const establishmentId = formData.establishment_id;

        if (shouldCheckDuplication(taxId, establishmentId)) {
          try {
            console.log(
              `🔍 Verificando duplicação de ${taxId} no estabelecimento ${establishmentId}...`
            );

            const checkResult =
              await clientsService.checkExistingInEstablishment(
                establishmentId,
                taxId
              );
            const duplicationResult = processClientDuplication(
              checkResult,
              establishmentId
            );

            console.log(`📋 Resultado da verificação:`, duplicationResult);

            if (duplicationResult.action === "BLOCK") {
              // CENÁRIOS 1 e 3: Cliente já existe no mesmo estabelecimento → IMPEDIR
              console.log(
                `🚫 ${duplicationResult.scenario}: Bloqueando criação`
              );
              setError(duplicationResult.message);
              notify.error(duplicationResult.title);
              return;
            } else if (duplicationResult.action === "OFFER_REUSE") {
              // CENÁRIOS 2 e 4: Pessoa existe mas sem cliente no estabelecimento → OFERECER REUTILIZAÇÃO
              console.log(
                `🔄 ${duplicationResult.scenario}: Oferecendo reutilização`
              );

              notify.confirm(
                duplicationResult.title,
                duplicationResult.message,
                async () => {
                  // Confirmar - reutilizar dados da pessoa existente
                  console.log(
                    `✅ Usuário confirmou reutilização da pessoa existente`
                  );

                  if (duplicationResult.existingPerson) {
                    const reuseData = createClientDataWithExistingPerson(
                      duplicationResult.existingPerson,
                      establishmentId,
                      formData.client_code
                    );

                    try {
                      const savedClient = await clientsService.create(
                        reuseData
                      );
                      console.log(
                        `✅ Cliente criado com sucesso reutilizando pessoa:`,
                        savedClient
                      );
                      notify.success("Cliente criado com sucesso!");

                      if (onSave) {
                        onSave();
                      }
                    } catch (saveError) {
                      console.error(
                        `❌ Erro ao salvar cliente com pessoa reutilizada:`,
                        saveError
                      );
                      setError("Erro ao salvar cliente. Tente novamente.");
                    }
                  }
                },
                () => {
                  // Cancelar - continuar com formulário atual (permitir override)
                  console.log(
                    `❌ Usuário optou por não reutilizar. Permitindo prosseguir com dados novos.`
                  );
                  // Não bloquear, apenas notificar
                  notify.info(
                    "Você pode alterar o CPF/CNPJ para prosseguir com dados novos"
                  );
                }
              );
              return;
            }
            // CENÁRIO 5: Nenhum conflito → ALLOW (continua com execução normal)
            console.log(
              `✅ ${duplicationResult.scenario}: Sem conflitos, prosseguindo...`
            );
          } catch (duplicateCheckError: any) {
            // Em caso de erro na verificação, loggar mas permitir continuar
            console.warn(
              `⚠️ Erro ao verificar duplicação:`,
              duplicateCheckError
            );

            // 🎯 CORREÇÃO: Implementar lógica igual ao establishment (FUNCIONA!)
            const errorDetail = duplicateCheckError.response?.data?.detail;
            if (
              errorDetail &&
              typeof errorDetail === "string" &&
              errorDetail.includes(taxId)
            ) {
              // Usar lógica exata do establishment que funciona
              notify.confirm(
                "CPF/CNPJ já cadastrado",
                `O ${
                  taxId.length === 11 ? "CPF" : "CNPJ"
                } ${taxId} já está cadastrado no sistema.\n\nDeseja reutilizar os dados existentes dessa pessoa para criar o cliente?`,
                async () => {
                  // Confirmar - reutilizar dados existentes (IGUAL establishment)
                  console.log(
                    `✅ Usuário confirmou reutilização da pessoa existente`
                  );
                  await saveWithExistingPerson(taxId, establishmentId);
                },
                () => {
                  // Cancelar - não criar cliente (IGUAL establishment)
                  console.log(
                    `❌ Usuário cancelou. Precisa informar outro CPF/CNPJ`
                  );
                  setError(
                    "Por favor, informe um CPF/CNPJ diferente ou confirme o uso do documento existente."
                  );
                }
              );
              return;
            }

            // Não bloquear o usuário se a API de verificação falhar
          }
        }
      }

      // Clean and prepare data - FORÇAR LIMPEZA DO TAX_ID
      const cleanedData: ClientCreate | ClientUpdate = {
        establishment_id: formData.establishment_id,
        client_code: formData.client_code?.trim(), // Now required
        status: formData.status,
      };

      console.log(
        `🔍 DEBUG - formData.person.tax_id antes da limpeza:`,
        formData.person?.tax_id
      );

      // Add person data if creating new person
      if (formData.person && !formData.existing_person_id) {
        // 🎯 LIMPEZA ABSOLUTA COM VALIDAÇÃO RIGOROSA
        let cleanTaxId = (formData.person.tax_id || "")
          .replace(/\D/g, "")
          .trim();

        console.log(`🔍 DEBUG - tax_id original:`, formData.person.tax_id);
        console.log(`🔍 DEBUG - tax_id após limpeza:`, cleanTaxId);
        console.log(`🔍 DEBUG - tax_id comprimento:`, cleanTaxId.length);

        // Validação extra
        if (cleanTaxId.length !== 11 && cleanTaxId.length !== 14) {
          throw new Error(
            `Tax ID deve ter 11 (CPF) ou 14 (CNPJ) dígitos. Atual: ${cleanTaxId.length}`
          );
        }

        // Verificação final: garantir que não há caracteres especiais
        if (!/^\d+$/.test(cleanTaxId)) {
          throw new Error(
            `Tax ID deve conter apenas números. Atual: "${cleanTaxId}"`
          );
        }

        cleanedData.person = {
          name: formData.person.name.trim(),
          trade_name: formData.person.trade_name?.trim() || undefined,
          tax_id: cleanTaxId,
          secondary_tax_id:
            formData.person.secondary_tax_id?.replace(/\D/g, "") || undefined,
          person_type: formData.person.person_type,
          birth_date: formData.person.birth_date || undefined,
          gender:
            formData.person.gender !== Gender.NOT_INFORMED
              ? formData.person.gender
              : undefined,
          marital_status:
            formData.person.marital_status !== MaritalStatus.NOT_INFORMED
              ? formData.person.marital_status
              : undefined,
          occupation: formData.person.occupation?.trim() || undefined,
          incorporation_date: formData.person.incorporation_date || undefined,
          tax_regime: formData.person.tax_regime?.trim() || undefined,
          legal_nature: formData.person.legal_nature?.trim() || undefined,
          municipal_registration:
            formData.person.municipal_registration?.trim() || undefined,
          website: formData.person.website?.trim() || undefined,
          status: PersonStatus.ACTIVE,
          description: formData.person.description?.trim() || undefined,
          lgpd_consent_version: formData.person.lgpd_consent_version,
        };

        // Temporarily not sending contacts - will be added later
        // (cleanedData as ClientCreate).phones = cleanPhones;
        // (cleanedData as ClientCreate).emails = cleanEmails;
        // (cleanedData as ClientCreate).addresses = cleanAddresses;
      } else if (formData.existing_person_id) {
        (cleanedData as ClientCreate).existing_person_id =
          formData.existing_person_id;
      }

      // Temporarily not processing contacts - will be added later
      // const cleanPhones = formData.phones
      //   .filter(phone => phone.number?.trim() && phone.number.trim().length >= 8)
      //   .map(phone => ({
      //     country_code: phone.country_code || "55",
      //     area_code: phone.area_code?.trim() || undefined,
      //     number: phone.number.replace(/\D/g, ""),
      //     extension: phone.extension?.trim() || undefined,
      //     type: phone.type,
      //     is_principal: phone.is_principal,
      //     is_whatsapp: phone.is_whatsapp,
      //     description: phone.description?.trim() || undefined,
      //   }));

      // const cleanEmails = formData.emails
      //   .filter(email => email.email_address?.trim() && validateEmail(email.email_address))
      //   .map(email => ({
      //     email_address: email.email_address.trim(),
      //     type: email.type,
      //     is_principal: email.is_principal,
      //     is_verified: email.is_verified,
      //     description: email.description?.trim() || undefined,
      //   }));

      // const cleanAddresses = formData.addresses
      //   .filter(address => address.street?.trim() && address.city?.trim())
      //   .map(address => ({
      //     street: address.street.trim(),
      //     number: address.number?.trim() || undefined,
      //     complement: address.complement?.trim() || undefined,
      //     neighborhood: address.neighborhood.trim(),
      //     city: address.city.trim(),
      //     state: address.state,
      //     zip_code: address.zip_code.replace(/\D/g, ""),
      //     country: address.country || "BR",
      //     type: address.type,
      //     is_principal: address.is_principal,
      //     latitude: address.latitude,
      //     longitude: address.longitude,
      //     ibge_city_code: address.ibge_city_code?.trim() || undefined,
      //     gia_code: address.gia_code?.trim() || undefined,
      //     siafi_code: address.siafi_code?.trim() || undefined,
      //     area_code: address.area_code?.trim() || undefined,
      //     description: address.description?.trim() || undefined,
      //   }));

      // Save client
      console.log(
        `🔍 DEBUG - Payload final sendo enviado:`,
        JSON.stringify(cleanedData, null, 2)
      );

      if (isEditing) {
        await clientsService.update(clientId!, cleanedData as ClientUpdate);
        notify.success("Cliente atualizado com sucesso!");
      } else {
        await clientsService.create(cleanedData as ClientCreate);
        notify.success("Cliente criado com sucesso!");
      }

      // Call success callback
      if (onSave) {
        onSave();
      }
    } catch (err: any) {
      console.error("Erro ao salvar cliente:", err);

      let errorMessage = "Erro desconhecido ao salvar cliente";

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
          const detail = err.response.data.detail;

          // Tratar especificamente o erro de CPF/CNPJ duplicado
          if (detail.includes("já existe no sistema")) {
            errorMessage = `⚠️ ${detail}\n\n💡 Dica: Este CPF/CNPJ já está cadastrado. Para continuar:\n• Verifique se já existe um cliente com este documento\n• Use um CPF/CNPJ diferente\n• Ou entre em contato com o administrador para vincular os dados existentes`;
          } else {
            errorMessage = detail;
          }
        }
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
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
    availableEstablishments,
    isEditing,

    // Actions
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
    save,
    proceedWithSave,
  };
};

export default useClientForm;
