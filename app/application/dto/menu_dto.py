"""
Menu DTOs - Application Layer
Data Transfer Objects para casos de uso de Menus
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.domain.entities.menu import MenuType, MenuStatus


class MenuCreateDTO(BaseModel):
    """DTO para criação de menu"""
    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    name: str = Field(..., min_length=1, max_length=100, description="Nome do menu")
    slug: str = Field(..., min_length=1, max_length=50, 
                     description="Identificador único (URL-friendly)")
    url: Optional[str] = Field(None, max_length=255, description="URL de destino")
    route_name: Optional[str] = Field(None, max_length=100, description="Nome da rota (frontend)")
    route_params: Optional[str] = Field(None, max_length=255, description="Parâmetros da rota JSON")
    icon: Optional[str] = Field(None, max_length=50, description="Classe do ícone (ex: fas fa-home)")
    menu_type: MenuType = Field(MenuType.PAGE, description="Tipo do menu")
    permission_name: Optional[str] = Field(None, max_length=100, 
                                          description="Nome da permissão necessária")
    company_specific: bool = Field(False, description="Menu específico de empresa")
    establishment_specific: bool = Field(False, description="Menu específico de estabelecimento")
    badge_text: Optional[str] = Field(None, max_length=20, description="Texto do badge")
    badge_color: Optional[str] = Field(None, max_length=20, description="Cor do badge")
    css_class: Optional[str] = Field(None, max_length=100, description="Classe CSS customizada")
    description: Optional[str] = Field(None, max_length=255, description="Descrição do menu")
    help_text: Optional[str] = Field(None, max_length=500, description="Texto de ajuda")
    keywords: List[str] = Field(default_factory=list, description="Palavras-chave para busca")
    is_visible: bool = Field(True, description="Menu visível no sistema")
    visible_in_menu: bool = Field(True, description="Visível na navegação")
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug deve conter apenas letras, números, hífens e underscores')
        return v.lower()
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v and len(v) > 10:
            raise ValueError('Máximo de 10 palavras-chave permitidas')
        return [keyword.strip().lower() for keyword in v if keyword.strip()]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Relatórios",
                "slug": "relatorios", 
                "url": "/relatorios",
                "icon": "fas fa-chart-bar",
                "menu_type": "page",
                "description": "Módulo de relatórios gerenciais",
                "keywords": ["relatorios", "graficos", "dados"],
                "is_visible": True,
                "visible_in_menu": True
            }
        }


class MenuUpdateDTO(BaseModel):
    """DTO para atualização de menu"""
    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    url: Optional[str] = Field(None, max_length=255)
    route_name: Optional[str] = Field(None, max_length=100)
    route_params: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    menu_type: Optional[MenuType] = None
    status: Optional[MenuStatus] = None
    permission_name: Optional[str] = Field(None, max_length=100)
    company_specific: Optional[bool] = None
    establishment_specific: Optional[bool] = None
    badge_text: Optional[str] = Field(None, max_length=20)
    badge_color: Optional[str] = Field(None, max_length=20)
    css_class: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    help_text: Optional[str] = Field(None, max_length=500)
    keywords: Optional[List[str]] = None
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, description="Ordem de exibição")
    
    @validator('slug')
    def validate_slug(cls, v):
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug deve conter apenas letras, números, hífens e underscores')
        return v.lower() if v else v
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if v and len(v) > 10:
            raise ValueError('Máximo de 10 palavras-chave permitidas')
        return [keyword.strip().lower() for keyword in v if keyword.strip()] if v else v


class MenuListDTO(BaseModel):
    """DTO para listagem de menus"""
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    level: int
    sort_order: int
    menu_type: MenuType
    status: MenuStatus
    is_visible: bool
    visible_in_menu: bool
    permission_name: Optional[str]
    has_children: bool = Field(False, description="Possui filhos")
    children_count: int = Field(0, description="Total de filhos")
    full_path_name: Optional[str] = Field(None, description="Caminho completo (Pai > Filho)")
    icon: Optional[str]
    badge_text: Optional[str]
    badge_color: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True


class MenuDetailDTO(MenuListDTO):
    """DTO completo do menu"""
    url: Optional[str]
    route_name: Optional[str] 
    route_params: Optional[str]
    company_specific: bool
    establishment_specific: bool
    css_class: Optional[str]
    description: Optional[str]
    help_text: Optional[str]
    keywords: List[str] = Field(default_factory=list)
    id_path: List[int] = Field(default_factory=list, description="Caminho de IDs até a raiz")
    deleted_at: Optional[datetime] = None
    
    # Navegação (opcional, pode ser populado conforme necessário)
    parent: Optional['MenuListDTO'] = Field(None, description="Menu pai")
    children: List['MenuListDTO'] = Field(default_factory=list, description="Menus filhos diretos")
    siblings: List['MenuListDTO'] = Field(default_factory=list, description="Menus no mesmo nível")


class MenuTreeItemDTO(BaseModel):
    """Item da árvore hierárquica"""
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    url: Optional[str]
    icon: Optional[str]
    level: int
    sort_order: int
    menu_type: MenuType
    badge_text: Optional[str]
    badge_color: Optional[str]
    has_permission: bool = Field(True, description="Se usuário tem permissão")
    is_accessible: bool = Field(True, description="Se está acessível no contexto")
    children: List['MenuTreeItemDTO'] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class MenuTreeResponseDTO(BaseModel):
    """Resposta da árvore de menus"""
    user_id: Optional[int] = Field(None, description="ID do usuário (se aplicável)")
    context_type: str = Field(..., description="Contexto atual (system/company/establishment)")
    context_id: Optional[int] = Field(None, description="ID do contexto específico")
    total_menus: int = Field(..., description="Total de menus na árvore")
    root_menus: int = Field(..., description="Total de menus raiz")
    max_depth: int = Field(..., description="Profundidade máxima da árvore")
    tree: List[MenuTreeItemDTO] = Field(..., description="Árvore hierárquica")
    cache_hit: bool = Field(False, description="Se foi servido do cache")
    load_time_ms: int = Field(..., description="Tempo de carregamento em ms")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp da geração")


class ReorderRequestDTO(BaseModel):
    """DTO para requisição de reordenação de menus"""
    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    menu_orders: List[Dict[str, int]] = Field(
        ..., 
        description="Lista de {menu_id, sort_order}",
        min_items=1
    )
    
    @validator('menu_orders')
    def validate_menu_orders(cls, v):
        if not v:
            raise ValueError('Lista de ordens não pode estar vazia')
        
        menu_ids = set()
        sort_orders = set()
        
        for item in v:
            if 'menu_id' not in item or 'sort_order' not in item:
                raise ValueError('Cada item deve ter menu_id e sort_order')
            
            menu_id = item['menu_id']
            sort_order = item['sort_order']
            
            if not isinstance(menu_id, int) or menu_id <= 0:
                raise ValueError('menu_id deve ser um inteiro positivo')
            
            if not isinstance(sort_order, int) or sort_order < 0:
                raise ValueError('sort_order deve ser um inteiro não-negativo')
            
            if menu_id in menu_ids:
                raise ValueError(f'menu_id {menu_id} duplicado')
            
            if sort_order in sort_orders:
                raise ValueError(f'sort_order {sort_order} duplicado')
            
            menu_ids.add(menu_id)
            sort_orders.add(sort_order)
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "parent_id": None,
                "menu_orders": [
                    {"menu_id": 1, "sort_order": 1},
                    {"menu_id": 2, "sort_order": 2},
                    {"menu_id": 3, "sort_order": 3}
                ]
            }
        }


class MenuSearchRequestDTO(BaseModel):
    """DTO para requisição de busca de menus"""
    query: str = Field(..., min_length=2, max_length=100, description="Termo de busca")
    context_type: str = Field("system", description="Contexto da busca")
    context_id: Optional[int] = Field(None, description="ID do contexto específico")
    include_inactive: bool = Field(False, description="Incluir menus inativos")
    limit: int = Field(20, ge=1, le=100, description="Máximo de resultados")


class MenuSearchResultDTO(BaseModel):
    """DTO para resultado de busca"""
    id: int
    name: str
    slug: str
    url: Optional[str]
    full_path_name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    level: int
    menu_type: MenuType
    status: MenuStatus
    match_score: float = Field(description="Score de relevância da busca")
    match_reason: str = Field(description="Razão do match (name, description, etc.)")


class MenuStatisticsDTO(BaseModel):
    """DTO para estatísticas de menus"""
    total_menus: int
    active_menus: int
    inactive_menus: int
    draft_menus: int
    menus_by_level: Dict[int, int] = Field(description="Quantidade por nível")
    menus_by_type: Dict[str, int] = Field(description="Quantidade por tipo")
    menus_with_permissions: int
    company_specific_menus: int
    establishment_specific_menus: int
    root_menus: int
    max_depth: int
    avg_children_per_menu: float
    most_used_icons: List[Dict[str, Any]] = Field(description="Ícones mais utilizados")
    recent_activity: Dict[str, int] = Field(description="Atividade recente (últimos 7 dias)")


class BulkUpdateRequestDTO(BaseModel):
    """DTO para atualização em lote"""
    menu_ids: List[int] = Field(..., min_items=1, description="IDs dos menus")
    status: Optional[MenuStatus] = None
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None
    
    @validator('menu_ids')
    def validate_menu_ids(cls, v):
        if not v:
            raise ValueError('Lista de IDs não pode estar vazia')
        if len(set(v)) != len(v):
            raise ValueError('IDs duplicados não são permitidos')
        return v


class MenuValidationErrorDTO(BaseModel):
    """DTO para erros de validação"""
    field: str
    message: str
    code: str


class MenuOperationResultDTO(BaseModel):
    """DTO para resultado de operações"""
    success: bool
    message: str
    menu_id: Optional[int] = None
    errors: List[MenuValidationErrorDTO] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# Configurar referências forward
MenuDetailDTO.model_rebuild()
MenuTreeItemDTO.model_rebuild()