from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .company import Address, Email, Phone


class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class PersonType(str, Enum):
    PF = "PF"  # Pessoa Física
    PJ = "PJ"  # Pessoa Jurídica


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    NOT_INFORMED = "not_informed"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    STABLE_UNION = "stable_union"
    NOT_INFORMED = "not_informed"


class PersonStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


# ==========================================
# BASE SCHEMAS
# ==========================================


class ClientBase(BaseModel):
    establishment_id: int = Field(..., gt=0, description="ID do estabelecimento")
    client_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Código único do cliente dentro do estabelecimento",
    )
    status: ClientStatus = Field(ClientStatus.ACTIVE, description="Status do cliente")

    @field_validator("client_code")
    @classmethod
    def validate_client_code(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) < 2:
                raise ValueError("Client code deve ter pelo menos 2 caracteres")
            return v.upper()
        return v


class PersonBaseForClient(BaseModel):
    name: str = Field(
        ..., min_length=2, max_length=200, description="Nome completo ou Razão Social"
    )
    trade_name: Optional[str] = Field(
        None, max_length=200, description="Nome social ou Nome Fantasia"
    )
    tax_id: str = Field(
        ...,
        min_length=11,
        max_length=18,  # Allow formatted input (max 18 chars for CNPJ with formatting)
        description="CPF (11 dígitos) ou CNPJ (14 dígitos), com ou sem máscara",
    )
    secondary_tax_id: Optional[str] = Field(
        None, max_length=20, description="RG ou Inscrição Estadual"
    )
    person_type: PersonType = Field(..., description="Tipo de pessoa: PF ou PJ")
    birth_date: Optional[datetime] = Field(None, description="Data de nascimento")
    gender: Optional[Gender] = Field(None, description="Gênero")
    marital_status: Optional[MaritalStatus] = Field(None, description="Estado civil")
    occupation: Optional[str] = Field(
        None, max_length=100, description="Ocupação/Profissão"
    )

    # Campos específicos para PJ
    incorporation_date: Optional[datetime] = Field(
        None, description="Data de constituição"
    )
    tax_regime: Optional[str] = Field(
        None, max_length=50, description="Regime tributário"
    )
    legal_nature: Optional[str] = Field(
        None, max_length=100, description="Natureza jurídica"
    )
    municipal_registration: Optional[str] = Field(
        None, max_length=20, description="Inscrição municipal"
    )
    website: Optional[str] = Field(None, description="Website da empresa")

    status: PersonStatus = Field(PersonStatus.ACTIVE, description="Status da pessoa")
    description: Optional[str] = Field(None, description="Observações gerais")

    # Metadados LGPD
    lgpd_consent_version: Optional[str] = Field(
        None, max_length=10, description="Versão do consentimento LGPD"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadados adicionais em JSON"
    )

    @field_validator("tax_id")
    @classmethod
    def validate_tax_id(cls, v):
        import re

        # Remove caracteres não numéricos
        clean_tax_id = re.sub(r"\D", "", v)

        if len(clean_tax_id) == 11:
            # CPF - validar formato básico
            if not clean_tax_id.isdigit():
                raise ValueError("CPF deve conter apenas números")
            return clean_tax_id
        elif len(clean_tax_id) == 14:
            # CNPJ - validar formato básico
            if not clean_tax_id.isdigit():
                raise ValueError("CNPJ deve conter apenas números")
            return clean_tax_id
        else:
            raise ValueError("tax_id deve ter 11 dígitos (CPF) ou 14 dígitos (CNPJ)")

    @field_validator("person_type")
    @classmethod
    def validate_person_type_with_tax_id(cls, v, info):
        if "tax_id" in info.data:
            import re

            clean_tax_id = re.sub(r"\D", "", info.data["tax_id"])

            if len(clean_tax_id) == 11 and v != PersonType.PF:
                raise ValueError("CPF (11 dígitos) deve ser usado com person_type='PF'")
            elif len(clean_tax_id) == 14 and v != PersonType.PJ:
                raise ValueError(
                    "CNPJ (14 dígitos) deve ser usado com person_type='PJ'"
                )

        return v


class PersonDetailed(PersonBaseForClient):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# LIST SCHEMAS
# ==========================================


