"""
Schemas para sistema de códigos de programas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProgramCodeBase(BaseModel):
    """Base schema para código de programa"""

    shortcode: str = Field(
        ..., min_length=6, max_length=10, description="Código curto (ex: em0001)"
    )
    module_code: str = Field(
        ..., min_length=2, max_length=2, description="Sigla do módulo (ex: EM)"
    )
    program_type: str = Field(
        ..., min_length=2, max_length=2, description="Tipo de programa (ex: 00)"
    )
    label: str = Field(..., max_length=100, description="Nome da tela")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    route: str = Field(..., max_length=255, description="Rota no frontend")
    icon: Optional[str] = Field(None, max_length=50, description="Nome do ícone Lucide")
    search_tokens: List[str] = Field(
        default_factory=list, description="Tokens para busca"
    )
    required_permission: Optional[str] = Field(None, description="Permissão necessária")


class ProgramCodeCreate(ProgramCodeBase):
    """Schema para criar código de programa"""

    pass


class ProgramCodeUpdate(BaseModel):
    """Schema para atualizar código de programa"""

    label: Optional[str] = None
    description: Optional[str] = None
    route: Optional[str] = None
    icon: Optional[str] = None
    search_tokens: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProgramCodeResponse(ProgramCodeBase):
    """Schema de resposta de código de programa"""

    id: int
    menu_id: Optional[int] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class QuickSearchRequest(BaseModel):
    """Request para busca rápida"""

    query: str = Field(
        ..., min_length=1, max_length=100, description="Termo de busca ou código"
    )


class QuickSearchResult(BaseModel):
    """Resultado individual de busca"""

    shortcode: str
    label: str
    description: Optional[str] = None
    route: str
    icon: Optional[str] = None
    module_code: str
    program_type: str
    match_type: str = Field(..., description="exact|fuzzy|token")
    relevance_score: float = Field(default=0.0, description="Score de relevância (0-1)")


class QuickSearchResponse(BaseModel):
    """Resposta de busca rápida"""

    query: str
    execution_type: str = Field(..., description="direct|select")
    results: List[QuickSearchResult]
    total_results: int
    search_time_ms: float


class ProgramCodeUsageRequest(BaseModel):
    """Request para registrar uso"""

    shortcode: str = Field(..., description="Código do programa acessado")
    user_id: Optional[int] = Field(None, description="ID do usuário (opcional)")


class ProgramCodeStatsResponse(BaseModel):
    """Estatísticas de uso"""

    total_codes: int
    active_codes: int
    most_used: List[QuickSearchResult]
    recently_used: List[QuickSearchResult]
