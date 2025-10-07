/**
 * Formatters - Funções para formatação de entrada de dados
 */

import { removeNonNumeric } from "./validators";

/**
 * Formatar CPF: 123.456.789-01
 */
export const formatCPF = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 3) return numbers;
  if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
  if (numbers.length <= 9)
    return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
  return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(
    6,
    9
  )}-${numbers.slice(9, 11)}`;
};

/**
 * Formatar CNPJ: 12.345.678/0001-90
 */
export const formatCNPJ = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 2) return numbers;
  if (numbers.length <= 5) return `${numbers.slice(0, 2)}.${numbers.slice(2)}`;
  if (numbers.length <= 8)
    return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5)}`;
  if (numbers.length <= 12)
    return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(
      5,
      8
    )}/${numbers.slice(8)}`;
  return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(
    5,
    8
  )}/${numbers.slice(8, 12)}-${numbers.slice(12, 14)}`;
};

/**
 * Formatar CEP: 12345-678
 */
export const formatCEP = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 5) return numbers;
  return `${numbers.slice(0, 5)}-${numbers.slice(5, 8)}`;
};

/**
 * Formatar telefone: (11) 99999-9999 ou (11) 9999-9999
 */
export const formatPhone = (value) => {
  const numbers = removeNonNumeric(value);

  if (numbers.length <= 2) return numbers;
  if (numbers.length <= 6)
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
  if (numbers.length <= 10) {
    // Telefone fixo: (11) 9999-9999
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 6)}-${numbers.slice(
      6
    )}`;
  }
  // Celular: (11) 99999-9999
  return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(
    7,
    11
  )}`;
};

/**
 * Formatar moeda brasileira: R$ 1.234,56
 */
export const formatCurrency = (value) => {
  const numbers = removeNonNumeric(value);
  if (!numbers) return "";

  const numValue = parseFloat(numbers) / 100;
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(numValue);
};

/**
 * Formatar valor numérico como moeda (para exibição)
 * @param {number|string} value - Valor numérico decimal
 * @param {object} options - Opções de formatação
 * @returns {string} Valor formatado como R$ X.XXX,XX
 */
export const formatCurrencyDisplay = (value, options = {}) => {
  if (value === null || value === undefined || value === "") return "R$ 0,00";

  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "R$ 0,00";

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...options,
  }).format(numValue);
};

/**
 * Formatar valor sem símbolo de moeda (apenas com separadores)
 * @param {number|string} value - Valor numérico decimal
 * @returns {string} Valor formatado como X.XXX,XX
 */
export const formatCurrencyValue = (value) => {
  if (value === null || value === undefined || value === "") return "0,00";

  const numValue = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(numValue)) return "0,00";

  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numValue);
};

/**
 * Formatar data: DD/MM/AAAA
 */
export const formatDate = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 2) return numbers;
  if (numbers.length <= 4) return `${numbers.slice(0, 2)}/${numbers.slice(2)}`;
  return `${numbers.slice(0, 2)}/${numbers.slice(2, 4)}/${numbers.slice(4, 8)}`;
};

/**
 * Parser para moeda - converte string formatada para número
 */
export const parseCurrency = (formattedValue) => {
  if (!formattedValue) return 0;

  const numbers = formattedValue
    .replace(/[R$\s]/g, "")
    .replace(/\./g, "")
    .replace(",", ".");

  return parseFloat(numbers) || 0;
};

/**
 * Parser melhorado para moeda - mais robusto
 * @param {string} formattedValue - Valor formatado (R$ 1.234,56 ou 1234.56)
 * @returns {number} Valor numérico decimal
 */
export const parseCurrencyRobust = (formattedValue) => {
  if (!formattedValue || formattedValue === "") return 0;

  // Converter para string se for número
  const str = formattedValue.toString();

  // Remover tudo exceto números, vírgula e ponto
  let cleanStr = str.replace(/[^0-9,.]/g, "");

  // Se tem vírgula e ponto, assume que vírgula é separador decimal
  if (cleanStr.includes(",") && cleanStr.includes(".")) {
    // Se o ponto vem antes da vírgula, ponto é separador de milhar
    const lastCommaIndex = cleanStr.lastIndexOf(",");
    const lastDotIndex = cleanStr.lastIndexOf(".");

    if (lastCommaIndex > lastDotIndex) {
      // Formato: 1.234.567,89
      cleanStr = cleanStr.replace(/\./g, "").replace(",", ".");
    } else {
      // Formato: 1,234,567.89
      cleanStr = cleanStr.replace(/,/g, "");
    }
  } else if (cleanStr.includes(",")) {
    // Apenas vírgula - assumir separador decimal
    const parts = cleanStr.split(",");
    if (parts.length === 2 && parts[1].length <= 2) {
      // Formato: 1234,56
      cleanStr = cleanStr.replace(",", ".");
    } else {
      // Formato: 1,234,567 (separador de milhares)
      cleanStr = cleanStr.replace(/,/g, "");
    }
  }

  const numValue = parseFloat(cleanStr);
  return isNaN(numValue) ? 0 : numValue;
};