class ClientListParams(BaseModel):
    establishment_id: Optional[int] = Field(
        None, description="Filtrar por estabelecimento"
    )
    status: Optional[ClientStatus] = Field(None, description="Filtrar por status")
    person_type: Optional[PersonType] = Field(
        None, description="Filtrar por tipo de pessoa"
    )
    search: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Buscar por nome ou CPF/CNPJ"
    )
    page: int = Field(1, ge=1, description="Número da página")
    size: int = Field(10, ge=1, le=100, description="Itens por página")


class ClientSimple(BaseModel):
    id: int
    person_id: int
    establishment_id: int
    client_code: Optional[str]
    status: ClientStatus
    created_at: datetime

    # Dados básicos da pessoa
    name: str
    tax_id: str
    person_type: PersonType


class ClientDetailed(ClientSimple):
    updated_at: Optional[datetime] = None

    # Dados completos da pessoa
    person: PersonDetailed

    # Dados do estabelecimento
    establishment_name: str
    establishment_code: str
    establishment_type: str
    company_id: int
    company_name: str

    # Contatos (relacionamentos polimórficos)
    phones: List[Phone] = []
    emails: List[Email] = []
    addresses: List[Address] = []


class ClientListResponse(BaseModel):
    clients: List[ClientDetailed]
    total: int
    page: int
    size: int
    pages: int


# ==========================================
# CREATE SCHEMAS
# ==========================================


class ClientCreate(ClientBase):
    person: Optional[PersonBaseForClient] = Field(
        None, description="Dados da pessoa (opcional se existing_person_id fornecido)"
    )
    existing_person_id: Optional[int] = Field(
        None, gt=0, description="ID de pessoa existente para reutilizar (opcional)"
    )

    @field_validator("existing_person_id")
    @classmethod
    def validate_mutual_exclusion(cls, v, info):
        if v and info.data.get("person"):
            raise ValueError("Forneça 'person' OU 'existing_person_id', não ambos")
        if not v and not info.data.get("person"):
            raise ValueError("É necessário fornecer 'person' ou 'existing_person_id'")
        return v


# ==========================================
# UPDATE SCHEMAS
# ==========================================


class ClientUpdate(BaseModel):
    client_code: Optional[str] = Field(
        None, max_length=50, description="Código do cliente"
    )
    status: Optional[ClientStatus] = Field(None, description="Status do cliente")


class ClientUpdateComplete(ClientUpdate):
    person: Optional[PersonBaseForClient] = Field(
        None, description="Dados da pessoa para atualizar"
    )


# ==========================================
# VALIDATION SCHEMAS
# ==========================================


class ClientValidationResponse(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = []


class ClientExistingCheckResponse(BaseModel):
    exists_in_establishment: bool
    existing_client: Optional[ClientDetailed] = None
    person_exists_globally: bool
    existing_person: Optional[Dict[str, Any]] = None
    person_type: str
    other_establishments: List[Dict[str, Any]] = []


# ==========================================
# REORDER SCHEMA
# ==========================================


class ClientReorderRequest(BaseModel):
    establishment_id: int = Field(..., gt=0, description="ID do estabelecimento")
    client_orders: List[Dict[str, int]] = Field(
        ..., description="Lista de objetos {id, order} com nova ordenação"
    )

    @field_validator("client_orders")
    @classmethod
    def validate_orders(cls, v):
        if not v:
            raise ValueError("Lista de ordenação não pode estar vazia")

        ids = [item.get("id") for item in v]
        orders = [item.get("order") for item in v]

        if None in ids or None in orders:
            raise ValueError("Todos os itens devem ter 'id' e 'order'")

        if len(set(ids)) != len(ids):
            raise ValueError("IDs duplicados na lista")

        if len(set(orders)) != len(orders):
            raise ValueError("Orders duplicados na lista")

        return v


# ==========================================
# CONFIGURATION
# ==========================================


# Configure all models for ORM mode
for model_class in [
    ClientSimple,
    ClientDetailed,
    PersonDetailed,
    ClientListResponse,
    ClientValidationResponse,
]:
    model_class.model_config = ConfigDict(from_attributes=True)
