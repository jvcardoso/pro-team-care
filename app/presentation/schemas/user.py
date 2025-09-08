from pydantic import BaseModel, Field, ConfigDict, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Importar schemas reutilizáveis de company
from .company import (
    PersonType, PersonStatus, PhoneType, LineType, EmailType, AddressType,
    PhoneCreate, Phone, EmailCreate, Email, 
    AddressCreate, Address
)


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    PENDING = "pending"


class NotificationFrequency(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    DISABLED = "disabled"


# ===== PERSON SCHEMAS (PF para usuários) =====

class PersonCreatePF(BaseModel):
    """Schema para criação de pessoa física (usuários)"""
    name: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    tax_id: str = Field(..., min_length=11, max_length=14, description="CPF (apenas números)")
    birth_date: Optional[date] = Field(None, description="Data de nascimento")
    gender: Optional[str] = Field(None, max_length=1, description="Gênero (M/F/O)")

    status: PersonStatus = Field(PersonStatus.ACTIVE, description="Status da pessoa")
    
    # Sempre PF para usuários
    person_type: PersonType = Field(PersonType.PF, description="Tipo de pessoa (sempre PF)")
    
    # Metadados opcionais
    description: Optional[str] = Field(None, max_length=2000, description="Observações/Descrição")
    
    @validator('tax_id')
    def validate_cpf(cls, v):
        """Validação básica de CPF"""
        if not v:
            raise ValueError("CPF é obrigatório")
        
        # Remover caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, v))
        
        if len(cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
        
        # Verificar sequências inválidas
        if cpf == cpf[0] * 11:
            raise ValueError("CPF não pode ser uma sequência de dígitos iguais")
            
        return cpf

    @validator('name')
    def validate_name(cls, v):
        """Validação de nome"""
        if not v or len(v.strip()) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        return v.strip().title()


class PersonDetailed(BaseModel):
    """Schema detalhado para pessoa (resposta da API)"""
    id: int
    name: str
    tax_id: str
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    person_type: PersonType
    status: PersonStatus
    description: Optional[str] = None  # Campo que existe no modelo People
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ===== ROLE SCHEMAS =====

class UserRoleDetailed(BaseModel):
    """Schema para roles de usuário"""
    id: int
    role_name: str
    context_type: str  # system, company, establishment
    context_id: Optional[int]
    context_name: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# ===== USER MAIN SCHEMAS =====

class UserCreate(BaseModel):
    """Schema para criação completa de usuário"""
    # Dados da pessoa (PF obrigatória)
    person: PersonCreatePF
    
    # Dados do usuário
    email_address: EmailStr = Field(..., description="Email único do usuário")
    password: str = Field(..., min_length=8, description="Senha (mín. 8 caracteres)")
    is_active: bool = Field(True, description="Usuário ativo")
    
    # Contatos opcionais
    phones: Optional[List[PhoneCreate]] = Field([], description="Telefones do usuário")
    emails: Optional[List[EmailCreate]] = Field([], description="Emails adicionais")
    addresses: Optional[List[AddressCreate]] = Field([], description="Endereços")
    
    # Configurações opcionais
    preferences: Optional[Dict[str, Any]] = Field({}, description="Preferências do usuário")
    notification_settings: Optional[Dict[str, Any]] = Field({}, description="Configurações de notificação")
    
    @validator('password')
    def validate_password(cls, v):
        """Validação de senha forte"""
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Senha deve conter pelo menos: 1 maiúscula, 1 minúscula e 1 número")
            
        return v


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    # Dados básicos (opcionais)
    person: Optional[PersonCreatePF] = None
    email_address: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    
    # Contatos (opcionais - substituição completa)
    phones: Optional[List[PhoneCreate]] = None
    emails: Optional[List[EmailCreate]] = None  
    addresses: Optional[List[AddressCreate]] = None
    
    # Configurações
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserPasswordChange(BaseModel):
    """Schema para alteração de senha"""
    current_password: Optional[str] = Field(None, description="Senha atual (obrigatória se não for admin)")
    new_password: str = Field(..., min_length=8, description="Nova senha")
    confirm_password: str = Field(..., description="Confirmação da nova senha")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Senhas não conferem")
        return v


class UserDetailed(BaseModel):
    """Schema detalhado completo para usuário"""
    # Dados básicos do usuário
    id: int
    person_id: int
    email_address: str
    email_verified_at: Optional[datetime]
    is_active: bool
    is_system_admin: bool
    last_login_at: Optional[datetime]
    
    # Configurações
    preferences: Optional[Dict[str, Any]]
    notification_settings: Optional[Dict[str, Any]]
    
    # Relacionamentos
    person: PersonDetailed
    phones: List[Phone] = []
    emails: List[Email] = []
    addresses: List[Address] = []
    roles: List[UserRoleDetailed] = []
    
    # Metadados
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Campos sensíveis NÃO incluídos por segurança
    # password, remember_token, two_factor_secret
    
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    """Schema otimizado para listagem de usuários"""
    id: int
    person_name: str  # do relacionamento person
    email_address: str
    is_active: bool
    is_system_admin: bool
    last_login_at: Optional[datetime]
    
    # Contadores úteis
    roles_count: int = 0
    phones_count: int = 0
    
    # Metadados
    created_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    """Schema para perfil público do usuário"""
    id: int
    name: str  # person.name
    email_address: str
    is_active: bool
    last_login_at: Optional[datetime]
    
    # Dados básicos da pessoa (sem CPF)
    gender: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# ===== RESPONSE SCHEMAS =====

class UserCreateResponse(BaseModel):
    """Resposta para criação de usuário"""
    user: UserDetailed
    message: str = "Usuário criado com sucesso"
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Resposta paginada para listagem de usuários"""
    users: List[UserList]
    total: int
    page: int
    size: int
    pages: int
    
    model_config = ConfigDict(from_attributes=True)


class UserCountResponse(BaseModel):
    """Resposta para contagem de usuários"""
    total: int
    active: int = 0
    inactive: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# ===== LEGACY COMPATIBILITY =====

# Manter compatibilidade com schemas existentes de auth
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Aliases para compatibilidade
User = UserDetailed
UserInDB = UserDetailed