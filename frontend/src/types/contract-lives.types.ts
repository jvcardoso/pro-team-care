/**
 * Tipos TypeScript para Contract Lives (Vidas de Contratos)
 * Sincronizado com schemas Pydantic do backend
 */

/**
 * Tipos de relacionamento de uma vida com o contrato
 */
export type RelationshipType =
  | "TITULAR"
  | "DEPENDENTE"
  | "FUNCIONARIO"
  | "BENEFICIARIO";

/**
 * Status possíveis de uma vida no contrato
 */
export type ContractLifeStatus =
  | "active"
  | "inactive"
  | "substituted"
  | "cancelled";

/**
 * Tipo de ação no histórico de auditoria
 */
export type HistoryAction = "created" | "updated" | "substituted" | "cancelled";

/**
 * Interface completa de uma vida de contrato (response da API)
 */
export interface ContractLife {
  id: number;
  contract_id: number;
  person_id: number;
  person_name: string;
  person_cpf: string;
  start_date: string; // ISO date: YYYY-MM-DD
  end_date: string | null;
  relationship_type: RelationshipType;
  status: ContractLifeStatus;
  substitution_reason: string | null;
  allows_substitution: boolean;
  primary_service_address: Record<string, any> | null; // JSON genérico
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  created_by: number | null;

  // Campos opcionais (para visualização global)
  contract_number?: string;
  client_name?: string;
}

/**
 * DTO para criar uma nova vida no contrato
 */
export interface ContractLifeCreateDTO {
  person_name: string;
  start_date: string; // YYYY-MM-DD
  end_date?: string | null; // YYYY-MM-DD
  relationship_type: RelationshipType;
  allows_substitution?: boolean;
  notes?: string;
}

/**
 * DTO para atualizar uma vida existente
 */
export interface ContractLifeUpdateDTO {
  end_date?: string | null;
  status?: ContractLifeStatus;
  notes?: string;
  substitution_reason?: string;
}

/**
 * Parâmetros de filtro para listagem de vidas
 */
export interface ContractLifeListParams {
  status?: ContractLifeStatus;
  relationship_type?: RelationshipType;
  start_date_from?: string;
  start_date_to?: string;
  active_only?: boolean;
}

/**
 * Estatísticas de vidas de um contrato
 */
export interface ContractLifeStats {
  total_lives: number;
  active_lives: number;
  inactive_lives: number;
  substituted_lives: number;
  cancelled_lives: number;
  lives_contracted: number;
  lives_minimum: number | null;
  lives_maximum: number | null;
  available_slots: number;
  utilization_percentage: number;
}

/**
 * Evento de histórico de uma vida (auditoria)
 */
export interface ContractLifeHistoryEvent {
  id: number;
  contract_life_id: number;
  action: HistoryAction;
  changed_fields: Record<string, any> | null;
  old_values: Record<string, any> | null;
  new_values: Record<string, any> | null;
  changed_by: number | null;
  changed_by_name: string | null;
  changed_at: string; // ISO datetime
}

/**
 * Resposta do histórico completo de uma vida
 */
export interface ContractLifeHistory {
  contract_life_id: number;
  person_name: string;
  events: ContractLifeHistoryEvent[];
  total_events: number;
}

/**
 * Response da API ao adicionar/atualizar vida
 */
export interface ContractLifeMutationResponse {
  id?: number;
  person_id?: number;
  message: string;
  life_id?: number;
  updated_fields?: string[];
}

/**
 * Opções para callbacks de ações da tabela
 */
export interface ContractLivesTableCallbacks {
  onViewTimeline?: (life: ContractLife) => void;
  onSubstitute?: (life: ContractLife) => void;
  onEdit?: (life: ContractLife) => void;
  onDelete?: (life: ContractLife) => void;
  onAdd?: () => void;
}

/**
 * Dados do formulário de vida (usado no componente)
 */
export interface LifeFormData {
  person_id: number;
  person_name: string;
  start_date: string;
  end_date?: string;
  notes?: string;
  relationship_type?: RelationshipType;
}

/**
 * Props do componente ContractLivesManager
 */
export interface ContractLivesManagerProps {
  contractId?: number; // Se omitido, mostra vidas de todos os contratos
}

/**
 * Estado de erro de validação de negócio
 */
export interface ContractLifeValidationError {
  field: string;
  message: string;
  code:
    | "MIN_LIVES"
    | "MAX_LIVES"
    | "PERIOD_OVERLAP"
    | "INVALID_DATE"
    | "SUBSTITUTION_NOT_ALLOWED";
}
