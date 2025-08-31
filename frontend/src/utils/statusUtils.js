export const getStatusBadge = (status) => {
  const baseClasses = 'px-3 py-1 text-sm font-medium rounded-full';
  switch (status) {
    case 'active':
      return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
    case 'inactive':
      return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    case 'suspended':
      return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
    default:
      return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
  }
};

export const getStatusLabel = (status) => {
  switch (status) {
    case 'active': return 'Ativo';
    case 'inactive': return 'Inativo';
    case 'suspended': return 'Suspenso';
    default: return status;
  }
};

export const getPhoneTypeLabel = (type) => {
  switch (type) {
    case 'commercial': return 'Comercial';
    case 'mobile': return 'Celular';
    case 'fax': return 'Fax';
    default: return type;
  }
};

export const getEmailTypeLabel = (type) => {
  switch (type) {
    case 'work': return 'Trabalho';
    case 'personal': return 'Pessoal';
    case 'other': return 'Outro';
    default: return type;
  }
};

export const getAddressTypeLabel = (type) => {
  switch (type) {
    case 'commercial': return 'Comercial';
    case 'residential': return 'Residencial';
    case 'billing': return 'Cobrança';
    case 'delivery': return 'Entrega';
    default: return type;
  }
};

export const formatTaxId = (taxId) => {
  if (!taxId) return '-';
  return taxId.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
};

export const formatPhone = (phone) => {
  if (!phone.number) return '-';
  const number = phone.number.replace(/\D/g, '');
  if (number.length === 11) {
    return `+${phone.country_code} (${number.slice(0,2)}) ${number.slice(2,7)}-${number.slice(7)}`;
  }
  if (number.length === 10) {
    return `+${phone.country_code} (${number.slice(0,2)}) ${number.slice(2,6)}-${number.slice(6)}`;
  }
  return `+${phone.country_code} ${number}`;
};

export const formatZipCode = (zipCode) => {
  if (!zipCode) return '-';
  return zipCode.replace(/^(\d{5})(\d{3})$/, '$1-$2');
};