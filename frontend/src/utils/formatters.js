/**
 * Formatters - Funções para formatação de entrada de dados
 */

import { removeNonNumeric } from './validators';

/**
 * Formatar CPF: 123.456.789-01
 */
export const formatCPF = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 3) return numbers;
  if (numbers.length <= 6) return `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
  if (numbers.length <= 9) return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
  return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9, 11)}`;
};

/**
 * Formatar CNPJ: 12.345.678/0001-90
 */
export const formatCNPJ = (value) => {
  const numbers = removeNonNumeric(value);
  if (numbers.length <= 2) return numbers;
  if (numbers.length <= 5) return `${numbers.slice(0, 2)}.${numbers.slice(2)}`;
  if (numbers.length <= 8) return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5)}`;
  if (numbers.length <= 12) return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8)}`;
  return `${numbers.slice(0, 2)}.${numbers.slice(2, 5)}.${numbers.slice(5, 8)}/${numbers.slice(8, 12)}-${numbers.slice(12, 14)}`;
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
  if (numbers.length <= 6) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
  if (numbers.length <= 10) {
    // Telefone fixo: (11) 9999-9999
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 6)}-${numbers.slice(6)}`;
  }
  // Celular: (11) 99999-9999
  return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7, 11)}`;
};

/**
 * Formatar moeda brasileira: R$ 1.234,56
 */
export const formatCurrency = (value) => {
  const numbers = removeNonNumeric(value);
  if (!numbers) return '';
  
  const numValue = parseFloat(numbers) / 100;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
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
    .replace(/[R$\s]/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
    
  return parseFloat(numbers) || 0;
};

/**
 * Parser para data - converte DD/MM/AAAA para AAAA-MM-DD
 */
export const parseDate = (formattedDate) => {
  if (!formattedDate) return '';
  
  const parts = formattedDate.split('/');
  if (parts.length !== 3) return '';
  
  const [day, month, year] = parts;
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
};

/**
 * Aplicar máscara genérica
 */
export const applyMask = (value, mask) => {
  if (!value || !mask) return value;
  
  const numbers = removeNonNumeric(value);
  let masked = '';
  let numberIndex = 0;
  
  for (let i = 0; i < mask.length && numberIndex < numbers.length; i++) {
    if (mask[i] === '#') {
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
  CPF: '###.###.###-##',
  CNPJ: '##.###.###/####-##',
  CEP: '#####-###',
  PHONE_MOBILE: '(##) #####-####',
  PHONE_LANDLINE: '(##) ####-####',
  DATE: '##/##/####'
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
  if (!str) return '';
  return str.replace(/\b\w/g, (char) => char.toUpperCase());
};

/**
 * Normalizar string para busca (remove acentos, case insensitive)
 */
export const normalizeForSearch = (str) => {
  if (!str) return '';
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
};