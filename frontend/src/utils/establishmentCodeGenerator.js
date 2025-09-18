/**
 * Utilitários para geração automática de códigos de estabelecimento
 * Formato: E[INICIAIS][SEQUENCIAL] - Ex: EHSC001, EABC002
 */

/**
 * Extrai as iniciais da razão social da empresa
 * @param {string} companyName - Nome da empresa
 * @returns {string} Iniciais (máximo 3 caracteres)
 */
export const extractCompanyInitials = (companyName) => {
  if (!companyName || typeof companyName !== "string") {
    return "EST"; // Fallback padrão
  }

  // Remover caracteres especiais e normalizar
  const cleanName = companyName
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
 * Gera um código de estabelecimento baseado na empresa
 * @param {object} company - Dados da empresa
 * @param {number} sequence - Número sequencial (opcional)
 * @returns {string} Código no formato E[INICIAIS][SEQUENCIAL]
 */
export const generateEstablishmentCode = (company, sequence = 1) => {
  if (!company) {
    return `EST${String(sequence).padStart(3, "0")}`;
  }

  // Tentar diferentes campos para o nome da empresa
  const companyName =
    company.name || company.people?.name || company.person_name || "EMPRESA";

  const initials = extractCompanyInitials(companyName);
  const sequentialNumber = String(sequence).padStart(3, "0");

  return `E${initials}${sequentialNumber}`;
};

/**
 * Sugere códigos de estabelecimento com base nos existentes
 * @param {object} company - Dados da empresa
 * @param {array} existingEstablishments - Estabelecimentos existentes da empresa
 * @returns {string} Código sugerido
 */
export const suggestEstablishmentCode = (
  company,
  existingEstablishments = []
) => {
  if (!company) {
    return generateEstablishmentCode(null, 1);
  }

  const companyName =
    company.name || company.people?.name || company.person_name || "EMPRESA";
  const initials = extractCompanyInitials(companyName);
  const prefix = `E${initials}`;

  // Encontrar o próximo número sequencial disponível
  let maxSequence = 0;

  existingEstablishments.forEach((est) => {
    if (est.code && est.code.startsWith(prefix)) {
      // Extrair número do final do código
      const match = est.code.match(/(\d+)$/);
      if (match) {
        const sequence = parseInt(match[1], 10);
        if (sequence > maxSequence) {
          maxSequence = sequence;
        }
      }
    }
  });

  const nextSequence = maxSequence + 1;
  return generateEstablishmentCode(company, nextSequence);
};

/**
 * Valida se um código de estabelecimento está no formato correto
 * @param {string} code - Código para validar
 * @returns {object} {isValid: boolean, message: string}
 */
export const validateEstablishmentCode = (code) => {
  if (!code || typeof code !== "string") {
    return { isValid: false, message: "Código é obrigatório" };
  }

  const cleanCode = code.trim().toUpperCase();

  // Verificar formato: E + 2-3 letras + 3 dígitos
  const formatRegex = /^E[A-Z]{2,3}\d{3}$/;

  if (!formatRegex.test(cleanCode)) {
    return {
      isValid: false,
      message:
        "Formato inválido. Use: E + iniciais (2-3 letras) + sequencial (3 dígitos). Ex: EHSC001",
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
 * Exemplos de uso e casos de teste
 */
export const getCodeExamples = () => {
  return [
    {
      company: "Hospital Santa Catarina",
      expected: "EHSC001",
      explanation: "E + HSC (Hospital Santa Catarina) + 001",
    },
    {
      company: "Associação Beneficente Síria",
      expected: "EABS001",
      explanation: "E + ABS (Associação Beneficente Síria) + 001",
    },
    {
      company: "Clínica Médica Avançada LTDA",
      expected: "ECMA001",
      explanation: "E + CMA (Clínica Médica Avançada) + 001",
    },
    {
      company: "Instituto de Cardiologia",
      expected: "EIC001",
      explanation: "E + IC + primeira letra repetida = EIC + 001",
    },
  ];
};
