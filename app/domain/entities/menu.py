"""
Menu Entity - Entidade de Domínio para Menus Dinâmicos
Clean Architecture - Domain Layer
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MenuType(str, Enum):
    """Tipos de menu disponíveis"""
    FOLDER = "folder"
    PAGE = "page" 
    EXTERNAL_LINK = "external_link"
    SEPARATOR = "separator"


class MenuStatus(str, Enum):
    """Status do menu"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


@dataclass
class MenuEntity:
    """
    Entidade de negócio para Menus (Clean Architecture)
    
    Representa um item de menu no sistema com todas suas propriedades
    e regras de negócio. Esta classe é independente de frameworks
    e tecnologias específicas.
    """
    # Identificação
    id: Optional[int] = None
    parent_id: Optional[int] = None
    
    # Dados principais
    name: str = ""
    slug: str = ""
    url: Optional[str] = None
    route_name: Optional[str] = None
    route_params: Optional[str] = None
    
    # Hierarquia e ordenação
    level: int = 0
    sort_order: int = 0
    
    # Tipo e status
    menu_type: MenuType = MenuType.PAGE
    status: MenuStatus = MenuStatus.ACTIVE
    
    # Visibilidade
    is_visible: bool = True
    visible_in_menu: bool = True
    
    # Permissões e contexto
    permission_name: Optional[str] = None
    company_specific: bool = False
    establishment_specific: bool = False
    
    # Customização visual
    icon: Optional[str] = None
    badge_text: Optional[str] = None
    badge_color: Optional[str] = None
    css_class: Optional[str] = None
    
    # Metadados
    description: Optional[str] = None
    help_text: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    # Auditoria
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Hierarquia computada
    full_path_name: Optional[str] = None
    id_path: List[int] = field(default_factory=list)
    
    # Relacionamentos
    children: List['MenuEntity'] = field(default_factory=list)
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.keywords is None:
            self.keywords = []
        if self.id_path is None:
            self.id_path = []
        if self.children is None:
            self.children = []
    
    # Métodos de negócio
    
    def is_root_menu(self) -> bool:
        """Verifica se é um menu raiz (sem pai)"""
        return self.parent_id is None
    
    def is_leaf_menu(self) -> bool:
        """Verifica se é um menu folha (sem filhos)"""
        return len(self.children) == 0
    
    def has_children(self) -> bool:
        """Verifica se tem filhos"""
        return len(self.children) > 0
    
    def get_depth(self) -> int:
        """Retorna a profundidade na hierarquia (baseado no level)"""
        return self.level
    
    def can_have_children(self) -> bool:
        """Verifica se pode ter filhos baseado no tipo"""
        return self.menu_type in [MenuType.FOLDER, MenuType.PAGE]
    
    def is_accessible_by_permission(self, user_permissions: List[str]) -> bool:
        """Verifica se o usuário tem permissão para acessar este menu"""
        if not self.permission_name:
            return True  # Menu público
        return self.permission_name in user_permissions
    
    def is_visible_in_context(self, context_type: str) -> bool:
        """Verifica se o menu é visível no contexto específico"""
        if not self.is_visible or not self.visible_in_menu:
            return False
            
        if context_type == "system":
            return True
        elif context_type == "company":
            return not self.establishment_specific
        elif context_type == "establishment":
            return True
        
        return False
    
    def add_child(self, child: 'MenuEntity'):
        """Adiciona um menu filho"""
        if not self.can_have_children():
            raise ValueError(f"Menu do tipo '{self.menu_type}' não pode ter filhos")
        
        child.parent_id = self.id
        child.level = self.level + 1
        self.children.append(child)
    
    def remove_child(self, child_id: int) -> bool:
        """Remove um menu filho"""
        for i, child in enumerate(self.children):
            if child.id == child_id:
                self.children.pop(i)
                return True
        return False
    
    def get_all_descendants(self) -> List['MenuEntity']:
        """Retorna todos os descendentes (recursivo)"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_ancestors_path(self) -> List[int]:
        """Retorna o caminho de IDs até a raiz"""
        return self.id_path.copy()
    
    def update_sort_order(self, new_order: int):
        """Atualiza a ordem de classificação"""
        if new_order < 0:
            raise ValueError("Sort order não pode ser negativo")
        self.sort_order = new_order
    
    def activate(self):
        """Ativa o menu"""
        self.status = MenuStatus.ACTIVE
        self.is_visible = True
        self.visible_in_menu = True
    
    def deactivate(self):
        """Desativa o menu"""
        self.status = MenuStatus.INACTIVE
        self.is_visible = False
        self.visible_in_menu = False
    
    def set_as_draft(self):
        """Marca como rascunho"""
        self.status = MenuStatus.DRAFT
        self.is_visible = False
        self.visible_in_menu = False
    
    def validate_hierarchy_rules(self) -> List[str]:
        """Valida regras de hierarquia e retorna lista de erros"""
        errors = []
        
        # Máximo 5 níveis de profundidade
        if self.level > 4:
            errors.append("Máximo de 5 níveis de hierarquia permitidos")
        
        # Menu não pode ser pai de si mesmo
        if self.id and self.parent_id == self.id:
            errors.append("Menu não pode ser pai de si mesmo")
        
        # Separadores não podem ter filhos
        if self.menu_type == MenuType.SEPARATOR and self.has_children():
            errors.append("Separadores não podem ter filhos")
        
        # Links externos não deveriam ter filhos
        if self.menu_type == MenuType.EXTERNAL_LINK and self.has_children():
            errors.append("Links externos não deveriam ter filhos")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (serialização)"""
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'slug': self.slug,
            'url': self.url,
            'route_name': self.route_name,
            'route_params': self.route_params,
            'level': self.level,
            'sort_order': self.sort_order,
            'menu_type': self.menu_type.value if self.menu_type else None,
            'status': self.status.value if self.status else None,
            'is_visible': self.is_visible,
            'visible_in_menu': self.visible_in_menu,
            'permission_name': self.permission_name,
            'company_specific': self.company_specific,
            'establishment_specific': self.establishment_specific,
            'icon': self.icon,
            'badge_text': self.badge_text,
            'badge_color': self.badge_color,
            'css_class': self.css_class,
            'description': self.description,
            'help_text': self.help_text,
            'keywords': self.keywords.copy() if self.keywords else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'full_path_name': self.full_path_name,
            'id_path': self.id_path.copy() if self.id_path else [],
            'children': [child.to_dict() for child in self.children] if self.children else []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MenuEntity':
        """Cria instância a partir de dicionário (deserialização)"""
        # Converter strings de volta para enums
        menu_type = MenuType(data['menu_type']) if data.get('menu_type') else MenuType.PAGE
        status = MenuStatus(data['status']) if data.get('status') else MenuStatus.ACTIVE
        
        # Converter strings ISO para datetime
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        deleted_at = datetime.fromisoformat(data['deleted_at']) if data.get('deleted_at') else None
        
        # Converter filhos recursivamente
        children = []
        if data.get('children'):
            children = [cls.from_dict(child_data) for child_data in data['children']]
        
        return cls(
            id=data.get('id'),
            parent_id=data.get('parent_id'),
            name=data.get('name', ''),
            slug=data.get('slug', ''),
            url=data.get('url'),
            route_name=data.get('route_name'),
            route_params=data.get('route_params'),
            level=data.get('level', 0),
            sort_order=data.get('sort_order', 0),
            menu_type=menu_type,
            status=status,
            is_visible=data.get('is_visible', True),
            visible_in_menu=data.get('visible_in_menu', True),
            permission_name=data.get('permission_name'),
            company_specific=data.get('company_specific', False),
            establishment_specific=data.get('establishment_specific', False),
            icon=data.get('icon'),
            badge_text=data.get('badge_text'),
            badge_color=data.get('badge_color'),
            css_class=data.get('css_class'),
            description=data.get('description'),
            help_text=data.get('help_text'),
            keywords=data.get('keywords', []).copy() if data.get('keywords') else [],
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by'),
            full_path_name=data.get('full_path_name'),
            id_path=data.get('id_path', []).copy() if data.get('id_path') else [],
            children=children
        )
    
    def __repr__(self) -> str:
        return f"MenuEntity(id={self.id}, name='{self.name}', slug='{self.slug}', level={self.level})"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"