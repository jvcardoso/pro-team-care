"""
Menu Schemas - Presentation Layer
Schemas Pydantic para endpoints FastAPI do sistema de menus
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator


class MenuTypeSchema(str, Enum):
    """Schema para tipos de menu"""

    FOLDER = "folder"
    PAGE = "page"
    EXTERNAL_LINK = "external_link"
    SEPARATOR = "separator"


class MenuStatusSchema(str, Enum):
    """Schema para status do menu"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class MenuCreateSchema(BaseModel):
    """Schema para criação de menu"""

    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    name: str = Field(..., min_length=1, max_length=100, description="Nome do menu")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Identificador único (URL-friendly)",
    )
    url: Optional[str] = Field(None, max_length=255, description="URL de destino")
    route_name: Optional[str] = Field(
        None, max_length=100, description="Nome da rota (frontend)"
    )
    route_params: Optional[str] = Field(
        None, max_length=255, description="Parâmetros da rota JSON"
    )
    icon: Optional[str] = Field(
        None, max_length=50, description="Classe do ícone (ex: fas fa-home)"
    )
    menu_type: MenuTypeSchema = Field(MenuTypeSchema.PAGE, description="Tipo do menu")
    permission_name: Optional[str] = Field(
        None, max_length=100, description="Nome da permissão necessária"
    )
    company_specific: bool = Field(False, description="Menu específico de empresa")
    establishment_specific: bool = Field(
        False, description="Menu específico de estabelecimento"
    )
    badge_text: Optional[str] = Field(None, max_length=20, description="Texto do badge")
    badge_color: Optional[str] = Field(None, max_length=20, description="Cor do badge")
    css_class: Optional[str] = Field(
        None, max_length=100, description="Classe CSS customizada"
    )
    description: Optional[str] = Field(
        None, max_length=255, description="Descrição do menu"
    )
    help_text: Optional[str] = Field(None, max_length=500, description="Texto de ajuda")
    keywords: List[str] = Field(
        default_factory=list, description="Palavras-chave para busca"
    )
    is_visible: bool = Field(True, description="Menu visível no sistema")
    visible_in_menu: bool = Field(True, description="Visível na navegação")

    @validator("slug")
    def validate_slug(cls, v):
        """Validar formato do slug"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Slug deve conter apenas letras, números, hífens e underscores"
            )
        return v.lower()

    @validator("keywords")
    def validate_keywords(cls, v):
        """Validar palavras-chave"""
        if v and len(v) > 10:
            raise ValueError("Máximo de 10 palavras-chave permitidas")
        return [keyword.strip().lower() for keyword in v if keyword.strip()]

    @validator("badge_color")
    def validate_badge_color(cls, v):
        """Validar cor do badge"""
        if v:
            valid_colors = [
                "primary",
                "secondary",
                "success",
                "danger",
                "warning",
                "info",
                "light",
                "dark",
                "red",
                "green",
                "blue",
                "yellow",
            ]
            if v not in valid_colors:
                raise ValueError(f'Cor deve ser uma das: {", ".join(valid_colors)}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Relatórios",
                "slug": "relatorios",
                "url": "/relatorios",
                "icon": "fas fa-chart-bar",
                "menu_type": "page",
                "description": "Módulo de relatórios gerenciais",
                "keywords": ["relatorios", "graficos", "dados"],
                "badge_text": "NEW",
                "badge_color": "success",
                "is_visible": True,
                "visible_in_menu": True,
            }
        }
    )


class MenuUpdateSchema(BaseModel):
    """Schema para atualização de menu"""

    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    url: Optional[str] = Field(None, max_length=255)
    route_name: Optional[str] = Field(None, max_length=100)
    route_params: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    menu_type: Optional[MenuTypeSchema] = None
    status: Optional[MenuStatusSchema] = None
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

    @validator("slug")
    def validate_slug(cls, v):
        """Validar formato do slug"""
        if v and not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Slug deve conter apenas letras, números, hífens e underscores"
            )
        return v.lower() if v else v

    @validator("keywords")
    def validate_keywords(cls, v):
        """Validar palavras-chave"""
        if v and len(v) > 10:
            raise ValueError("Máximo de 10 palavras-chave permitidas")
        return [keyword.strip().lower() for keyword in v if keyword.strip()] if v else v

    @validator("badge_color")
    def validate_badge_color(cls, v):
        """Validar cor do badge"""
        if v:
            valid_colors = [
                "primary",
                "secondary",
                "success",
                "danger",
                "warning",
                "info",
                "light",
                "dark",
                "red",
                "green",
                "blue",
                "yellow",
            ]
            if v not in valid_colors:
                raise ValueError(f'Cor deve ser uma das: {", ".join(valid_colors)}')
        return v


class MenuListSchema(BaseModel):
    """Schema para listagem de menus"""

    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    level: int
    sort_order: int
    menu_type: MenuTypeSchema
    status: MenuStatusSchema
    is_visible: bool
    visible_in_menu: bool
    permission_name: Optional[str]
    has_children: bool = Field(False, description="Possui filhos")
    children_count: int = Field(0, description="Total de filhos")
    full_path_name: Optional[str] = Field(
        None, description="Caminho completo (Pai > Filho)"
    )
    icon: Optional[str]
    badge_text: Optional[str]
    badge_color: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class MenuDetailedSchema(MenuListSchema):
    """Schema completo do menu"""

    url: Optional[str]
    route_name: Optional[str]
    route_params: Optional[str]
    company_specific: bool
    establishment_specific: bool
    css_class: Optional[str]
    description: Optional[str]
    help_text: Optional[str]
    keywords: List[str] = Field(default_factory=list)
    id_path: List[int] = Field(
        default_factory=list, description="Caminho de IDs até a raiz"
    )
    deleted_at: Optional[datetime] = None

    # Navegação (opcional)
    parent: Optional["MenuListSchema"] = Field(None, description="Menu pai")
    children: List["MenuListSchema"] = Field(
        default_factory=list, description="Menus filhos diretos"
    )
    siblings: List["MenuListSchema"] = Field(
        default_factory=list, description="Menus no mesmo nível"
    )


class MenuTreeItemSchema(BaseModel):
    """Item da árvore hierárquica"""

    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    url: Optional[str]
    icon: Optional[str]
    level: int
    sort_order: int
    menu_type: MenuTypeSchema
    badge_text: Optional[str]
    badge_color: Optional[str]
    has_permission: bool = Field(True, description="Se usuário tem permissão")
    is_accessible: bool = Field(True, description="Se está acessível no contexto")
    children: List["MenuTreeItemSchema"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MenuTreeResponseSchema(BaseModel):
    """Resposta da árvore de menus"""

    user_id: Optional[int] = Field(None, description="ID do usuário (se aplicável)")
    context_type: str = Field(
        ..., description="Contexto atual (system/company/establishment)"
    )
    context_id: Optional[int] = Field(None, description="ID do contexto específico")
    total_menus: int = Field(..., description="Total de menus na árvore")
    root_menus: int = Field(..., description="Total de menus raiz")
    max_depth: int = Field(..., description="Profundidade máxima da árvore")
    tree: List[MenuTreeItemSchema] = Field(..., description="Árvore hierárquica")
    cache_hit: bool = Field(False, description="Se foi servido do cache")
    load_time_ms: int = Field(..., description="Tempo de carregamento em ms")
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp da geração"
    )


class ReorderRequestSchema(BaseModel):
    """Schema para requisição de reordenação"""

    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    menu_orders: List[Dict[str, int]] = Field(
        ..., description="Lista de {menu_id, sort_order}", min_items=1
    )

    @validator("menu_orders")
    def validate_menu_orders(cls, v):
        """Validar ordens dos menus"""
        if not v:
            raise ValueError("Lista de ordens não pode estar vazia")

        menu_ids = set()
        sort_orders = set()

        for item in v:
            if "menu_id" not in item or "sort_order" not in item:
                raise ValueError("Cada item deve ter menu_id e sort_order")

            menu_id = item["menu_id"]
            sort_order = item["sort_order"]

            if not isinstance(menu_id, int) or menu_id <= 0:
                raise ValueError("menu_id deve ser um inteiro positivo")

            if not isinstance(sort_order, int) or sort_order < 0:
                raise ValueError("sort_order deve ser um inteiro não-negativo")

            if menu_id in menu_ids:
                raise ValueError(f"menu_id {menu_id} duplicado")

            if sort_order in sort_orders:
                raise ValueError(f"sort_order {sort_order} duplicado")

            menu_ids.add(menu_id)
            sort_orders.add(sort_order)

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_id": None,
                "menu_orders": [
                    {"menu_id": 1, "sort_order": 1},
                    {"menu_id": 2, "sort_order": 2},
                    {"menu_id": 3, "sort_order": 3},
                ],
            }
        }
    )


class MenuSearchRequestSchema(BaseModel):
    """Schema para requisição de busca"""

    query: str = Field(..., min_length=2, max_length=100, description="Termo de busca")
    context_type: str = Field("system", description="Contexto da busca")
    context_id: Optional[int] = Field(None, description="ID do contexto específico")
    include_inactive: bool = Field(False, description="Incluir menus inativos")
    limit: int = Field(20, ge=1, le=100, description="Máximo de resultados")


class MenuSearchResultSchema(BaseModel):
    """Schema para resultado de busca"""

    id: int
    name: str
    slug: str
    url: Optional[str]
    full_path_name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    level: int
    menu_type: MenuTypeSchema
    status: MenuStatusSchema
    match_score: float = Field(description="Score de relevância da busca")
    match_reason: str = Field(description="Razão do match (name, description, etc.)")

    model_config = ConfigDict(from_attributes=True)


class MenuStatisticsSchema(BaseModel):
    """Schema para estatísticas de menus"""

    total_menus: int
    active_menus: int
    inactive_menus: int
    draft_menus: int
    menus_by_level: Dict[str, int] = Field(description="Quantidade por nível")
    menus_by_type: Dict[str, int] = Field(description="Quantidade por tipo")
    menus_with_permissions: int
    company_specific_menus: int
    establishment_specific_menus: int
    root_menus: int
    max_depth: int
    avg_children_per_menu: float
    most_used_icons: List[Dict[str, Any]] = Field(
        default_factory=list, description="Ícones mais utilizados"
    )
    recent_activity: Dict[str, int] = Field(
        default_factory=dict, description="Atividade recente"
    )

    model_config = ConfigDict(from_attributes=True)


class BulkUpdateRequestSchema(BaseModel):
    """Schema para atualização em lote"""

    menu_ids: List[int] = Field(..., min_items=1, description="IDs dos menus")
    status: Optional[MenuStatusSchema] = None
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None

    @validator("menu_ids")
    def validate_menu_ids(cls, v):
        """Validar IDs dos menus"""
        if not v:
            raise ValueError("Lista de IDs não pode estar vazia")
        if len(set(v)) != len(v):
            raise ValueError("IDs duplicados não são permitidos")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"menu_ids": [1, 2, 3], "status": "active", "is_visible": True}
        }
    )


class MenuValidationErrorSchema(BaseModel):
    """Schema para erros de validação"""

    field: str
    message: str
    code: str


class MenuOperationResultSchema(BaseModel):
    """Schema para resultado de operações"""

    success: bool
    message: str
    menu_id: Optional[int] = None
    errors: List[MenuValidationErrorSchema] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class MenuHealthSchema(BaseModel):
    """Schema para health check dos menus"""

    service: str = Field(..., description="Nome do serviço")
    status: str = Field(..., description="Status do serviço")
    version: str = Field(..., description="Versão do serviço")
    cache_status: Dict[str, Any] = Field(..., description="Status do cache")
    repository_status: str = Field(..., description="Status do repository")
    total_menus: int = Field(..., description="Total de menus no sistema")
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Métricas de performance"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class MenuExportRequestSchema(BaseModel):
    """Schema para exportação de menus"""

    format: str = Field("json", description="Formato de exportação (json, csv, xlsx)")
    include_hierarchy: bool = Field(True, description="Incluir estrutura hierárquica")
    include_inactive: bool = Field(False, description="Incluir menus inativos")
    context_type: Optional[str] = Field(None, description="Filtrar por contexto")

    @validator("format")
    def validate_format(cls, v):
        """Validar formato de exportação"""
        valid_formats = ["json", "csv", "xlsx"]
        if v not in valid_formats:
            raise ValueError(f'Formato deve ser um dos: {", ".join(valid_formats)}')
        return v


class MenuImportRequestSchema(BaseModel):
    """Schema para importação de menus"""

    data: List[Dict[str, Any]] = Field(..., description="Dados dos menus para importar")
    mode: str = Field(
        "create", description="Modo de importação (create, update, upsert)"
    )
    validate_hierarchy: bool = Field(
        True, description="Validar hierarquia durante importação"
    )

    @validator("mode")
    def validate_mode(cls, v):
        """Validar modo de importação"""
        valid_modes = ["create", "update", "upsert"]
        if v not in valid_modes:
            raise ValueError(f'Modo deve ser um dos: {", ".join(valid_modes)}')
        return v


class MenuBreadcrumbSchema(BaseModel):
    """Schema para breadcrumbs"""

    id: int
    name: str
    slug: str
    url: Optional[str]
    level: int

    model_config = ConfigDict(from_attributes=True)


class MenuPathSchema(BaseModel):
    """Schema para caminho do menu"""

    menu_id: int
    breadcrumbs: List[MenuBreadcrumbSchema]
    total_levels: int

    model_config = ConfigDict(from_attributes=True)


# Configurar referências forward
MenuDetailedSchema.model_rebuild()
MenuTreeItemSchema.model_rebuild()


# Schemas de resposta HTTP padronizados
class MenuListResponse(BaseModel):
    """Resposta padrão para listagem"""

    data: List[MenuListSchema]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class MenuSearchResponse(BaseModel):
    """Resposta padrão para busca"""

    data: List[MenuSearchResultSchema]
    query: str
    total: int
    execution_time_ms: int


class MenuErrorResponse(BaseModel):
    """Resposta padrão para erros"""

    error: bool = True
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
