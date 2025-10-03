/**
 * Status utilities for companies
 */

export function getStatusBadge(status: string): string {
  const statusConfig: Record<string, string> = {
    active: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    inactive: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300",
    suspended:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
  };

  return `inline-flex px-2 py-1 text-xs font-medium rounded-full ${
    statusConfig[status] || statusConfig["inactive"]
  }`;
}

export function getStatusLabel(status: string): string {
  const statusLabels: Record<string, string> = {
    active: "Ativo",
    inactive: "Inativo",
    suspended: "Suspenso",
  };

  return statusLabels[status] || status;
}
