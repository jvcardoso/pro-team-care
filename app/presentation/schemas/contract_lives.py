"""
Schemas para gestão de vidas em contratos (Contract Lives)
Valida dados de entrada/saída da API de vidas vinculadas a contratos
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ContractLifeBase(BaseModel):
    """Schema base para Contract Life"""

    start_date: date = Field(
        ..., description="Data de início da vida no contrato (YYYY-MM-DD)"
    )
    end_date: Optional[date] = Field(
        None, description="Data de fim da vida no contrato (opcional)"
    )
    relationship_type: Literal[
        "TITULAR", "DEPENDENTE", "FUNCIONARIO", "BENEFICIARIO"
    ] = Field(..., description="Tipo de relacionamento com o contrato")
    notes: Optional[str] = Field(
        None, max_length=500, description="Observações sobre a vida"
    )

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que end_date é posterior a start_date"""
        if v and "start_date" in info.data:
            start_date = info.data["start_date"]
            if v < start_date:
                raise ValueError(
                    f"end_date ({v}) deve ser posterior ou igual a start_date ({start_date})"
                )
        return v


class ContractLifeCreate(ContractLifeBase):
    """Schema para criar uma nova vida no contrato"""

    person_name: str = Field(
        ..., min_length=3, max_length=200, description="Nome completo da pessoa"
    )
    allows_substitution: bool = Field(
        default=True, description="Se permite substituição futura"
    )

    @field_validator("person_name")
    @classmethod
    def validate_person_name(cls, v: str) -> str:
        """Valida e normaliza o nome da pessoa"""
        # Remove espaços extras e garante capitalização
        v = " ".join(v.strip().split())
        if not v:
            raise ValueError("Nome da pessoa não pode estar vazio")
        if len(v) < 3:
            raise ValueError("Nome da pessoa deve ter no mínimo 3 caracteres")
        return v


class ContractLifeUpdate(BaseModel):
    """Schema para atualizar uma vida existente"""

    end_date: Optional[date] = Field(
        None, description="Nova data de fim (para encerrar vida)"
    )
    status: Optional[
        Literal["active", "inactive", "substituted", "cancelled"]
    ] = Field(None, description="Novo status da vida")
    notes: Optional[str] = Field(
        None, max_length=500, description="Atualização de observações"
    )
    substitution_reason: Optional[str] = Field(
        None, max_length=100, description="Motivo da substituição"
    )

    @field_validator("status")
    @classmethod
    def validate_status_transition(cls, v: Optional[str]) -> Optional[str]:
        """Valida transições de status permitidas"""
        # Regras de negócio para transições de status
        valid_statuses = ["active", "inactive", "substituted", "cancelled"]
        if v and v not in valid_statuses:
            raise ValueError(f"Status inválido. Valores permitidos: {valid_statuses}")
        return v


class ContractLifeResponse(BaseModel):
    """Schema de resposta para uma vida do contrato"""

    id: int
    contract_id: int
    person_id: int
    person_name: str = Field(..., description="Nome da pessoa (JOIN com people)")
    person_cpf: str = Field(..., description="CPF da pessoa (JOIN com people)")
    start_date: date
    end_date: Optional[date]
    relationship_type: Literal["TITULAR", "DEPENDENTE", "FUNCIONARIO", "BENEFICIARIO"]
    status: Literal["active", "inactive", "substituted", "cancelled"]
    substitution_reason: Optional[str] = None
    allows_substitution: bool = Field(
        default=True, description="Se permite substituição"
    )
    primary_service_address: Optional[dict] = Field(
        None, description="Endereço principal de atendimento (JSON)"
    )
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None

    # Campos adicionais opcionais (para listagem global)
    contract_number: Optional[str] = Field(
        None, description="Número do contrato (para visualização global)"
    )
    client_name: Optional[str] = Field(
        None, description="Nome do cliente (para visualização global)"
    )

    class Config:
        from_attributes = True  # Permite converter SQLAlchemy models


class ContractLifeListParams(BaseModel):
    """Parâmetros para filtrar listagem de vidas"""

    status: Optional[Literal["active", "inactive", "substituted", "cancelled"]] = None
    relationship_type: Optional[
        Literal["TITULAR", "DEPENDENTE", "FUNCIONARIO", "BENEFICIARIO"]
    ] = None
    start_date_from: Optional[date] = Field(
        None, description="Filtro: data de início maior ou igual"
    )
    start_date_to: Optional[date] = Field(
        None, description="Filtro: data de início menor ou igual"
    )
    active_only: bool = Field(default=True, description="Mostrar apenas vidas ativas")


class ContractLifeStatsResponse(BaseModel):
    """Estatísticas de vidas de um contrato"""

    total_lives: int = Field(..., description="Total de vidas (todas)")
    active_lives: int = Field(..., description="Vidas ativas")
    inactive_lives: int = Field(..., description="Vidas inativas")
    substituted_lives: int = Field(..., description="Vidas substituídas")
    cancelled_lives: int = Field(..., description="Vidas canceladas")
    lives_contracted: int = Field(..., description="Vidas contratadas (meta)")
    lives_minimum: Optional[int] = Field(None, description="Vidas mínimas (contrato)")
    lives_maximum: Optional[int] = Field(None, description="Vidas máximas (contrato)")
    available_slots: int = Field(
        ..., description="Vagas disponíveis (contracted - active)"
    )
    utilization_percentage: float = Field(
        ..., description="Percentual de utilização (active/contracted * 100)"
    )


class ContractLifeHistoryEvent(BaseModel):
    """Evento de histórico de uma vida (para timeline)"""

    id: int
    contract_life_id: int
    action: Literal["created", "updated", "substituted", "cancelled"]
    changed_fields: Optional[dict] = Field(None, description="Campos alterados (JSON)")
    old_values: Optional[dict] = Field(None, description="Valores antigos (JSON)")
    new_values: Optional[dict] = Field(None, description="Valores novos (JSON)")
    changed_by: Optional[int] = Field(None, description="ID do usuário que alterou")
    changed_by_name: Optional[str] = Field(None, description="Nome do usuário")
    changed_at: datetime

    class Config:
        from_attributes = True


class ContractLifeHistoryResponse(BaseModel):
    """Resposta com histórico completo de uma vida"""

    contract_life_id: int
    person_name: str
    events: list[ContractLifeHistoryEvent]
    total_events: int
