/**
 * Validators - Funções tipadas para validação de dados brasileiros  
 * Migrado para TypeScript com type safety
 */

import { ValidationResult } from '@/types';

// ===============================
// UTILITY FUNCTIONS
// ===============================

/**
 * Remove caracteres não numéricos de uma string
 */
export const removeNonNumeric = (value: string): string => {
  return value ? value.replace(/\D/g, '') : '';
};

/**
 * Formata string com máscara
 */
export const applyMask = (value: string, mask: string): string => {
  if (!value || !mask) return value;
  
  const numbers = removeNonNumeric(value);
  let formatted = '';
  let numberIndex = 0;
  
  for (let i = 0; i < mask.length && numberIndex < numbers.length; i++) {
    if (mask[i] === '#') {
      formatted += numbers[numberIndex];
      numberIndex++;
    } else {
      formatted += mask[i];
    }
  }
  
  return formatted;
};

// ===============================
// VALIDATION FUNCTIONS
// ===============================

/**
 * Validação de CPF com algoritmo oficial
 */
export const validateCPF = (cpf: string): boolean => {
  const numbers = removeNonNumeric(cpf);
  
  if (numbers.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(numbers)) return false; // Todos iguais
  
  // Primeiro dígito
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(numbers.charAt(i)) * (10 - i);
  }
  let remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(numbers.charAt(9))) return false;
  
  // Segundo dígito
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(numbers.charAt(i)) * (11 - i);
  }
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(numbers.charAt(10))) return false;
  
  return true;
};

/**
 * Validação de CNPJ com algoritmo oficial
 */
export const validateCNPJ = (cnpj: string): boolean => {
  const numbers = removeNonNumeric(cnpj);
  
  if (numbers.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(numbers)) return false; // Todos iguais
  
  // Primeiro dígito
  let sum = 0;
  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  for (let i = 0; i < 12; i++) {
    sum += parseInt(numbers.charAt(i)) * weights1[i];
  }
  let remainder = sum % 11;
  const digit1 = remainder < 2 ? 0 : 11 - remainder;
  if (digit1 !== parseInt(numbers.charAt(12))) return false;
  
  // Segundo dígito
  sum = 0;
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  for (let i = 0; i < 13; i++) {
    sum += parseInt(numbers.charAt(i)) * weights2[i];
  }
  remainder = sum % 11;
  const digit2 = remainder < 2 ? 0 : 11 - remainder;
  if (digit2 !== parseInt(numbers.charAt(13))) return false;
  
  return true;
};

/**
 * Validação de CEP brasileiro
 */
export const validateCEP = (cep: string): boolean => {
  const numbers = removeNonNumeric(cep);
  return numbers.length === 8 && !/^0{8}$/.test(numbers);
};

/**
 * Validação de telefone brasileiro
 */
export const validatePhone = (phone: string): boolean => {
  const numbers = removeNonNumeric(phone);
  
  // Celular: 11 dígitos (2 DDD + 9 dígitos começando com 9)
  // Fixo: 10 dígitos (2 DDD + 8 dígitos)
  if (numbers.length === 11) {
    const ddd = numbers.substring(0, 2);
    const number = numbers.substring(2);
    return VALID_DDDS.includes(parseInt(ddd)) && number.charAt(0) === '9';
  }
  
  if (numbers.length === 10) {
    const ddd = numbers.substring(0, 2);
    const number = numbers.substring(2);
    return VALID_DDDS.includes(parseInt(ddd)) && ['2', '3', '4', '5'].includes(number.charAt(0));
  }
  
  return false;
};

/**
 * Validação de email
 */
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// ===============================
// VALIDATION HELPERS
// ===============================

/**
 * Lista de DDDs válidos no Brasil
 */
export const VALID_DDDS: number[] = [
  11, 12, 13, 14, 15, 16, 17, 18, 19, // São Paulo
  21, 22, 24, // Rio de Janeiro
  27, 28, // Espírito Santo
  31, 32, 33, 34, 35, 37, 38, // Minas Gerais
  41, 42, 43, 44, 45, 46, // Paraná
  47, 48, 49, // Santa Catarina
  51, 53, 54, 55, // Rio Grande do Sul
  61, // Distrito Federal
  62, 64, // Goiás
  63, // Tocantins
  65, 66, // Mato Grosso
  67, // Mato Grosso do Sul
  68, // Acre
  69, // Rondônia
  71, 73, 74, 75, 77, // Bahia
  79, // Sergipe
  81, 87, // Pernambuco
  82, // Alagoas
  83, // Paraíba
  84, // Rio Grande do Norte
  85, 88, // Ceará
  86, 89, // Piauí
  91, 93, 94, // Pará
  92, 97, // Amazonas
  95, // Roraima
  96, // Amapá
  98, 99, // Maranhão
];

// ===============================
// VALIDATION RESULT BUILDERS
// ===============================

/**
 * Cria resultado de validação para CPF
 */
export const validateCPFWithResult = (cpf: string): ValidationResult => {
  const isValid = validateCPF(cpf);
  return {
    isValid,
    errors: isValid ? [] : [{ field: 'cpf', message: 'CPF inválido' }]
  };
};

/**
 * Cria resultado de validação para CNPJ
 */
export const validateCNPJWithResult = (cnpj: string): ValidationResult => {
  const isValid = validateCNPJ(cnpj);
  return {
    isValid,
    errors: isValid ? [] : [{ field: 'cnpj', message: 'CNPJ inválido' }]
  };
};

/**
 * Cria resultado de validação para CEP
 */
export const validateCEPWithResult = (cep: string): ValidationResult => {
  const isValid = validateCEP(cep);
  return {
    isValid,
    errors: isValid ? [] : [{ field: 'cep', message: 'CEP inválido' }]
  };
};

/**
 * Cria resultado de validação para telefone
 */
export const validatePhoneWithResult = (phone: string): ValidationResult => {
  const isValid = validatePhone(phone);
  return {
    isValid,
    errors: isValid ? [] : [{ field: 'phone', message: 'Telefone inválido' }]
  };
};

/**
 * Cria resultado de validação para email
 */
export const validateEmailWithResult = (email: string): ValidationResult => {
  const isValid = validateEmail(email);
  return {
    isValid,
    errors: isValid ? [] : [{ field: 'email', message: 'Email inválido' }]
  };
};

// ===============================
// FORMATTERS
// ===============================

/**
 * Formatar CPF
 */
export const formatCPF = (cpf: string): string => {
  return applyMask(cpf, '###.###.###-##');
};

/**
 * Formatar CNPJ
 */
export const formatCNPJ = (cnpj: string): string => {
  return applyMask(cnpj, '##.###.###/####-##');
};

/**
 * Formatar CEP
 */
export const formatCEP = (cep: string): string => {
  return applyMask(cep, '#####-###');
};

/**
 * Formatar telefone
 */
export const formatPhone = (phone: string): string => {
  const numbers = removeNonNumeric(phone);
  
  if (numbers.length === 11) {
    return applyMask(phone, '(##) #####-####');
  } else if (numbers.length === 10) {
    return applyMask(phone, '(##) ####-####');
  }
  
  return phone;
};