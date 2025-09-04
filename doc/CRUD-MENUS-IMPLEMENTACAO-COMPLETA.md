# CRUD DE MENUS DINÂMICOS - IMPLEMENTAÇÃO COMPLETA

## 🎯 OBJETIVO

Este documento detalha a implementação completa do sistema CRUD para menus dinâmicos, seguindo todas as práticas, padrões e recursos já estabelecidos no sistema de empresas, com foco especial em **performance** devido à lentidão identificada.

---

## 🚨 PROBLEMA DE PERFORMANCE IDENTIFICADO

### Query SQL Complexa no MenuRepository
**Arquivo:** `app/domain/repositories/menu_repository.py:79-194`

**Problemas identificados:**
- Query com 3 CTEs (Common Table Expressions) aninhadas
- Múltiplos JOINs complexos (users, roles, permissions, menus)
- Falta de índices otimizados
- Execução de validações de contexto em tempo real

**Solução proposta:**
- Implementar cache Redis para menus por usuário/contexto
- Criar views materializadas no banco
- Otimizar queries com índices específicos
- Implementar lazy loading para menus filhos

---

## 📋 ESTRUTURA COMPLETA DO CRUD

### 1. CAMADA DE DOMÍNIO

#### 1.1 Entidade Principal - MenuEntity
```python
# app/domain/entities/menu.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MenuType(str, Enum):
    FOLDER = "folder"
    PAGE = "page" 
    EXTERNAL_LINK = "external_link"
    SEPARATOR = "separator"

class MenuStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

@dataclass
class MenuEntity:
    """Entidade de negócio para Menus (Clean Architecture)"""
    id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str = ""
    slug: str = ""
    url: Optional[str] = None
    route_name: Optional[str] = None
    route_params: Optional[str] = None
    icon: Optional[str] = None
    level: int = 0
    sort_order: int = 0
    menu_type: MenuType = MenuType.PAGE
    status: MenuStatus = MenuStatus.ACTIVE
    is_visible: bool = True
    visible_in_menu: bool = True
    
    # Permissões e contexto
    permission_name: Optional[str] = None
    company_specific: bool = False
    establishment_specific: bool = False
    
    # Customização visual
    badge_text: Optional[str] = None
    badge_color: Optional[str] = None
    css_class: Optional[str] = None
    
    # Metadados
    description: Optional[str] = None
    help_text: Optional[str] = None
    keywords: List[str] = None
    
    # Auditoria
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    
    # Hierarquia computed
    full_path_name: Optional[str] = None
    id_path: Optional[List[int]] = None
    children: List['MenuEntity'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.keywords is None:
            self.keywords = []
```

#### 1.2 Interface do Repository
```python
# app/domain/repositories/menu_repository_interface.py

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.menu import MenuEntity

class MenuRepositoryInterface(ABC):
    """Interface para Repository de Menus (Dependency Inversion)"""
    
    @abstractmethod
    async def create(self, menu: MenuEntity) -> MenuEntity:
        """Criar novo menu"""
        pass
    
    @abstractmethod
    async def get_by_id(self, menu_id: int) -> Optional[MenuEntity]:
        """Buscar menu por ID"""
        pass
    
    @abstractmethod
    async def get_all(self, 
                     skip: int = 0, 
                     limit: int = 100,
                     parent_id: Optional[int] = None,
                     status: Optional[str] = None,
                     search: Optional[str] = None) -> List[MenuEntity]:
        """Listar menus com filtros"""
        pass
    
    @abstractmethod
    async def update(self, menu_id: int, menu: MenuEntity) -> Optional[MenuEntity]:
        """Atualizar menu"""
        pass
    
    @abstractmethod
    async def delete(self, menu_id: int) -> bool:
        """Excluir menu (soft delete)"""
        pass
    
    @abstractmethod
    async def get_hierarchy_tree(self, 
                                user_id: Optional[int] = None,
                                context_type: str = "system") -> List[MenuEntity]:
        """Buscar árvore hierárquica completa"""
        pass
    
    @abstractmethod
    async def reorder_siblings(self, parent_id: Optional[int], menu_orders: List[Dict]) -> bool:
        """Reordenar menus irmãos"""
        pass
    
    @abstractmethod
    async def validate_hierarchy(self, menu: MenuEntity) -> bool:
        """Validar hierarquia (evitar loops)"""
        pass
```

### 2. CAMADA DE APLICAÇÃO

