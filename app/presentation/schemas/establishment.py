from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

class EstablishmentType(str, Enum):
    MATRIZ = "matriz"
    FILIAL = "filial"
    UNIDADE = "unidade"
    POSTO = "posto"

class EstablishmentCategory(str, Enum):
    CLINICA = "clinica"
    HOSPITAL = "hospital"
    LABORATORIO = "laboratorio"
    FARMACIA = "farmacia"
    CONSULTORIO = "consultorio"
    UPA = "upa"
    UBS = "ubs"
    OUTRO = "outro"

# ==========================================
# BASE SCHEMAS
# ==========================================

class EstablishmentBase(BaseModel):
    code: str = Field(..., max_length=50, description="Código único do estabelecimento dentro da empresa")
    type: EstablishmentType = Field(..., description="Tipo do estabelecimento")
    category: EstablishmentCategory = Field(..., description="Categoria do estabelecimento")
    is_active: bool = Field(True, description="Estabelecimento ativo")
    is_principal: bool = Field(False, description="Estabelecimento principal da empresa")
    settings: Optional[Dict[str, Any]] = Field(None, description="Configurações específicas")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Horários de funcionamento")
    service_areas: Optional[Dict[str, Any]] = Field(None, description="Áreas de serviço")

    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Code é obrigatório')
        if len(v.strip()) < 2:
            raise ValueError('Code deve ter pelo menos 2 caracteres')
        return v.strip().upper()

class PersonCreateForEstablishment(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nome do estabelecimento")
    tax_id: str = Field(..., min_length=11, max_length=18, description="CNPJ do estabelecimento")
    person_type: str = Field("PJ", description="Tipo de pessoa (sempre PJ)")
    status: str = Field("active", description="Status da pessoa")
    description: Optional[str] = Field(None, max_length=2000, description="Observações")

    @validator('tax_id')
    def validate_cnpj(cls, v):
        import re
        # Remove non-numeric characters
        cnpj = re.sub(r'\D', '', v)
        if len(cnpj) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        return cnpj

# ==========================================
# CREATE SCHEMAS
# ==========================================

class EstablishmentCreate(EstablishmentBase):
    company_id: int = Field(..., gt=0, description="ID da empresa pai")
    person: PersonCreateForEstablishment = Field(..., description="Dados da pessoa jurídica")

# ==========================================
# UPDATE SCHEMAS  
# ==========================================

class EstablishmentUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    type: Optional[EstablishmentType] = None
    category: Optional[EstablishmentCategory] = None
    is_active: Optional[bool] = None
    is_principal: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    operating_hours: Optional[Dict[str, Any]] = None
    service_areas: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = Field(None, ge=0)

    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('Code não pode ser vazio')
            if len(v.strip()) < 2:
                raise ValueError('Code deve ter pelo menos 2 caracteres')
            return v.strip().upper()
        return v

class PersonUpdateForEstablishment(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    tax_id: Optional[str] = Field(None, min_length=11, max_length=18)
    status: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)

    @validator('tax_id')
    def validate_cnpj(cls, v):
        if v is not None:
            import re
            cnpj = re.sub(r'\D', '', v)
            if len(cnpj) != 14:
                raise ValueError('CNPJ deve ter 14 dígitos')
            return cnpj
        return v

class EstablishmentUpdateComplete(EstablishmentUpdate):
    person: Optional[PersonUpdateForEstablishment] = None

# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class PersonDetailed(BaseModel):
    id: int
    name: str
    tax_id: str
    person_type: str
    status: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EstablishmentSimple(BaseModel):
    id: int
    person_id: int
    company_id: int
    code: str
    type: str
    category: str
    is_active: bool
    is_principal: bool
    display_order: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class EstablishmentDetailed(BaseModel):
    id: int
    person_id: int
    company_id: int
    code: str
    type: str
    category: str
    is_active: bool
    is_principal: bool
    display_order: int
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    operating_hours: Optional[Dict[str, Any]] = None
    service_areas: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relacionamentos
    person: Optional[PersonDetailed] = None
    company_name: Optional[str] = None
    company_tax_id: Optional[str] = None
    
    # Contadores
    user_count: Optional[int] = 0
    professional_count: Optional[int] = 0
    client_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# LIST SCHEMAS
# ==========================================

class EstablishmentListParams(BaseModel):
    company_id: Optional[int] = Field(None, gt=0, description="Filtrar por empresa")
    is_active: Optional[bool] = Field(None, description="Filtrar por status ativo")
    is_principal: Optional[bool] = Field(None, description="Filtrar estabelecimentos principais")
    type: Optional[EstablishmentType] = Field(None, description="Filtrar por tipo")
    category: Optional[EstablishmentCategory] = Field(None, description="Filtrar por categoria")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Buscar por nome ou código")
    page: int = Field(1, ge=1, description="Número da página")
    size: int = Field(10, ge=1, le=100, description="Itens por página")

class EstablishmentListResponse(BaseModel):
    establishments: List[EstablishmentDetailed]
    total: int
    page: int
    size: int
    pages: int

# ==========================================
# OPERATIONAL SCHEMAS  
# ==========================================

class EstablishmentReorderRequest(BaseModel):
    company_id: int = Field(..., gt=0)
    establishment_orders: List[Dict[str, int]] = Field(..., description="Lista de {id, order}")

    @validator('establishment_orders')
    def validate_orders(cls, v):
        if not v:
            raise ValueError('Lista de ordens não pode ser vazia')
        
        ids = [item.get('id') for item in v]
        orders = [item.get('order') for item in v]
        
        if None in ids or None in orders:
            raise ValueError('Cada item deve ter id e order')
            
        if len(set(ids)) != len(ids):
            raise ValueError('IDs duplicados na lista')
            
        if len(set(orders)) != len(orders):
            raise ValueError('Orders duplicadas na lista')
            
        return v

class EstablishmentValidationResponse(BaseModel):
    is_valid: bool
    error_message: str
    suggested_display_order: int

# ==========================================
# COMPANY RELATIONSHIP SCHEMAS
# ==========================================

class CompanySimpleForEstablishment(BaseModel):
    id: int
    name: str
    tax_id: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class EstablishmentWithCompany(EstablishmentDetailed):
    company: Optional[CompanySimpleForEstablishment] = None