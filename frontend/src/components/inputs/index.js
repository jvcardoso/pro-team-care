// Specialized Input Components
export { default as InputPhone } from "./InputPhone";
export { default as InputCEP } from "./InputCEP";
export { default as InputEmail } from "./InputEmail";
export { default as InputCNPJ } from "./InputCNPJ";
export { default as InputCPF } from "./InputCPF";
export { default as InputDate } from "./InputDate";
export { default as InputWhatsApp } from "./InputWhatsApp";

// Re-export utilities for convenience
export {
  formatPhone,
  formatCEP,
  formatCPF,
  formatCNPJ,
  formatCurrency,
  formatDate,
} from "../../utils/formatters";

export {
  validatePhone,
  validateCEP,
  validateEmail,
  validateCPF,
  validateCNPJ,
  validateDDD,
  removeNonNumeric,
} from "../../utils/validators";
