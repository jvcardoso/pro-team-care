/**
 * Company Types - Baseado na estrutura da API
 */

export interface Company {
  id: number;
  person_id: number;
  name: string;
  trade_name?: string;
  tax_id: string;
  status: "active" | "inactive" | "suspended";
  establishments_count?: number;
  clients_count?: number;
  professionals_count?: number;
  users_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface CompanyDetailed extends Company {
  people?: any;
  phones?: any[];
  emails?: any[];
  addresses?: any[];
}

export interface CompanyCreate {
  name: string;
  trade_name?: string;
  tax_id: string;
  status?: "active" | "inactive" | "suspended";
}

export interface CompanyUpdate extends Partial<CompanyCreate> {
  id: number;
}