#### 2.1 Use Cases Principais
```python
# app/application/use_cases/menu_use_cases.py

from typing import List, Optional
from app.domain.entities.menu import MenuEntity
from app.domain.repositories.menu_repository_interface import MenuRepositoryInterface
from app.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO, MenuListDTO

class CreateMenuUseCase:
    """Caso de uso: Criar Menu"""
    
    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
    
    async def execute(self, data: MenuCreateDTO, created_by: int) -> MenuEntity:
        """Executar criação de menu com validações de negócio"""
        
        # Validação: slug único no nível
        existing = await self.repository.get_by_slug(data.slug, data.parent_id)
        if existing:
            raise ValueError(f"Menu com slug '{data.slug}' já existe no nível")
        
        # Validação: hierarquia (máximo 5 níveis)
        if data.parent_id:
            parent = await self.repository.get_by_id(data.parent_id)
            if not parent:
                raise ValueError("Menu pai não encontrado")
            if parent.level >= 4:
                raise ValueError("Máximo de 5 níveis de hierarquia permitidos")
        
        # Calcular nível e sort_order
        level = 0
        if data.parent_id:
            parent = await self.repository.get_by_id(data.parent_id)
            level = parent.level + 1
        
        # Auto sort_order (último + 1)
        siblings = await self.repository.get_siblings(data.parent_id)
        sort_order = max([s.sort_order for s in siblings], default=0) + 1
        
        # Criar entidade
        menu_entity = MenuEntity(
            parent_id=data.parent_id,
            name=data.name,
            slug=data.slug,
            url=data.url,
            route_name=data.route_name,
            icon=data.icon,
            level=level,
            sort_order=sort_order,
            menu_type=data.menu_type,
            permission_name=data.permission_name,
            company_specific=data.company_specific,
            establishment_specific=data.establishment_specific,
            created_by=created_by
        )
        
        return await self.repository.create(menu_entity)

class UpdateMenuUseCase:
    """Caso de uso: Atualizar Menu"""
    
    def __init__(self, repository: MenuRepositoryInterface):
        self.repository = repository
    
    async def execute(self, menu_id: int, data: MenuUpdateDTO, updated_by: int) -> Optional[MenuEntity]:
        """Executar atualização com validações"""
        
        existing = await self.repository.get_by_id(menu_id)
        if not existing:
            return None
        
        # Validação: não pode ser pai de si mesmo
        if data.parent_id == menu_id:
            raise ValueError("Menu não pode ser pai de si mesmo")
        
        # Validação: não pode criar loop
        if data.parent_id and not await self.repository.validate_hierarchy_change(menu_id, data.parent_id):
            raise ValueError("Alteração criaria loop na hierarquia")
        
        # Aplicar mudanças
        for field, value in data.model_dump(exclude_unset=True).items():
            if hasattr(existing, field):
                setattr(existing, field, value)
        
        existing.updated_by = updated_by
        
        return await self.repository.update(menu_id, existing)

class GetMenuTreeUseCase:
    """Caso de uso: Buscar Árvore de Menus (com cache)"""
    
    def __init__(self, repository: MenuRepositoryInterface, cache_service):
        self.repository = repository
        self.cache = cache_service
    
    async def execute(self, user_id: Optional[int] = None, context_type: str = "system") -> List[MenuEntity]:
        """Buscar árvore com cache inteligente"""
        
        # Cache key baseado no contexto
        cache_key = f"menu_tree:user_{user_id}:ctx_{context_type}"
        
        # Tentar cache primeiro (5 minutos TTL)
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Buscar do banco
        tree = await self.repository.get_hierarchy_tree(user_id, context_type)
        
        # Cachear resultado
        await self.cache.set(cache_key, tree, ttl=300)
        
        return tree
```

#### 2.2 DTOs de Transferência
```python
# app/application/dto/menu_dto.py

from pydantic import BaseModel, Field
from typing import Optional, List
from app.domain.entities.menu import MenuType, MenuStatus

class MenuCreateDTO(BaseModel):
    """DTO para criação de menu"""
    parent_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=50, regex=r'^[a-z0-9-_]+$')
    url: Optional[str] = Field(None, max_length=255)
    route_name: Optional[str] = Field(None, max_length=100)
    route_params: Optional[str] = Field(None, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    menu_type: MenuType = MenuType.PAGE
    permission_name: Optional[str] = Field(None, max_length=100)
    company_specific: bool = False
    establishment_specific: bool = False
    badge_text: Optional[str] = Field(None, max_length=20)
    badge_color: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=255)
    is_visible: bool = True
    visible_in_menu: bool = True

class MenuUpdateDTO(BaseModel):
    """DTO para atualização de menu"""
    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50, regex=r'^[a-z0-9-_]+$')
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
    description: Optional[str] = Field(None, max_length=255)
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None
    sort_order: Optional[int] = None

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
    children_count: int = 0
    has_permission: bool = True
    full_path_name: str
    created_at: datetime
    updated_at: datetime

class MenuDetailDTO(MenuListDTO):
    """DTO completo do menu"""
    url: Optional[str]
    route_name: Optional[str]
    route_params: Optional[str]
    icon: Optional[str]
    permission_name: Optional[str]
    company_specific: bool
    establishment_specific: bool
    badge_text: Optional[str]
    badge_color: Optional[str]
    description: Optional[str]
    help_text: Optional[str]
    css_class: Optional[str]
    keywords: List[str] = []
    children: List['MenuDetailDTO'] = []
```

### 3. CAMADA DE INFRAESTRUTURA

