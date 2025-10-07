/**
 * Utilitários para geração automática de códigos de cliente
 * Formato: CLI-{cod-empresa}-{seq} - Ex: CLI-057-001, CLI-012-001
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
 * @returns {string} Código no formato CLI-{cod-empresa}-{seq}
 */
export const generateClientCode = (establishment, sequence = 1) => {
  if (!establishment) {
    return `CLI-000-${String(sequence).padStart(3, "0")}`;
  }

  // Extrair código da empresa do código do estabelecimento (EST-057-002 → 057)
  const establishmentCode = establishment.code || `EST-000-001`;
  const companyCodeMatch = establishmentCode.match(/EST-(\d{3})-\d{3}/);
  const companyCode = companyCodeMatch ? companyCodeMatch[1] : "000";
  const sequentialNumber = String(sequence).padStart(3, "0");

  return `CLI-${companyCode}-${sequentialNumber}`;
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

  // Extrair código da empresa do código do estabelecimento (EST-057-002 → 057)
  const establishmentCode = establishment.code || `EST-000-001`;
  const companyCodeMatch = establishmentCode.match(/EST-(\d{3})-\d{3}/);
  const companyCode = companyCodeMatch ? companyCodeMatch[1] : "000";
  const prefix = `CLI-${companyCode}-`;

  console.log(
    `🔍 Gerando código para estabelecimento: ${
      establishment.name || establishment.person?.name
    }`
  );
  console.log(`📋 Código do estabelecimento: ${establishmentCode}`);
  console.log(`📋 Código da empresa extraído: ${companyCode}`);
  console.log(`📋 Prefixo: ${prefix}`);
  console.log(`📊 Clientes existentes: ${existingClients.length}`);

  // Encontrar o próximo número sequencial disponível
  let maxSequence = 0;

  existingClients.forEach((client) => {
    const code = client.client_code || client.code;
    if (code && code.startsWith(prefix)) {
      // Extrair número do final do código (após o último hífen)
      const match = code.match(/-(\d+)$/);
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

  // Verificar formato: CLI-XXX-XXX (onde X são dígitos)
  const formatRegex = /^CLI-\d{3}-\d{3}$/;

  if (!formatRegex.test(cleanCode)) {
    return {
      isValid: false,
      message:
        "Formato inválido. Use: CLI-XXX-XXX (onde X são dígitos). Ex: CLI-057-001",
    };
  }

  if (cleanCode.length !== 11) {
    return {
      isValid: false,
      message: "Código deve ter exatamente 11 caracteres (CLI-XXX-XXX)",
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
      establishment: { code: "EST-057-001", name: "Hospital Santa Catarina" },
      expected: "CLI-057-001",
      explanation: "CLI + código da empresa (057) + sequencial (001)",
    },
    {
      establishment: { code: "EST-012-002", name: "Clínica Médica Avançada" },
      expected: "CLI-012-001",
      explanation: "CLI + código da empresa (012) + sequencial (001)",
    },
    {
      establishment: { code: "EST-123-001", name: "UPA Central Norte" },
      expected: "CLI-123-001",
      explanation: "CLI + código da empresa (123) + sequencial (001)",
    },
    {
      establishment: { code: "EST-005-003", name: "Centro Cardiológico" },
      expected: "CLI-005-001",
      explanation: "CLI + código da empresa (005) + sequencial (001)",
    },
  ];
};
