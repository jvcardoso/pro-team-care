/**
 * Lógica de verificação de duplicação de clientes
 * Implementa os 4 cenários especificados pelo usuário:
 *
 * 1. CPF + Cliente já existe no estabelecimento → IMPEDIR
 * 2. CPF + Pessoa existe mas sem cliente no estabelecimento → OFERECER REUTILIZAÇÃO
 * 3. CNPJ + Cliente já existe no estabelecimento → IMPEDIR
 * 4. CNPJ + Pessoa existe mas sem cliente no estabelecimento → OFERECER REUTILIZAÇÃO
 */

/**
 * Resultado da verificação de duplicação
 * @typedef {Object} DuplicationCheckResult
 * @property {'BLOCK' | 'OFFER_REUSE' | 'ALLOW'} action - Ação a ser tomada
 * @property {'CPF_EXISTS_SAME_ESTABLISHMENT' | 'CNPJ_EXISTS_SAME_ESTABLISHMENT' | 'CPF_EXISTS_OTHER_ESTABLISHMENT' | 'CNPJ_EXISTS_OTHER_ESTABLISHMENT' | 'NO_CONFLICT'} scenario - Cenário identificado
 * @property {string} title - Título da mensagem
 * @property {string} message - Mensagem para o usuário
 * @property {Object|null} existingClient - Cliente existente (se houver no mesmo estabelecimento)
 * @property {Object|null} existingPerson - Dados da pessoa (se existir globalmente)
 * @property {string} personType - Tipo de pessoa (CPF/CNPJ)
 * @property {Array} otherEstablishments - Outros estabelecimentos onde a pessoa tem clientes
 */

/**
 * Verifica duplicação e retorna ação apropriada
 * @param {Object} checkResult - Resultado da API check-existing-in-establishment
 * @param {number} establishmentId - ID do estabelecimento atual
 * @returns {DuplicationCheckResult}
 */
export function processDuplicationCheck(checkResult, establishmentId) {
  const {
    exists_in_establishment,
    existing_client,
    person_exists_globally,
    existing_person,
    person_type,
    other_establishments = [],
  } = checkResult;

  const isCPF = person_type === "PF";
  const isCNPJ = person_type === "PJ";
  const documentType = isCPF ? "CPF" : "CNPJ";

  // CENÁRIOS 1 e 3: Cliente já existe no mesmo estabelecimento → IMPEDIR
  if (exists_in_establishment && existing_client) {
    const scenario = isCPF
      ? "CPF_EXISTS_SAME_ESTABLISHMENT"
      : "CNPJ_EXISTS_SAME_ESTABLISHMENT";

    return {
      action: "BLOCK",
      scenario,
      title: `${documentType} já cadastrado`,
      message:
        `Já existe um cliente cadastrado com este ${documentType} neste estabelecimento.\n\n` +
        `Cliente: ${existing_client.name || "Nome não disponível"}\n` +
        `Código: ${existing_client.client_code || "Sem código"}\n` +
        `Status: ${getStatusLabel(existing_client.status)}\n\n` +
        `Não é possível prosseguir com o cadastro.`,
      existingClient: existing_client,
      existingPerson: existing_person,
      personType: person_type,
      otherEstablishments: [],
    };
  }

  // CENÁRIOS 2 e 4: Pessoa existe globalmente mas sem cliente no estabelecimento → OFERECER REUTILIZAÇÃO
  if (person_exists_globally && existing_person && !exists_in_establishment) {
    const scenario = isCPF
      ? "CPF_EXISTS_OTHER_ESTABLISHMENT"
      : "CNPJ_EXISTS_OTHER_ESTABLISHMENT";

    const otherEstablishmentsText =
      other_establishments.length > 0
        ? `\n\nEsta pessoa possui clientes em outros estabelecimentos:\n${other_establishments
            .map(
              (est) =>
                `• ${est.establishment_name} (Código: ${est.client_code})`
            )
            .join("\n")}`
        : "";

    return {
      action: "OFFER_REUSE",
      scenario,
      title: `${documentType} já cadastrado`,
      message:
        `Já existe uma ${
          isCPF ? "pessoa" : "empresa"
        } cadastrada com este ${documentType}.\n\n` +
        `${isCPF ? "Nome" : "Razão Social"}: ${
          existing_person.name || "Nome não disponível"
        }\n` +
        `${isCPF ? "CPF" : "CNPJ"}: ${formatTaxId(existing_person.tax_id)}\n` +
        `${otherEstablishmentsText}\n\n` +
        `Deseja reutilizar os dados existentes (${
          isCPF
            ? "nome, telefones, endereços, etc."
            : "razão social, nome fantasia, endereços, etc."
        }) ` +
        `para criar um novo cliente neste estabelecimento?`,
      existingClient: null,
      existingPerson: existing_person,
      personType: person_type,
      otherEstablishments,
    };
  }

  // CENÁRIO 5: Nenhum conflito → PERMITIR
  return {
    action: "ALLOW",
    scenario: "NO_CONFLICT",
    title: "Documento válido",
    message: "Nenhum conflito detectado. Prossiga com o cadastro.",
    existingClient: null,
    existingPerson: null,
    personType: person_type,
    otherEstablishments: [],
  };
}

/**
 * Obter label amigável para status do cliente
 * @param {string} status - Status do cliente
 * @returns {string}
 */
function getStatusLabel(status) {
  const labels = {
    active: "Ativo",
    inactive: "Inativo",
    on_hold: "Em Espera",
    archived: "Arquivado",
  };

  return labels[status] || status;
}

/**
 * Formatar CPF/CNPJ para exibição
 * @param {string} taxId - CPF ou CNPJ limpo (só números)
 * @returns {string}
 */
function formatTaxId(taxId) {
  if (!taxId) return "";

  const clean = taxId.replace(/\D/g, "");

  if (clean.length === 11) {
    // CPF: 000.000.000-00
    return clean.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  } else if (clean.length === 14) {
    // CNPJ: 00.000.000/0000-00
    return clean.replace(
      /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
      "$1.$2.$3/$4-$5"
    );
  }

  return taxId;
}

/**
 * Criar dados do cliente reutilizando pessoa existente
 * @param {Object} existingPerson - Dados da pessoa existente
 * @param {number} establishmentId - ID do estabelecimento
 * @param {string} clientCode - Código do cliente
 * @returns {Object} - Dados formatados para criação do cliente
 */
export function createClientDataWithExistingPerson(
  existingPerson,
  establishmentId,
  clientCode
) {
  return {
    establishment_id: establishmentId,
    client_code: clientCode,
    status: "active",
    existing_person_id: existingPerson.id,
    // Não enviar dados de person quando usando existing_person_id
    person: null,
  };
}

/**
 * Validar se CPF/CNPJ está preenchido e tem tamanho correto
 * @param {string} taxId - CPF ou CNPJ
 * @returns {boolean}
 */
export function isValidTaxIdForCheck(taxId) {
  if (!taxId || typeof taxId !== "string") return false;

  const clean = taxId.replace(/\D/g, "");
  return clean.length === 11 || clean.length === 14;
}

/**
 * Determinar se deve fazer verificação (só para documentos válidos)
 * @param {string} taxId - CPF ou CNPJ
 * @param {number} establishmentId - ID do estabelecimento
 * @returns {boolean}
 */
export function shouldCheckDuplication(taxId, establishmentId) {
  return isValidTaxIdForCheck(taxId) && establishmentId > 0;
}