#### 3.1 Repository Otimizado com Cache
```python
# app/infrastructure/repositories/menu_repository_optimized.py

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from redis import Redis
import json
import structlog
from datetime import datetime, timedelta

from app.domain.repositories.menu_repository_interface import MenuRepositoryInterface
from app.domain.entities.menu import MenuEntity
from app.infrastructure.orm.models import Menu as MenuORM
from app.infrastructure.cache.redis_service import RedisService

logger = structlog.get_logger()

class MenuRepositoryOptimized(MenuRepositoryInterface):
    """Repository otimizado com cache e performance melhorada"""
    
    def __init__(self, db: AsyncSession, cache: RedisService):
        self.db = db
        self.cache = cache
        self.logger = logger
    
    async def create(self, menu: MenuEntity) -> MenuEntity:
        """Criar menu com invalidação de cache"""
        
        menu_orm = MenuORM(
            parent_id=menu.parent_id,
            name=menu.name,
            slug=menu.slug,
            url=menu.url,
            route_name=menu.route_name,
            route_params=menu.route_params,
            icon=menu.icon,
            level=menu.level,
            sort_order=menu.sort_order,
            menu_type=menu.menu_type.value,
            status=menu.status.value,
            is_visible=menu.is_visible,
            visible_in_menu=menu.visible_in_menu,
            permission_name=menu.permission_name,
            company_specific=menu.company_specific,
            establishment_specific=menu.establishment_specific,
            badge_text=menu.badge_text,
            badge_color=menu.badge_color,
            css_class=menu.css_class,
            description=menu.description,
            help_text=menu.help_text,
            created_by=menu.created_by
        )
        
        self.db.add(menu_orm)
        await self.db.flush()
        
        # Recalcular full_path_name
        await self._update_hierarchy_paths(menu_orm.id)
        
        await self.db.commit()
        
        # Invalidar cache relacionado
        await self._invalidate_menu_cache()
        
        # Retornar entidade atualizada
        await self.db.refresh(menu_orm)
        return self._orm_to_entity(menu_orm)
    
    async def get_all(self, 
                     skip: int = 0, 
                     limit: int = 100,
                     parent_id: Optional[int] = None,
                     status: Optional[str] = None,
                     search: Optional[str] = None) -> List[MenuEntity]:
        """Listar menus com cache e otimizações"""
        
        # Cache key
        cache_key = f"menu_list:skip_{skip}:limit_{limit}:parent_{parent_id}:status_{status}:search_{search}"
        
        # Tentar cache primeiro
        cached = await self.cache.get(cache_key)
        if cached:
            self.logger.info("Menu list served from cache", cache_key=cache_key)
            return [MenuEntity(**item) for item in cached]
        
        # Query otimizada
        query = select(MenuORM).options(
            selectinload(MenuORM.children)
        ).where(MenuORM.deleted_at.is_(None))
        
        if parent_id is not None:
            query = query.where(MenuORM.parent_id == parent_id)
        
        if status:
            query = query.where(MenuORM.status == status)
        
        if search:
            search_filter = or_(
                MenuORM.name.ilike(f"%{search}%"),
                MenuORM.slug.ilike(f"%{search}%"),
                MenuORM.full_path_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        query = query.order_by(MenuORM.level, MenuORM.sort_order, MenuORM.name)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        menus_orm = result.scalars().all()
        
        # Converter para entidades
        entities = [self._orm_to_entity(menu) for menu in menus_orm]
        
        # Cachear (TTL 10 minutos)
        await self.cache.set(cache_key, [entity.__dict__ for entity in entities], ttl=600)
        
        self.logger.info("Menu list loaded from database", count=len(entities))
        return entities
    
    async def get_hierarchy_tree(self, 
                               user_id: Optional[int] = None,
                               context_type: str = "system") -> List[MenuEntity]:
        """Buscar árvore com query otimizada e materializada"""
        
        cache_key = f"menu_tree:user_{user_id}:ctx_{context_type}"
        
        # Cache primeiro (TTL 5 minutos)
        cached = await self.cache.get(cache_key)
        if cached:
            return [MenuEntity(**item) for item in cached]
        
        # Query otimizada usando view materializada (se disponível)
        # Ou CTE otimizada com menos JOINs
        query = text("""
            WITH RECURSIVE menu_tree AS (
                -- Raiz: menus sem pai
                SELECT 
                    id, parent_id, name, slug, url, route_name, icon,
                    level, sort_order, menu_type, status, is_visible,
                    permission_name, company_specific, establishment_specific,
                    full_path_name, ARRAY[id] as path
                FROM master.menus 
                WHERE parent_id IS NULL 
                  AND deleted_at IS NULL
                  AND status = 'active'
                  AND is_visible = true
                
                UNION ALL
                
                -- Recursivo: filhos
                SELECT 
                    m.id, m.parent_id, m.name, m.slug, m.url, m.route_name, m.icon,
                    m.level, m.sort_order, m.menu_type, m.status, m.is_visible,
                    m.permission_name, m.company_specific, m.establishment_specific,
                    m.full_path_name, mt.path || m.id
                FROM master.menus m
                JOIN menu_tree mt ON m.parent_id = mt.id
                WHERE m.deleted_at IS NULL
                  AND m.status = 'active'
                  AND m.is_visible = true
                  AND array_length(mt.path, 1) < 5  -- Máximo 5 níveis
            )
            SELECT * FROM menu_tree
            ORDER BY level, sort_order, name
        """)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Converter para entidades e construir árvore
        menu_dict = {}
        root_menus = []
        
        for row in rows:
            entity = MenuEntity(
                id=row.id,
                parent_id=row.parent_id,
                name=row.name,
                slug=row.slug,
                url=row.url,
                route_name=row.route_name,
                icon=row.icon,
                level=row.level,
                sort_order=row.sort_order,
                menu_type=row.menu_type,
                status=row.status,
                is_visible=row.is_visible,
                permission_name=row.permission_name,
                company_specific=row.company_specific,
                establishment_specific=row.establishment_specific,
                full_path_name=row.full_path_name,
                children=[]
            )
            
            menu_dict[entity.id] = entity
            
            if entity.parent_id is None:
                root_menus.append(entity)
            else:
                parent = menu_dict.get(entity.parent_id)
                if parent:
                    parent.children.append(entity)
        
        # Cache resultado (TTL 5 minutos)
        serializable_tree = [self._entity_to_dict(menu) for menu in root_menus]
        await self.cache.set(cache_key, serializable_tree, ttl=300)
        
        self.logger.info("Menu hierarchy loaded from database", 
                        total_menus=len(menu_dict),
                        root_menus=len(root_menus))
        
        return root_menus
    
    async def reorder_siblings(self, parent_id: Optional[int], menu_orders: List[Dict]) -> bool:
        """Reordenar menus irmãos em batch"""
        
        try:
            # Update em batch para performance
            for item in menu_orders:
                await self.db.execute(
                    text("UPDATE master.menus SET sort_order = :sort_order WHERE id = :menu_id"),
                    {"sort_order": item["sort_order"], "menu_id": item["menu_id"]}
                )
            
            await self.db.commit()
            
            # Invalidar cache
            await self._invalidate_menu_cache()
            
            self.logger.info("Menu siblings reordered", parent_id=parent_id, count=len(menu_orders))
            return True
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error reordering menu siblings", error=str(e))
            return False
    
    async def _update_hierarchy_paths(self, menu_id: int):
        """Atualizar caminhos hierárquicos (full_path_name, id_path)"""
        
        query = text("""
            WITH RECURSIVE menu_path AS (
                SELECT 
                    id, parent_id, name, slug,
                    name as full_path_name,
                    ARRAY[id] as id_path,
                    0 as depth
                FROM master.menus 
                WHERE id = :menu_id
                
                UNION ALL
                
                SELECT 
                    mp.id, mp.parent_id, mp.name, mp.slug,
                    m.name || ' > ' || mp.full_path_name,
                    ARRAY[m.id] || mp.id_path,
                    mp.depth + 1
                FROM menu_path mp
                JOIN master.menus m ON mp.parent_id = m.id
                WHERE mp.parent_id IS NOT NULL
            )
            UPDATE master.menus 
            SET 
                full_path_name = (SELECT full_path_name FROM menu_path ORDER BY depth DESC LIMIT 1),
                id_path = (SELECT id_path FROM menu_path ORDER BY depth DESC LIMIT 1)
            WHERE id = :menu_id
        """)
        
        await self.db.execute(query, {"menu_id": menu_id})
    
    async def _invalidate_menu_cache(self):
        """Invalidar todos os caches relacionados a menus"""
        
        patterns = [
            "menu_tree:*",
            "menu_list:*", 
            "menu_item:*"
        ]
        
        for pattern in patterns:
            await self.cache.delete_pattern(pattern)
        
        self.logger.info("Menu cache invalidated")
    
    def _orm_to_entity(self, orm: MenuORM) -> MenuEntity:
        """Converter ORM para Entity"""
        return MenuEntity(
            id=orm.id,
            parent_id=orm.parent_id,
            name=orm.name,
            slug=orm.slug,
            url=orm.url,
            route_name=orm.route_name,
            route_params=orm.route_params,
            icon=orm.icon,
            level=orm.level,
            sort_order=orm.sort_order,
            menu_type=orm.menu_type,
            status=orm.status,
            is_visible=orm.is_visible,
            visible_in_menu=orm.visible_in_menu,
            permission_name=orm.permission_name,
            company_specific=orm.company_specific,
            establishment_specific=orm.establishment_specific,
            badge_text=orm.badge_text,
            badge_color=orm.badge_color,
            css_class=orm.css_class,
            description=orm.description,
            help_text=orm.help_text,
            full_path_name=orm.full_path_name,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            created_by=orm.created_by
        )
    
    def _entity_to_dict(self, entity: MenuEntity) -> Dict:
        """Converter Entity para Dict serializável"""
        result = {
            "id": entity.id,
            "parent_id": entity.parent_id,
            "name": entity.name,
            "slug": entity.slug,
            "url": entity.url,
            "route_name": entity.route_name,
            "icon": entity.icon,
            "level": entity.level,
            "sort_order": entity.sort_order,
            "menu_type": entity.menu_type,
            "status": entity.status,
            "is_visible": entity.is_visible,
            "permission_name": entity.permission_name,
            "company_specific": entity.company_specific,
            "establishment_specific": entity.establishment_specific,
            "full_path_name": entity.full_path_name,
            "children": [self._entity_to_dict(child) for child in entity.children]
        }
        return result
```