/**
 * Validar valor monetário
 * @param {string|number} value - Valor a ser validado
 * @param {object} options - Opções de validação
 * @returns {object} {isValid: boolean, error: string, numericValue: number}
 */
export const validateCurrency = (value, options = {}) => {
  const {
    min = 0,
    max = null,
    required = false,
    allowNegative = false,
  } = options;

  if (required && (!value || value === "")) {
    return { isValid: false, error: "Valor é obrigatório", numericValue: 0 };
  }

  if (!value || value === "") {
    return { isValid: true, error: "", numericValue: 0 };
  }

  const numValue = parseCurrencyRobust(value);

  if (isNaN(numValue)) {
    return { isValid: false, error: "Valor inválido", numericValue: 0 };
  }

  if (!allowNegative && numValue < 0) {
    return {
      isValid: false,
      error: "Valor não pode ser negativo",
      numericValue: numValue,
    };
  }

  if (min !== null && numValue < min) {
    return {
      isValid: false,
      error: `Valor mínimo: ${formatCurrencyDisplay(min)}`,
      numericValue: numValue,
    };
  }

  if (max !== null && numValue > max) {
    return {
      isValid: false,
      error: `Valor máximo: ${formatCurrencyDisplay(max)}`,
      numericValue: numValue,
    };
  }

  return { isValid: true, error: "", numericValue: numValue };
};

/**
 * Parser para data - converte DD/MM/AAAA para AAAA-MM-DD
 */
export const parseDate = (formattedDate) => {
  if (!formattedDate) return "";

  const parts = formattedDate.split("/");
  if (parts.length !== 3) return "";

  const [day, month, year] = parts;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
};

/**
 * Aplicar máscara genérica
 */
export const applyMask = (value, mask) => {
  if (!value || !mask) return value;

  const numbers = removeNonNumeric(value);
  let masked = "";
  let numberIndex = 0;

  for (let i = 0; i < mask.length && numberIndex < numbers.length; i++) {
    if (mask[i] === "#") {
      masked += numbers[numberIndex];
      numberIndex++;
    } else {
      masked += mask[i];
    }
  }

  return masked;
};

/**
 * Máscaras predefinidas
 */
export const MASKS = {
  CPF: "###.###.###-##",
  CNPJ: "##.###.###/####-##",
  CEP: "#####-###",
  PHONE_MOBILE: "(##) #####-####",
  PHONE_LANDLINE: "(##) ####-####",
  DATE: "##/##/####",
};

/**
 * Auto-detectar tipo de telefone e aplicar máscara correta
 */
export const formatPhoneAuto = (value) => {
  const numbers = removeNonNumeric(value);

  if (numbers.length <= 10) {
    return applyMask(value, MASKS.PHONE_LANDLINE);
  }
  return applyMask(value, MASKS.PHONE_MOBILE);
};

/**
 * Limitar entrada de caracteres (para maxLength em inputs)
 */
export const limitInput = (value, maxLength) => {
  if (!value) return value;
  return value.toString().slice(0, maxLength);
};

/**
 * Capitalizar primeira letra de cada palavra
 */
export const capitalizeWords = (str) => {
  if (!str) return "";
  return str.replace(/\b\w/g, (char) => char.toUpperCase());
};

/**
 * Normalizar string para busca (remove acentos, case insensitive)
 */
export const normalizeForSearch = (str) => {
  if (!str) return "";
  return str
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
};

/**
 * Formatar CPF/CNPJ automaticamente (detecta o tipo)
 */
export const formatTaxId = (value) => {
  if (!value) return "";

  const numbers = removeNonNumeric(value);

  if (numbers.length <= 11) {
    // Formato CPF
    return formatCPF(value);
  } else {
    // Formato CNPJ
    return formatCNPJ(value);
  }
};
