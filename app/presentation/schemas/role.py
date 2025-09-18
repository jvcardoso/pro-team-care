from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContextType(str, Enum):
    SYSTEM = "system"
    COMPANY = "company"
    ESTABLISHMENT = "establishment"


class RoleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ==========================================
# BASE SCHEMAS
# ==========================================


class RoleBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=125,
        description="Nome técnico do perfil (único)",
    )
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Nome exibido do perfil",
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Descrição detalhada do perfil"
    )
    level: int = Field(
        ...,
        ge=10,
        le=100,
        description="Nível hierárquico do perfil (10-100)",
    )
    context_type: ContextType = Field(
        ..., description="Contexto de aplicação do perfil"
    )
    is_active: bool = Field(True, description="Perfil ativo")
    settings: Optional[Dict[str, Any]] = Field(
        None, description="Configurações específicas do perfil"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Nome é obrigatório")
        # Convert to lowercase and replace spaces with underscores
        return v.strip().lower().replace(" ", "_")

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Nome de exibição é obrigatório")
        return v.strip()


# ==========================================
# CREATE SCHEMAS
# ==========================================


class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = Field(
        None, description="IDs das permissões a serem associadas"
    )


# ==========================================
# UPDATE SCHEMAS
# ==========================================


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=125)
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    level: Optional[int] = Field(None, ge=10, le=100)
    context_type: Optional[ContextType] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    permission_ids: Optional[List[int]] = Field(
        None, description="IDs das permissões a serem associadas"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Nome não pode ser vazio")
            return v.strip().lower().replace(" ", "_")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Nome de exibição não pode ser vazio")
            return v.strip()
        return v


# ==========================================
# RESPONSE SCHEMAS
# ==========================================


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    module: str
    action: str
    resource: str
    context_level: str
    is_active: bool


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    level: int
    context_type: str
    is_active: bool
    is_system_role: bool
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Relationships
    permissions: Optional[List[PermissionResponse]] = None


class RoleDetailed(RoleResponse):
    """Role with full permission details"""

    permissions: List[PermissionResponse] = []


# ==========================================
# LIST SCHEMAS
# ==========================================


class RoleListParams(BaseModel):
    context_type: Optional[ContextType] = None
    is_active: Optional[bool] = None
    is_system_role: Optional[bool] = None
    level_min: Optional[int] = Field(None, ge=10, le=100)
    level_max: Optional[int] = Field(None, ge=10, le=100)
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int
    page: int
    size: int
    total_pages: int


# ==========================================
# PERMISSION SCHEMAS
# ==========================================


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=125)
    display_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    module: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=50)
    resource: str = Field(..., min_length=1, max_length=50)
    context_level: ContextType = Field(...)
    is_active: bool = Field(True)


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=125)
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    module: Optional[str] = Field(None, min_length=1, max_length=50)
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    resource: Optional[str] = Field(None, min_length=1, max_length=50)
    context_level: Optional[ContextType] = None
    is_active: Optional[bool] = None


class PermissionListParams(BaseModel):
    module: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    context_level: Optional[ContextType] = None
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class PermissionListResponse(BaseModel):
    permissions: List[PermissionResponse]
    total: int
    page: int
    size: int
    total_pages: int


# ==========================================
# ROLE ASSIGNMENT SCHEMAS
# ==========================================


class RoleAssignmentCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    role_id: int = Field(..., gt=0)
    context_type: ContextType = Field(...)
    context_id: int = Field(..., gt=0)
    expires_at: Optional[datetime] = None


class RoleAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role_id: int
    context_type: str
    context_id: int
    status: str
    assigned_by_user_id: Optional[int] = None
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime

    # Relationships
    role: Optional[RoleResponse] = None