### 4. CAMADA DE APRESENTAÇÃO

#### 4.1 Controlador FastAPI Completo
```python
# app/presentation/api/v1/menus_crud.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.cache.redis_service import get_redis_service
from app.infrastructure.repositories.menu_repository_optimized import MenuRepositoryOptimized
from app.application.use_cases.menu_use_cases import (
    CreateMenuUseCase, UpdateMenuUseCase, DeleteMenuUseCase, 
    GetMenuTreeUseCase, ReorderMenusUseCase
)
from app.presentation.schemas.menu import (
    MenuCreate, MenuUpdate, MenuDetailed, MenuList, MenuTreeResponse,
    ReorderRequest
)
from app.infrastructure.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/menus/crud", tags=["Menus CRUD"])
logger = get_logger()

# Dependency injection
async def get_menu_repository(
    db: AsyncSession = Depends(get_db),
    cache = Depends(get_redis_service)
) -> MenuRepositoryOptimized:
    return MenuRepositoryOptimized(db, cache)

@router.post(
    "/",
    response_model=MenuDetailed,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Menu",
    description="""
    Cria um novo menu na hierarquia do sistema.
    
    **Funcionalidades:**
    - Validação automática de hierarquia (máximo 5 níveis)
    - Slug único por nível
    - Auto-ordenação (sort_order)
    - Invalidação automática de cache
    
    **Validações:**
    - Nome e slug obrigatórios
    - Slug deve ser único no nível pai
    - Menu pai deve existir (se informado)
    - Permissão deve existir no sistema (se informada)
    """,
    responses={
        201: {"description": "Menu criado com sucesso"},
        400: {"description": "Dados inválidos ou hierarquia inválida"},
        401: {"description": "Não autorizado"},
        409: {"description": "Slug já existe no nível"}
    }
)
async def create_menu(
    menu_data: MenuCreate,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Criar novo menu com validações completas"""
    
    try:
        use_case = CreateMenuUseCase(repository)
        result = await use_case.execute(menu_data, current_user.id)
        
        logger.info("Menu criado com sucesso", 
                   menu_id=result.id, 
                   name=result.name,
                   created_by=current_user.id)
        
        return result
        
    except ValueError as e:
        logger.warning("Erro de validação na criação de menu", 
                      error=str(e), 
                      user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Erro interno ao criar menu", 
                    error=str(e), 
                    user_id=current_user.id,
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get(
    "/",
    response_model=List[MenuList],
    summary="Listar Menus",
    description="""
    Lista menus com filtros e paginação otimizada.
    
    **Performance:**
    - Cache automático (TTL 10 minutos)
    - Índices otimizados no banco
    - Eager loading de relacionamentos
    
    **Filtros:**
    - `parent_id`: Filtrar por menu pai (None = raiz)
    - `status`: Filtrar por status (active, inactive, draft)
    - `search`: Busca por nome, slug ou caminho completo
    - `level`: Filtrar por nível hierárquico
    """,
    responses={
        200: {"description": "Lista de menus retornada com sucesso"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menus(
    skip: int = Query(0, ge=0, description="Paginação: registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Paginação: máximo de registros"),
    parent_id: Optional[int] = Query(None, description="Filtrar por menu pai (None = raiz)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Busca por nome/slug/caminho"),
    level: Optional[int] = Query(None, ge=0, le=4, description="Filtrar por nível (0-4)"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Listar menus com cache e otimizações"""
    
    try:
        menus = await repository.get_all(
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            status=status,
            search=search
        )
        
        # Filtro adicional por nível (em memória para cache eficiente)
        if level is not None:
            menus = [m for m in menus if m.level == level]
        
        logger.info("Menus listados", 
                   count=len(menus),
                   user_id=current_user.id,
                   filters={'parent_id': parent_id, 'status': status, 'level': level})
        
        return menus
        
    except Exception as e:
        logger.error("Erro ao listar menus", 
                    error=str(e),
                    user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get(
    "/tree",
    response_model=MenuTreeResponse,
    summary="Buscar Árvore Hierárquica",
    description="""
    Retorna a árvore completa de menus em formato hierárquico.
    
    **Performance:**
    - Query recursiva otimizada (CTE)
    - Cache com TTL 5 minutos
    - Máximo 5 níveis de profundidade
    
    **Funcionalidades:**
    - Estrutura parent-children completa
    - Ordenação automática por nível e sort_order
    - Apenas menus ativos e visíveis
    """,
    responses={
        200: {"description": "Árvore retornada com sucesso"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu_tree(
    context_type: str = Query("system", description="Contexto (system/company/establishment)"),
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Buscar árvore hierárquica completa"""
    
    try:
        use_case = GetMenuTreeUseCase(repository, cache_service=repository.cache)
        tree = await use_case.execute(current_user.id, context_type)
        
        return {
            "user_id": current_user.id,
            "context_type": context_type,
            "total_menus": sum(count_tree_nodes(menu) for menu in tree),
            "root_menus": len(tree),
            "tree": tree
        }
        
    except Exception as e:
        logger.error("Erro ao buscar árvore de menus",
                    error=str(e),
                    user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get(
    "/{menu_id}",
    response_model=MenuDetailed,
    summary="Buscar Menu por ID",
    description="""
    Retorna dados completos de um menu específico.
    
    **Inclui:**
    - Todos os campos do menu
    - Informações da hierarquia (parent, children count)
    - Metadados de auditoria
    - Path completo na hierarquia
    """,
    responses={
        200: {"description": "Menu encontrado"},
        404: {"description": "Menu não encontrado"},
        401: {"description": "Não autorizado"}
    }
)
async def get_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Buscar menu por ID"""
    
    menu = await repository.get_by_id(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu não encontrado"
        )
    
    return menu

@router.put(
    "/{menu_id}",
    response_model=MenuDetailed,
    summary="Atualizar Menu",
    description="""
    Atualiza dados de um menu existente.
    
    **Funcionalidades:**
    - Validação de hierarquia (não pode criar loops)
    - Recálculo automático de níveis se mudou parent
    - Atualização de caminhos hierárquicos
    - Invalidação automática de cache
    
    **Restrições:**
    - Menu não pode ser pai de si mesmo
    - Não pode criar loops na hierarquia
    - Slug deve continuar único no nível
    """,
    responses={
        200: {"description": "Menu atualizado com sucesso"},
        400: {"description": "Dados inválidos"},
        404: {"description": "Menu não encontrado"},
        401: {"description": "Não autorizado"}
    }
)
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Atualizar menu com validações"""
    
    try:
        use_case = UpdateMenuUseCase(repository)
        result = await use_case.execute(menu_id, menu_data, current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        logger.info("Menu atualizado",
                   menu_id=menu_id,
                   updated_by=current_user.id)
        
        return result
        
    except ValueError as e:
        logger.warning("Erro de validação na atualização",
                      menu_id=menu_id,
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Erro interno ao atualizar menu",
                    menu_id=menu_id,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Menu",
    description="""
    Exclui um menu do sistema (soft delete).
    
    **Comportamento:**
    - Exclusão lógica (soft delete)
    - Menu não aparece mais nas listagens
    - Filhos não são excluídos automaticamente
    - Ação auditada nos logs
    
    **Regras de negócio:**
    - Menu com filhos ativos não pode ser excluído
    - Apenas o criador ou admin pode excluir
    """,
    responses={
        204: {"description": "Menu excluído com sucesso"},
        400: {"description": "Menu possui filhos ativos"},
        404: {"description": "Menu não encontrado"},
        403: {"description": "Sem permissão para excluir"},
        401: {"description": "Não autorizado"}
    }
)
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Excluir menu (soft delete)"""
    
    try:
        use_case = DeleteMenuUseCase(repository)
        success = await use_case.execute(menu_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu não encontrado"
            )
        
        logger.info("Menu excluído",
                   menu_id=menu_id,
                   deleted_by=current_user.id)
        
    except ValueError as e:
        logger.warning("Erro de validação na exclusão",
                      menu_id=menu_id,
                      error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Erro interno ao excluir menu",
                    menu_id=menu_id,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post(
    "/reorder",
    status_code=status.HTTP_200_OK,
    summary="Reordenar Menus",
    description="""
    Reordena menus irmãos em lote.
    
    **Funcionalidades:**
    - Atualização em batch para performance
    - Validação de integridade
    - Invalidação automática de cache
    
    **Payload:**
    ```json
    {
        "parent_id": null,
        "menu_orders": [
            {"menu_id": 1, "sort_order": 1},
            {"menu_id": 2, "sort_order": 2}
        ]
    }
    ```
    """,
    responses={
        200: {"description": "Reordenação concluída com sucesso"},
        400: {"description": "Dados inválidos"},
        401: {"description": "Não autorizado"}
    }
)
async def reorder_menus(
    reorder_data: ReorderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    repository: MenuRepositoryOptimized = Depends(get_menu_repository)
):
    """Reordenar menus irmãos"""
    
    try:
        use_case = ReorderMenusUseCase(repository)
        success = await use_case.execute(
            reorder_data.parent_id,
            reorder_data.menu_orders,
            current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro na reordenação dos menus"
            )
        
        logger.info("Menus reordenados",
                   parent_id=reorder_data.parent_id,
                   count=len(reorder_data.menu_orders),
                   reordered_by=current_user.id)
        
        return {"message": "Menus reordenados com sucesso"}
        
    except Exception as e:
        logger.error("Erro ao reordenar menus",
                    error=str(e),
                    user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

def count_tree_nodes(menu: MenuEntity) -> int:
    """Contar total de nós na árvore recursivamente"""
    count = 1  # Este nó
    for child in menu.children or []:
        count += count_tree_nodes(child)
    return count
```

