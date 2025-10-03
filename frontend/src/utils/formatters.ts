/**
 * Formatting utilities
 */

export function formatTaxId(taxId: string): string {
  if (!taxId) return "";

  const cleanTaxId = taxId.replace(/\D/g, "");

  if (cleanTaxId.length === 14) {
    // CNPJ: 00.000.000/0000-00
    return cleanTaxId.replace(
      /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
      "$1.$2.$3/$4-$5"
    );
  } else if (cleanTaxId.length === 11) {
    // CPF: 000.000.000-00
    return cleanTaxId.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
  }

  return taxId;
}
