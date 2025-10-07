/**
 * Filtro de status de ativação para lista de empresas
 */

import React from "react";
import { Filter } from "lucide-react";

interface CompanyActivationFilterProps {
  value: string;
  onChange: (value: string) => void;
  stats?: {
    total: number;
    pending_contract: number;
    contract_signed: number;
    pending_user: number;
    active: number;
    suspended: number;
  };
}

const CompanyActivationFilter: React.FC<CompanyActivationFilterProps> = ({
  value,
  onChange,
  stats,
}) => {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Filter className="h-4 w-4" />
        <span className="text-sm font-medium">Filtrar por status:</span>
      </div>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          px-3 py-2
          border border-gray-300 dark:border-gray-600
          rounded-md
          bg-white dark:bg-gray-700
          text-gray-900 dark:text-white
          text-sm
          focus:ring-2 focus:ring-primary-500 focus:border-primary-500
          min-w-[200px]
        "
      >
        <option value="all">Todas {stats ? `(${stats.total})` : ""}</option>
        <option value="pending_contract">
          ⏳ Aguardando Contrato {stats ? `(${stats.pending_contract})` : ""}
        </option>
        <option value="contract_signed">
          ✅ Contrato Assinado {stats ? `(${stats.contract_signed})` : ""}
        </option>
        <option value="pending_user">
          👤 Aguardando Usuário {stats ? `(${stats.pending_user})` : ""}
        </option>
        <option value="active">
          🟢 Ativas {stats ? `(${stats.active})` : ""}
        </option>
        <option value="suspended">
          🔴 Suspensas {stats ? `(${stats.suspended})` : ""}
        </option>
      </select>

      {value !== "all" && (
        <button
          onClick={() => onChange("all")}
          className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
        >
          Limpar filtro
        </button>
      )}
    </div>
  );
};

export default CompanyActivationFilter;