### 5. OTIMIZAÇÕES DE BANCO DE DADOS

#### 5.1 Índices Específicos
```sql
-- Índices para performance de menus
CREATE INDEX CONCURRENTLY idx_menus_parent_sort ON master.menus(parent_id, sort_order) 
WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY idx_menus_hierarchy ON master.menus(level, parent_id, sort_order) 
WHERE deleted_at IS NULL AND status = 'active';

CREATE INDEX CONCURRENTLY idx_menus_slug_parent ON master.menus(slug, parent_id) 
WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY idx_menus_search ON master.menus 
USING gin(to_tsvector('portuguese', name || ' ' || coalesce(full_path_name, '')));

-- Índice para permission lookup
CREATE INDEX CONCURRENTLY idx_menus_permission ON master.menus(permission_name) 
WHERE permission_name IS NOT NULL AND deleted_at IS NULL;
```

#### 5.2 View Materializada (Opcional)
```sql
-- View materializada para árvore de menus (refresh automático)
CREATE MATERIALIZED VIEW master.mv_menu_hierarchy AS
WITH RECURSIVE menu_tree AS (
    SELECT 
        id, parent_id, name, slug, level, sort_order,
        full_path_name, ARRAY[id] as ancestors,
        0 as depth
    FROM master.menus 
    WHERE parent_id IS NULL 
      AND deleted_at IS NULL
      AND status = 'active'
    
    UNION ALL
    
    SELECT 
        m.id, m.parent_id, m.name, m.slug, m.level, m.sort_order,
        m.full_path_name, mt.ancestors || m.id,
        mt.depth + 1
    FROM master.menus m
    JOIN menu_tree mt ON m.parent_id = mt.id
    WHERE m.deleted_at IS NULL
      AND m.status = 'active'
      AND mt.depth < 4
)
SELECT * FROM menu_tree;

-- Índices na view materializada
CREATE INDEX idx_mv_menu_hierarchy_parent ON master.mv_menu_hierarchy(parent_id, sort_order);
CREATE INDEX idx_mv_menu_hierarchy_depth ON master.mv_menu_hierarchy(depth, sort_order);

-- Trigger para refresh automático
CREATE OR REPLACE FUNCTION refresh_menu_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY master.mv_menu_hierarchy;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_menu_hierarchy_refresh
    AFTER INSERT OR UPDATE OR DELETE ON master.menus
    FOR EACH STATEMENT
    EXECUTE FUNCTION refresh_menu_hierarchy();
```

