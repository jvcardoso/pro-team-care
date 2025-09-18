/**
 * Utilitários para geração automática de códigos de cliente
 * Formato: C[INICIAIS_ESTABELECIMENTO][SEQUENCIAL] - Ex: CHSC001, CABC002
 * Garantia de UNICIDADE por estabelecimento conforme constraint do banco
 */

/**
 * Extrai as iniciais do nome do estabelecimento
 * @param {string} establishmentName - Nome do estabelecimento
 * @returns {string} Iniciais (máximo 3 caracteres)
 */
export const extractEstablishmentInitials = (establishmentName) => {
  if (!establishmentName || typeof establishmentName !== "string") {
    return "EST"; // Fallback padrão
  }

  // Remover caracteres especiais e normalizar
  const cleanName = establishmentName
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // Remove acentos
    .replace(/[^a-zA-Z\s]/g, "") // Remove caracteres especiais
    .trim()
    .toUpperCase();

  if (!cleanName) {
    return "EST"; // Fallback se nome estiver vazio após limpeza
  }

  // Dividir em palavras e filtrar palavras irrelevantes
  const irrelevantWords = [
    "DE",
    "DA",
    "DO",
    "DOS",
    "DAS",
    "E",
    "EM",
    "NA",
    "NO",
    "POR",
    "PARA",
    "COM",
    "SEM",
    "SOBRE",
    "ENTRE",
    "CONTRA",
    "LTDA",
    "EIRELI",
    "S/A",
    "SA",
    "SOCIEDADE",
    "EMPRESA",
    "COMPANHIA",
    "CIA",
    "ASSOCIACAO",
    "FUNDACAO",
    "INSTITUTO",
    "ORGANIZACAO",
    "COOPERATIVA",
    "SINDICATO",
    "FEDERACAO",
    "HOSPITAL",
    "CLINICA",
    "CENTRO",
    "POSTO",
    "UNIDADE",
    "UPA",
    "UBS",
  ];

  const words = cleanName
    .split(/\s+/)
    .filter((word) => word.length > 0 && !irrelevantWords.includes(word));

  if (words.length === 0) {
    return "EST"; // Fallback se não houver palavras válidas
  }

  // Estratégia de extração de iniciais
  let initials = "";

  if (words.length === 1) {
    // Uma palavra: pegar primeiras 3 letras
    initials = words[0].substring(0, 3);
  } else if (words.length === 2) {
    // Duas palavras: pegar primeira letra de cada + primeira da primeira
    initials = words[0].charAt(0) + words[1].charAt(0) + words[0].charAt(1);
  } else {
    // Três ou mais palavras: pegar primeira letra das 3 primeiras
    initials = words
      .slice(0, 3)
      .map((word) => word.charAt(0))
      .join("");
  }

  // Garantir que tem pelo menos 2 caracteres e máximo 3
  if (initials.length < 2) {
    initials = (initials + words[0].substring(0, 3)).substring(0, 3);
  } else if (initials.length > 3) {
    initials = initials.substring(0, 3);
  }

  return initials;
};

/**
 * Gera um código de cliente baseado no estabelecimento
 * @param {object} establishment - Dados do estabelecimento
 * @param {number} sequence - Número sequencial (opcional)
 * @returns {string} Código no formato C[INICIAIS][SEQUENCIAL]
 */
export const generateClientCode = (establishment, sequence = 1) => {
  if (!establishment) {
    return `CLI${String(sequence).padStart(3, "0")}`;
  }

  // Tentar diferentes campos para o nome do estabelecimento
  const establishmentName =
    establishment.name ||
    establishment.person?.name ||
    establishment.person_name ||
    "ESTABELECIMENTO";

  const initials = extractEstablishmentInitials(establishmentName);
  const sequentialNumber = String(sequence).padStart(3, "0");

  return `C${initials}${sequentialNumber}`;
};

/**
 * Sugere códigos de cliente com base nos existentes no estabelecimento
 * IMPORTANTE: Garante UNICIDADE por estabelecimento (constraint do banco)
 * @param {object} establishment - Dados do estabelecimento
 * @param {array} existingClients - Clientes existentes do estabelecimento
 * @returns {string} Código sugerido único
 */
