"""
User Schemas - Modelos Pydantic para APIs de usuários
Integrados com ValidationService para validações robustas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base model for User"""

    email: EmailStr
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserCreate(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    person_id: int

    # User specific
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    """Schema for updating user data"""

    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user responses"""

    id: int
    email: str
    person_id: int
    is_active: bool
    is_admin: bool
    created_at: Any
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class UserCompleteResponse(BaseModel):
    """Complete user data with relationships"""

    # User data
    user_id: int
    user_email: str
    user_is_active: bool
    user_is_system_admin: bool
    user_company_id: Optional[int]
    user_created_at: datetime
    user_updated_at: Optional[datetime]

    # Person data
    person_id: int
    person_name: str
    person_tax_id: str
    person_is_active: bool
    person_created_at: datetime
    person_updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserHierarchicalResponse(BaseModel):
    """User data with hierarchical context"""

    user_id: int
    user_email: str
    user_is_active: bool
    user_is_system_admin: bool

    person_name: str
    person_tax_id: str
    establishment_name: Optional[str]
    establishment_type: Optional[str]
    role_name: Optional[str]
    permissions_count: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Paginated list of users"""

    items: List[UserCompleteResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_prev: bool
    has_next: bool


class RoleAssignment(BaseModel):
    """Schema for assigning roles to users"""

    user_id: int
    role_id: int
    context_type: str = Field(..., pattern="^(system|company|establishment)$")
    context_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class UserEstablishmentCreate(BaseModel):
    """Schema for creating user-establishment relationship"""

    user_id: int
    establishment_id: int
    role_id: Optional[int] = None
    is_primary: Optional[bool] = False
    permissions: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class UserEstablishmentResponse(BaseModel):
    """Response for user-establishment relationship"""

    id: int
    user_id: int
    establishment_id: int
    role_id: Optional[int]
    is_primary: bool
    status: str
    permissions: Optional[Dict[str, Any]]
    assigned_at: datetime
    expires_at: Optional[datetime]

    # Related data
    user_email: Optional[str]
    establishment_code: Optional[str]
    role_name: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ProfessionalCreate(BaseModel):
    """Schema for creating professional"""

    pf_person_id: int  # Person física (required)
    pj_person_id: Optional[int] = None  # Person jurídica (optional)
    establishment_id: int
    professional_code: Optional[str] = Field(None, max_length=50)
    specialties: Optional[List[str]] = None
    admission_date: Optional[datetime] = None


class ProfessionalResponse(BaseModel):
    """Response for professional data"""

    id: int
    pf_person_id: int
    pj_person_id: Optional[int]
    establishment_id: int
    professional_code: Optional[str]
    status: str
    specialties: Optional[List[str]]
    admission_date: Optional[datetime]
    termination_date: Optional[datetime]
    created_at: datetime

    # Related data
    pf_person_name: Optional[str]
    pj_person_name: Optional[str]
    establishment_code: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ClientCreate(BaseModel):
    """Schema for creating client"""

    person_id: int
    establishment_id: int
    client_code: Optional[str] = Field(None, max_length=50)


class ClientResponse(BaseModel):
    """Response for client data"""

    id: int
    person_id: int
    establishment_id: int
    client_code: Optional[str]
    status: str
    created_at: datetime

    # Related data
    person_name: Optional[str]
    person_tax_id: Optional[str]
    establishment_code: Optional[str]

    model_config = ConfigDict(from_attributes=True)