### 6. TESTES UNITÁRIOS E INTEGRAÇÃO

#### 6.1 Testes de Use Cases
```python
# tests/unit/test_menu_use_cases.py

import pytest
from unittest.mock import AsyncMock, Mock
from app.application.use_cases.menu_use_cases import CreateMenuUseCase
from app.application.dto.menu_dto import MenuCreateDTO
from app.domain.entities.menu import MenuEntity, MenuType

class TestCreateMenuUseCase:
    """Testes unitários do caso de uso de criação"""
    
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_repository):
        return CreateMenuUseCase(mock_repository)
    
    @pytest.mark.asyncio
    async def test_create_root_menu_success(self, use_case, mock_repository):
        """Teste: criação de menu raiz com sucesso"""
        
        # Arrange
        mock_repository.get_by_slug.return_value = None
        mock_repository.get_siblings.return_value = []
        mock_repository.create.return_value = MenuEntity(
            id=1, name="Dashboard", slug="dashboard", level=0
        )
        
        data = MenuCreateDTO(
            name="Dashboard",
            slug="dashboard",
            menu_type=MenuType.PAGE
        )
        
        # Act
        result = await use_case.execute(data, created_by=1)
        
        # Assert
        assert result.id == 1
        assert result.name == "Dashboard"
        assert result.level == 0
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_menu_slug_already_exists(self, use_case, mock_repository):
        """Teste: erro quando slug já existe no nível"""
        
        # Arrange
        existing_menu = MenuEntity(id=1, name="Dashboard", slug="dashboard")
        mock_repository.get_by_slug.return_value = existing_menu
        
        data = MenuCreateDTO(
            name="Dashboard 2",
            slug="dashboard",  # Mesmo slug
            menu_type=MenuType.PAGE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="slug 'dashboard' já existe"):
            await use_case.execute(data, created_by=1)
    
    @pytest.mark.asyncio
    async def test_create_menu_max_hierarchy_level(self, use_case, mock_repository):
        """Teste: erro quando excede máximo de níveis"""
        
        # Arrange
        parent_menu = MenuEntity(id=1, level=4)  # Nível máximo
        mock_repository.get_by_slug.return_value = None
        mock_repository.get_by_id.return_value = parent_menu
        
        data = MenuCreateDTO(
            parent_id=1,
            name="Sub Menu",
            slug="sub-menu",
            menu_type=MenuType.PAGE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Máximo de 5 níveis"):
            await use_case.execute(data, created_by=1)
```