export const suggestClientCode = (establishment, existingClients = []) => {
  if (!establishment) {
    return generateClientCode(null, 1);
  }

  const establishmentName =
    establishment.name ||
    establishment.person?.name ||
    establishment.person_name ||
    "ESTABELECIMENTO";

  const initials = extractEstablishmentInitials(establishmentName);
  const prefix = `C${initials}`;

  console.log(`🔍 Gerando código para estabelecimento: ${establishmentName}`);
  console.log(`📋 Prefixo: ${prefix}`);
  console.log(`📊 Clientes existentes: ${existingClients.length}`);

  // Encontrar o próximo número sequencial disponível
  let maxSequence = 0;

  existingClients.forEach((client) => {
    const code = client.client_code || client.code;
    if (code && code.startsWith(prefix)) {
      // Extrair número do final do código
      const match = code.match(/(\d+)$/);
      if (match) {
        const sequence = parseInt(match[1], 10);
        if (sequence > maxSequence) {
          maxSequence = sequence;
        }
        console.log(
          `✅ Código existente encontrado: ${code} (sequência: ${sequence})`
        );
      }
    }
  });

  const nextSequence = maxSequence + 1;
  const suggestedCode = generateClientCode(establishment, nextSequence);

  console.log(`🎯 Próxima sequência: ${nextSequence}`);
  console.log(`✨ Código sugerido: ${suggestedCode}`);

  return suggestedCode;
};

/**
 * Valida se um código de cliente está no formato correto
 * @param {string} code - Código para validar
 * @returns {object} {isValid: boolean, message: string}
 */
export const validateClientCode = (code) => {
  if (!code || typeof code !== "string") {
    return { isValid: false, message: "Código é obrigatório" };
  }

  const cleanCode = code.trim().toUpperCase();

  // Verificar formato: C + 2-3 letras + 3 dígitos
  const formatRegex = /^C[A-Z]{2,3}\d{3}$/;

  if (!formatRegex.test(cleanCode)) {
    return {
      isValid: false,
      message:
        "Formato inválido. Use: C + iniciais (2-3 letras) + sequencial (3 dígitos). Ex: CHSC001",
    };
  }

  if (cleanCode.length < 6 || cleanCode.length > 7) {
    return {
      isValid: false,
      message: "Código deve ter entre 6 e 7 caracteres",
    };
  }

  return { isValid: true, message: "Código válido" };
};

/**
 * Verifica se um código já existe no estabelecimento (para validação de unicidade)
 * @param {string} code - Código para verificar
 * @param {array} existingClients - Clientes existentes do estabelecimento
 * @param {number} excludeClientId - ID do cliente a excluir da verificação (para edição)
 * @returns {boolean} true se código já existe
 */
export const isClientCodeDuplicated = (
  code,
  existingClients = [],
  excludeClientId = null
) => {
  if (!code) return false;

  const cleanCode = code.trim().toUpperCase();

  return existingClients.some((client) => {
    const clientCode = (client.client_code || client.code || "")
      .trim()
      .toUpperCase();
    const clientId = client.id || client.client_id;

    // Excluir o próprio cliente da verificação (caso de edição)
    if (excludeClientId && clientId === excludeClientId) {
      return false;
    }

    return clientCode === cleanCode;
  });
};

/**
 * Exemplos de uso e casos de teste
 */
export const getClientCodeExamples = () => {
  return [
    {
      establishment: "Hospital Santa Catarina",
      expected: "CHSC001",
      explanation: "C + HSC (Hospital Santa Catarina) + 001",
    },
    {
      establishment: "Clínica Médica Avançada",
      expected: "CCMA001",
      explanation: "C + CMA (Clínica Médica Avançada) + 001",
    },
    {
      establishment: "UPA Central Norte",
      expected: "CCN001",
      explanation: "C + CN (Central Norte) + 001 (UPA removido)",
    },
    {
      establishment: "Centro Cardiológico",
      expected: "CCAR001",
      explanation: "C + CAR (palavra única, primeiras 3 letras) + 001",
    },
  ];
};
