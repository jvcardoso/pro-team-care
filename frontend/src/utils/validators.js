/**
 * Validators - Funções puras para validação de dados brasileiros
 */

/**
 * Remove caracteres não numéricos de uma string
 */
export const removeNonNumeric = (value) => {
  return value ? value.toString().replace(/\D/g, "") : "";
};

/**
 * Validação de CPF
 */
export const validateCPF = (cpf) => {
  const numbers = removeNonNumeric(cpf);

  if (numbers.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(numbers)) return false; // Todos iguais

  // Primeiro dígito verificador
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(numbers[i]) * (10 - i);
  }
  let remainder = 11 - (sum % 11);
  const firstDigit = remainder >= 10 ? 0 : remainder;

  if (parseInt(numbers[9]) !== firstDigit) return false;

  // Segundo dígito verificador
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(numbers[i]) * (11 - i);
  }
  remainder = 11 - (sum % 11);
  const secondDigit = remainder >= 10 ? 0 : remainder;

  return parseInt(numbers[10]) === secondDigit;
};

/**
 * Validação de CNPJ
 */
export const validateCNPJ = (cnpj) => {
  const numbers = removeNonNumeric(cnpj);

  if (numbers.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(numbers)) return false; // Todos iguais

  // Primeiro dígito verificador
  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(numbers[i]) * weights1[i];
  }
  let remainder = sum % 11;
  const firstDigit = remainder < 2 ? 0 : 11 - remainder;

  if (parseInt(numbers[12]) !== firstDigit) return false;

  // Segundo dígito verificador
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  sum = 0;
  for (let i = 0; i < 13; i++) {
    sum += parseInt(numbers[i]) * weights2[i];
  }
  remainder = sum % 11;
  const secondDigit = remainder < 2 ? 0 : 11 - remainder;

  return parseInt(numbers[13]) === secondDigit;
};

/**
 * Validação de CEP
 */
export const validateCEP = (cep) => {
  const numbers = removeNonNumeric(cep);
  return numbers.length === 8 && /^\d{8}$/.test(numbers);
};

/**
 * Validação de Email
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validação de Telefone Brasileiro
 */
export const validatePhone = (phone) => {
  const numbers = removeNonNumeric(phone);

  // Celular: 11 dígitos (com 9)
  // Fixo: 10 dígitos
  if (numbers.length !== 10 && numbers.length !== 11) return false;

  // Validar DDD (11 a 99)
  const ddd = parseInt(numbers.substring(0, 2));
  if (ddd < 11 || ddd > 99) return false;

  // Validar formato celular (9 na frente)
  if (numbers.length === 11) {
    const thirdDigit = parseInt(numbers[2]);
    if (thirdDigit !== 9) return false;
  }

  return true;
};

/**
 * Lista de DDDs válidos no Brasil
 */
export const VALID_DDDS = [
  11,
  12,
  13,
  14,
  15,
  16,
  17,
  18,
  19, // SP
  21,
  22,
  24, // RJ
  27,
  28, // ES
  31,
  32,
  33,
  34,
  35,
  37,
  38, // MG
  41,
  42,
  43,
  44,
  45,
  46, // PR
  47,
  48,
  49, // SC
  51,
  53,
  54,
  55, // RS
  61, // DF
  62,
  64, // GO
  63, // TO
  65,
  66, // MT
  67, // MS
  68, // AC
  69, // RO
  71,
  73,
  74,
  75,
  77, // BA
  79, // SE
  81,
  87, // PE
  82, // AL
  83, // PB
  84, // RN
  85,
  88, // CE
  86,
  89, // PI
  91,
  93,
  94, // PA
  92,
  97, // AM
  95, // RR
  96, // AP
  98,
  99, // MA
];

/**
 * Validação de DDD
 */
export const validateDDD = (ddd) => {
  const number = parseInt(removeNonNumeric(ddd));
  return VALID_DDDS.includes(number);
};

/**
 * Validações condicionais para formulários
 */
export const isRequired = (value) => {
  return value && value.toString().trim().length > 0;
};

export const minLength = (value, min) => {
  return value && value.toString().length >= min;
};

export const maxLength = (value, max) => {
  return !value || value.toString().length <= max;
};

/**
 * Validação de CPF ou CNPJ (automaticamente detecta o tipo)
 */
export const validateTaxId = (taxId) => {
  const numbers = removeNonNumeric(taxId);

  if (numbers.length === 11) {
    return validateCPF(numbers);
  } else if (numbers.length === 14) {
    return validateCNPJ(numbers);
  }

  return false;
};

/**
 * Detecta automaticamente se é CPF ou CNPJ e retorna o tipo de pessoa
 * @param {string} taxId - CPF ou CNPJ
 * @returns {object} {personType: 'PF'|'PJ'|null, isValid: boolean, documentType: 'CPF'|'CNPJ'|null}
 */
export const detectPersonTypeFromTaxId = (taxId) => {
  const numbers = removeNonNumeric(taxId);

  if (numbers.length === 11) {
    return {
      personType: "PF",
      documentType: "CPF",
      isValid: validateCPF(numbers),
      formattedValue: formatCPF(numbers),
    };
  } else if (numbers.length === 14) {
    return {
      personType: "PJ",
      documentType: "CNPJ",
      isValid: validateCNPJ(numbers),
      formattedValue: formatCNPJ(numbers),
    };
  }

  // Documento incompleto ou inválido
  return {
    personType: null,
    documentType: null,
    isValid: false,
    formattedValue: taxId,
  };
};

/**
 * Formatação de CPF (000.000.000-00)
 */
export const formatCPF = (cpf) => {
  const numbers = removeNonNumeric(cpf);
  if (numbers.length !== 11) return cpf;

  return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
};

/**
 * Formatação de CNPJ (00.000.000/0000-00)
 */
export const formatCNPJ = (cnpj) => {
  const numbers = removeNonNumeric(cnpj);
  if (numbers.length !== 14) return cnpj;

  return numbers.replace(
    /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
    "$1.$2.$3/$4-$5"
  );
};