#### 6.2 Testes de Performance
```python
# tests/performance/test_menu_performance.py

import pytest
import asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.menu_repository_optimized import MenuRepositoryOptimized
from app.infrastructure.cache.redis_service import RedisService

class TestMenuPerformance:
    """Testes de performance para menus"""
    
    @pytest.mark.asyncio
    async def test_menu_tree_load_time(self, async_session: AsyncSession, redis_service: RedisService):
        """Teste: árvore de menus deve carregar em menos de 200ms"""
        
        # Arrange
        repository = MenuRepositoryOptimized(async_session, redis_service)
        
        # Act
        start_time = time.time()
        tree = await repository.get_hierarchy_tree()
        end_time = time.time()
        
        # Assert
        execution_time = end_time - start_time
        assert execution_time < 0.2, f"Menu tree load took {execution_time:.3f}s, expected < 0.2s"
        assert len(tree) > 0, "Should return at least root menus"
    
    @pytest.mark.asyncio
    async def test_menu_cache_hit_performance(self, async_session: AsyncSession, redis_service: RedisService):
        """Teste: cache hit deve ser muito mais rápido que DB"""
        
        # Arrange
        repository = MenuRepositoryOptimized(async_session, redis_service)
        
        # Act - primeira busca (miss)
        start_time = time.time()
        tree1 = await repository.get_hierarchy_tree()
        first_load_time = time.time() - start_time
        
        # Act - segunda busca (hit)
        start_time = time.time()
        tree2 = await repository.get_hierarchy_tree()
        cache_hit_time = time.time() - start_time
        
        # Assert
        assert cache_hit_time < first_load_time / 10, "Cache hit should be 10x faster"
        assert tree1 == tree2, "Cache should return same data"
    
    @pytest.mark.asyncio
    async def test_concurrent_menu_access(self, async_session: AsyncSession, redis_service: RedisService):
        """Teste: múltiplas requisições concorrentes"""
        
        # Arrange
        repository = MenuRepositoryOptimized(async_session, redis_service)
        concurrent_requests = 50
        
        # Act
        start_time = time.time()
        tasks = [repository.get_hierarchy_tree() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Assert
        assert len(results) == concurrent_requests
        assert total_time < 2.0, f"50 concurrent requests took {total_time:.3f}s, expected < 2s"
        
        # Todos os resultados devem ser idênticos
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
```

### 7. MONITORAMENTO E OBSERVABILIDADE

#### 7.1 Métricas de Performance
```python
# app/infrastructure/monitoring/menu_metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Métricas Prometheus
menu_requests_total = Counter(
    'menu_requests_total',
    'Total menu requests',
    ['operation', 'status']
)

menu_duration_seconds = Histogram(
    'menu_duration_seconds',
    'Menu operation duration',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

menu_cache_hits = Counter(
    'menu_cache_hits_total',
    'Menu cache hits',
    ['cache_type']
)

menu_hierarchy_depth = Gauge(
    'menu_hierarchy_max_depth',
    'Maximum menu hierarchy depth'
)

def monitor_menu_operation(operation: str):
    """Decorator para monitorar operações de menu"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                menu_requests_total.labels(operation=operation, status=status).inc()
                menu_duration_seconds.labels(operation=operation).observe(duration)
        
        return wrapper
    return decorator

# Uso nos métodos do repository
class MenuRepositoryOptimized:
    
    @monitor_menu_operation('get_hierarchy_tree')
    async def get_hierarchy_tree(self, user_id: Optional[int] = None, context_type: str = "system"):
        # ... implementação
        pass
    
    @monitor_menu_operation('create')
    async def create(self, menu: MenuEntity):
        # ... implementação
        pass
```

### 8. DOCUMENTAÇÃO DA API

