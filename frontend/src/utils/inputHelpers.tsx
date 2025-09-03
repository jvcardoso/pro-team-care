/**
 * Input Helpers - Configurações padronizadas para BaseInputField
 * 🎯 Centraliza formatação e validação para reutilização
 */

import React from "react";
import {
  User,
  Building,
  Phone,
  Mail,
  MapPin,
  Calendar,
  DollarSign,
} from "lucide-react";
import {
  formatCPF,
  formatCNPJ,
  formatPhone,
  formatCEP,
  formatCurrency,
  formatDate,
} from "./formatters";
import {
  removeNonNumeric,
  validateCPF,
  validateCNPJ,
  validatePhone,
  validateCEP,
  validateEmail,
} from "./validators";
import type {
  FormatterConfig,
  ValidatorConfig,
  ValidationResult,
} from "../components/inputs/BaseInputField";

// 🔢 CPF Configuration
export const cpfConfig = {
  formatter: {
    formatter: formatCPF,
    cleaner: removeNonNumeric,
    maxLength: 11,
    completedLength: 14, // formato: 000.000.000-00
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      const cleanValue = removeNonNumeric(value);

      if (!cleanValue && required) {
        return { isValid: false, message: "CPF é obrigatório" };
      }

      if (!cleanValue) {
        return { isValid: true, message: "" };
      }

      if (cleanValue.length < 11) {
        return {
          isValid: false,
          message: "CPF deve ter 11 dígitos",
          isComplete: false,
        };
      }

      if (!validateCPF(cleanValue)) {
        return { isValid: false, message: "CPF inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <User className="h-4 w-4" />,
  placeholder: "000.000.000-00",
  inputMode: "numeric" as const,
  autoComplete: "off",
  successMessage: "CPF válido",
  progressMessage: (remaining: number) => `${remaining} dígitos restantes`,
};

// 🏢 CNPJ Configuration
export const cnpjConfig = {
  formatter: {
    formatter: formatCNPJ,
    cleaner: removeNonNumeric,
    maxLength: 14,
    completedLength: 18, // formato: 00.000.000/0000-00
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      const cleanValue = removeNonNumeric(value);

      if (!cleanValue && required) {
        return { isValid: false, message: "CNPJ é obrigatório" };
      }

      if (!cleanValue) {
        return { isValid: true, message: "" };
      }

      if (cleanValue.length < 14) {
        return {
          isValid: false,
          message: "CNPJ deve ter 14 dígitos",
          isComplete: false,
        };
      }

      if (!validateCNPJ(cleanValue)) {
        return { isValid: false, message: "CNPJ inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <Building className="h-4 w-4" />,
  placeholder: "00.000.000/0000-00",
  inputMode: "numeric" as const,
  autoComplete: "off",
  successMessage: "CNPJ válido",
  progressMessage: (remaining: number) => `${remaining} dígitos restantes`,
};

// 📱 Phone Configuration
export const phoneConfig = {
  formatter: {
    formatter: formatPhone,
    cleaner: removeNonNumeric,
    maxLength: 11,
    completedLength: 15, // formato: (00) 00000-0000
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      const cleanValue = removeNonNumeric(value);

      if (!cleanValue && required) {
        return { isValid: false, message: "Telefone é obrigatório" };
      }

      if (!cleanValue) {
        return { isValid: true, message: "" };
      }

      if (cleanValue.length < 10) {
        return {
          isValid: false,
          message: "Telefone deve ter pelo menos 10 dígitos",
          isComplete: false,
        };
      }

      if (!validatePhone(cleanValue)) {
        return { isValid: false, message: "Telefone inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <Phone className="h-4 w-4" />,
  placeholder: "(00) 00000-0000",
  inputMode: "tel" as const,
  autoComplete: "tel",
  successMessage: "Telefone válido",
  progressMessage: (remaining: number) => `${remaining} dígitos restantes`,
};

// 📧 Email Configuration
export const emailConfig = {
  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      if (!value && required) {
        return { isValid: false, message: "Email é obrigatório" };
      }

      if (!value) {
        return { isValid: true, message: "" };
      }

      if (!validateEmail(value)) {
        return { isValid: false, message: "Email inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnChange: true,
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <Mail className="h-4 w-4" />,
  placeholder: "seu@email.com",
  type: "email" as const,
  inputMode: "email" as const,
  autoComplete: "email",
  successMessage: "Email válido",
};

// 🗺️ CEP Configuration
export const cepConfig = {
  formatter: {
    formatter: formatCEP,
    cleaner: removeNonNumeric,
    maxLength: 8,
    completedLength: 9, // formato: 00000-000
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      const cleanValue = removeNonNumeric(value);

      if (!cleanValue && required) {
        return { isValid: false, message: "CEP é obrigatório" };
      }

      if (!cleanValue) {
        return { isValid: true, message: "" };
      }

      if (cleanValue.length < 8) {
        return {
          isValid: false,
          message: "CEP deve ter 8 dígitos",
          isComplete: false,
        };
      }

      if (!validateCEP(cleanValue)) {
        return { isValid: false, message: "CEP inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <MapPin className="h-4 w-4" />,
  placeholder: "00000-000",
  inputMode: "numeric" as const,
  autoComplete: "postal-code",
  successMessage: "CEP válido",
  progressMessage: (remaining: number) => `${remaining} dígitos restantes`,
};

// 📅 Date Configuration
export const dateConfig = {
  formatter: {
    formatter: formatDate,
    cleaner: removeNonNumeric,
    maxLength: 8,
    completedLength: 10, // formato: 00/00/0000
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      const cleanValue = removeNonNumeric(value);

      if (!cleanValue && required) {
        return { isValid: false, message: "Data é obrigatória" };
      }

      if (!cleanValue) {
        return { isValid: true, message: "" };
      }

      if (cleanValue.length < 8) {
        return {
          isValid: false,
          message: "Data deve ter 8 dígitos",
          isComplete: false,
        };
      }

      // Validação básica de data
      const day = parseInt(cleanValue.substr(0, 2));
      const month = parseInt(cleanValue.substr(2, 2));
      const year = parseInt(cleanValue.substr(4, 4));

      if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900) {
        return { isValid: false, message: "Data inválida" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,

  icon: <Calendar className="h-4 w-4" />,
  placeholder: "dd/mm/aaaa",
  inputMode: "numeric" as const,
  successMessage: "Data válida",
  progressMessage: (remaining: number) => `${remaining} dígitos restantes`,
};

// 💰 Currency Configuration
export const currencyConfig = {
  formatter: {
    formatter: formatCurrency,
    cleaner: removeNonNumeric,
  } as FormatterConfig,

  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      if (!value && required) {
        return { isValid: false, message: "Valor é obrigatório" };
      }

      if (!value) {
        return { isValid: true, message: "" };
      }

      const numericValue = parseFloat(removeNonNumeric(value));

      if (isNaN(numericValue) || numericValue < 0) {
        return { isValid: false, message: "Valor inválido" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: true,
      };
    },
    validateOnChange: true,
  } as ValidatorConfig,

  icon: <DollarSign className="h-4 w-4" />,
  placeholder: "R$ 0,00",
  inputMode: "numeric" as const,
  successMessage: "Valor válido",
};

// 🔤 Text Configuration (sem formatação especial)
export const textConfig = {
  validator: {
    validator: (value: string, required?: boolean): ValidationResult => {
      if (!value?.trim() && required) {
        return { isValid: false, message: "Campo obrigatório" };
      }

      return {
        isValid: true,
        message: "",
        isComplete: !!value?.trim(),
      };
    },
    validateOnBlur: true,
  } as ValidatorConfig,
};