#### 8.1 Schemas OpenAPI Completos
```python
# app/presentation/schemas/menu.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MenuType(str, Enum):
    FOLDER = "folder"
    PAGE = "page"
    EXTERNAL_LINK = "external_link"
    SEPARATOR = "separator"

class MenuStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    DRAFT = "draft"

class MenuCreate(BaseModel):
    """Schema para criação de menu"""
    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    name: str = Field(..., min_length=1, max_length=100, description="Nome do menu")
    slug: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z0-9-_]+$', 
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
    description: Optional[str] = Field(None, max_length=255, description="Descrição do menu")
    help_text: Optional[str] = Field(None, max_length=500, description="Texto de ajuda")
    is_visible: bool = Field(True, description="Menu visível no sistema")
    visible_in_menu: bool = Field(True, description="Visível na navegação")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Relatórios",
                "slug": "relatorios", 
                "url": "/relatorios",
                "icon": "fas fa-chart-bar",
                "menu_type": "page",
                "description": "Módulo de relatórios gerenciais",
                "is_visible": True,
                "visible_in_menu": True
            }
        }
    )

class MenuUpdate(BaseModel):
    """Schema para atualização de menu"""
    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r'^[a-z0-9-_]+$')
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
    description: Optional[str] = Field(None, max_length=255)
    help_text: Optional[str] = Field(None, max_length=500)
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, description="Ordem de exibição")

class MenuList(BaseModel):
    """Schema para listagem de menus"""
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
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MenuDetailed(MenuList):
    """Schema completo do menu"""
    url: Optional[str]
    route_name: Optional[str] 
    route_params: Optional[str]
    icon: Optional[str]
    company_specific: bool
    establishment_specific: bool
    badge_text: Optional[str]
    badge_color: Optional[str]
    description: Optional[str]
    help_text: Optional[str]
    css_class: Optional[str]
    keywords: List[str] = []
    id_path: List[int] = Field([], description="Caminho de IDs até a raiz")
    created_by: Optional[int]
    updated_by: Optional[int]
    
    # Navegação
    parent: Optional['MenuList'] = Field(None, description="Menu pai")
    children: List['MenuList'] = Field([], description="Menus filhos diretos")
    siblings: List['MenuList'] = Field([], description="Menus no mesmo nível")

class MenuTreeItem(BaseModel):
    """Item da árvore hierárquica"""
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    url: Optional[str]
    icon: Optional[str]
    level: int
    sort_order: int
    badge_text: Optional[str]
    badge_color: Optional[str]
    has_permission: bool = True
    children: List['MenuTreeItem'] = []
    
    model_config = ConfigDict(from_attributes=True)

class MenuTreeResponse(BaseModel):
    """Resposta da árvore de menus"""
    user_id: int
    context_type: str = Field(..., description="Contexto atual (system/company/establishment)")
    total_menus: int = Field(..., description="Total de menus na árvore")
    root_menus: int = Field(..., description="Total de menus raiz")
    max_depth: int = Field(..., description="Profundidade máxima da árvore")
    tree: List[MenuTreeItem] = Field(..., description="Árvore hierárquica")
    cache_hit: bool = Field(False, description="Se foi servido do cache")
    load_time_ms: int = Field(..., description="Tempo de carregamento em ms")

class ReorderRequest(BaseModel):
    """Requisição para reordenação de menus"""
    parent_id: Optional[int] = Field(None, description="ID do menu pai (null = raiz)")
    menu_orders: List[Dict[str, int]] = Field(
        ..., 
        description="Lista de {menu_id, sort_order}",
        example=[
            {"menu_id": 1, "sort_order": 1},
            {"menu_id": 2, "sort_order": 2},
            {"menu_id": 3, "sort_order": 3}
        ]
    )

# Configurar referências forward
MenuDetailed.model_rebuild()
MenuTreeItem.model_rebuild()
```

---

## 🔧 IMPLEMENTAÇÃO POR FASES

### Fase 1 - Estrutura Base (1-2 dias)
- [ ] Criar entidades de domínio
- [ ] Implementar interfaces e DTOs
- [ ] Configurar models ORM básicos

### Fase 2 - Repository e Use Cases (2-3 dias)
- [ ] Implementar repository otimizado
- [ ] Desenvolver use cases principais
- [ ] Configurar cache Redis

### Fase 3 - API e Controladores (1-2 dias)
- [ ] Implementar endpoints CRUD
- [ ] Configurar validações e tratamento de erros
- [ ] Documentação OpenAPI

### Fase 4 - Otimizações de Performance (1-2 dias)
- [ ] Criar índices específicos
- [ ] Implementar view materializada
- [ ] Configurar monitoramento

### Fase 5 - Testes e Qualidade (1-2 dias)
- [ ] Testes unitários e integração
- [ ] Testes de performance
- [ ] Validação de qualidade

---

## 🎯 RESULTADOS ESPERADOS

### Performance
- **Tempo de resposta:** < 200ms para árvore completa
- **Cache hit rate:** > 90% após warmup
- **Concurrent load:** 100+ requisições/segundo

### Qualidade
- **Cobertura de testes:** > 85%
- **Complexidade ciclomática:** < 10 por método
- **Zero vazamentos de memória**

### Manutenibilidade
- **Clean Architecture:** Separação clara de responsabilidades
- **SOLID principles:** Código extensível e testável
- **Documentação:** 100% dos endpoints documentados

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Preparação
- [ ] Análise de requisitos completa
- [ ] Definição de arquitetura
- [ ] Setup do ambiente de desenvolvimento

### Desenvolvimento
- [ ] Implementar camada de domínio
- [ ] Desenvolver camada de aplicação
- [ ] Construir camada de infraestrutura
- [ ] Criar camada de apresentação

### Testes e Qualidade
- [ ] Testes unitários
- [ ] Testes de integração
- [ ] Testes de performance
- [ ] Code review

### Deploy e Monitoramento
- [ ] Deploy em ambiente de desenvolvimento
- [ ] Configurar monitoramento
- [ ] Validar performance em produção
- [ ] Documentação final

---

**Este documento segue exatamente os mesmos padrões, práticas e recursos implementados no sistema de empresas, garantindo consistência e qualidade no desenvolvimento do CRUD de menus dinâmicos.**