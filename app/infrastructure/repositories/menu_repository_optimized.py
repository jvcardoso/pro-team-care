"""
Menu Repository Otimizado - Infrastructure Layer
Implementação do repository com cache Redis e queries otimizadas
"""

import time
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, func, or_, select, text, update

from app.domain.entities.menu import MenuEntity, MenuStatus, MenuType
from app.domain.repositories.menu_repository_interface import MenuRepositoryInterface
from app.infrastructure.cache.menu_cache_service import (
    MenuCacheService,
    get_menu_cache_service,
)
from app.infrastructure.orm.models import Menu as MenuORM

logger = structlog.get_logger()


def timing_decorator(func):
    """Decorator para medir tempo de execução de métodos"""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            # Log apenas se for mais lento que 100ms
            if execution_time > 0.1:
                logger.warning(
                    "Método lento detectado",
                    method=func.__name__,
                    execution_time=f"{execution_time:.3f}s",
                    threshold="100ms",
                )

            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(
                "Erro em método com timing",
                method=func.__name__,
                execution_time=f"{execution_time:.3f}s",
                error=str(e),
            )
            raise

    return wrapper


class MenuRepositoryOptimized(MenuRepositoryInterface):
    """Repository otimizado com cache e performance melhorada"""

    def __init__(self, db, cache_service: Optional[MenuCacheService] = None):
        self.db = db
        self.cache_service = cache_service
        self.logger = logger

    async def _get_cache_service(self) -> MenuCacheService:
        """Obter serviço de cache (lazy loading)"""
        if not self.cache_service:
            self.cache_service = await get_menu_cache_service()
        return self.cache_service

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
            menu_type=MenuType(orm.menu_type) if orm.menu_type else MenuType.PAGE,
            status=MenuStatus(orm.status) if orm.status else MenuStatus.ACTIVE,
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
            keywords=orm.keywords or [],
            full_path_name=orm.full_path_name,
            id_path=orm.id_path or [],
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            deleted_at=orm.deleted_at,
            created_by=orm.created_by,
            updated_by=orm.updated_by,
        )

    def _entity_to_orm(
        self, entity: MenuEntity, orm: Optional[MenuORM] = None
    ) -> MenuORM:
        """Converter Entity para ORM"""
        if orm is None:
            orm = MenuORM()

        # Não atualizar ID se já existe
        if entity.id and not orm.id:
            orm.id = entity.id

        orm.parent_id = entity.parent_id
        orm.name = entity.name
        orm.slug = entity.slug
        orm.url = entity.url
        orm.route_name = entity.route_name
        orm.route_params = entity.route_params
        orm.icon = entity.icon
        orm.level = entity.level
        orm.sort_order = entity.sort_order
        orm.menu_type = entity.menu_type.value if entity.menu_type else "page"
        orm.status = entity.status.value if entity.status else "active"
        orm.is_visible = entity.is_visible
        orm.visible_in_menu = entity.visible_in_menu
        orm.permission_name = entity.permission_name
        orm.company_specific = entity.company_specific
        orm.establishment_specific = entity.establishment_specific
        orm.badge_text = entity.badge_text
        orm.badge_color = entity.badge_color
        orm.css_class = entity.css_class
        orm.description = entity.description
        orm.help_text = entity.help_text
        orm.keywords = entity.keywords
        orm.created_by = entity.created_by
        orm.updated_by = entity.updated_by

        return orm

    @timing_decorator
    async def create(self, menu: MenuEntity) -> MenuEntity:
        """Criar novo menu com invalidação de cache"""

        # Calcular level baseado no parent
        if menu.parent_id:
            parent = await self.get_by_id(menu.parent_id)
            if not parent:
                raise ValueError(f"Menu pai {menu.parent_id} não encontrado")
            menu.level = parent.level + 1
        else:
            menu.level = 0

        # Auto sort_order (último + 1)
        siblings = await self.get_siblings(menu.parent_id)
        menu.sort_order = max([s.sort_order for s in siblings], default=0) + 1

        # Criar ORM
        menu_orm = self._entity_to_orm(menu)
        self.db.add(menu_orm)
        await self.db.flush()

        # Recalcular caminhos hierárquicos
        await self._update_hierarchy_paths(menu_orm.id)

        await self.db.commit()

        # Invalidar cache relacionado
        cache_service = await self._get_cache_service()
        await cache_service.invalidate_menu_caches()

        # Retornar entidade atualizada
        await self.db.refresh(menu_orm)
        result_entity = self._orm_to_entity(menu_orm)

        # Cachear o novo item
        await cache_service.cache_menu_item(result_entity)

        self.logger.info(
            "Menu criado com sucesso",
            menu_id=result_entity.id,
            name=result_entity.name,
            level=result_entity.level,
        )

        return result_entity

    @timing_decorator
    async def get_by_id(self, menu_id: int) -> Optional[MenuEntity]:
        """Buscar menu por ID com cache"""

        # Tentar cache primeiro
        cache_service = await self._get_cache_service()
        cached_menu = await cache_service.get_menu_item(menu_id)
        if cached_menu:
            return cached_menu

        # Buscar no banco
        query = select(MenuORM).where(
            and_(MenuORM.id == menu_id, MenuORM.deleted_at.is_(None))
        )

        result = await self.db.execute(query)
        menu_orm = result.scalars().first()

        if not menu_orm:
            return None

        entity = self._orm_to_entity(menu_orm)

        # Cachear resultado
        await cache_service.cache_menu_item(entity)

        return entity

    @timing_decorator
    async def get_by_slug(
        self, slug: str, parent_id: Optional[int] = None
    ) -> Optional[MenuEntity]:
        """Buscar menu por slug no nível específico"""

        query = select(MenuORM).where(
            and_(
                MenuORM.slug == slug,
                MenuORM.parent_id == parent_id,
                MenuORM.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        menu_orm = result.scalars().first()

        if menu_orm:
            return self._orm_to_entity(menu_orm)

        return None

    @timing_decorator
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        level: Optional[int] = None,
    ) -> List[MenuEntity]:
        """Listar menus com cache e otimizações"""

        # Tentar cache primeiro
        cache_service = await self._get_cache_service()
        cached_menus = await cache_service.get_menu_list(
            skip, limit, parent_id, status, search, level
        )
        if cached_menus is not None:
            return cached_menus

        # Query otimizada
        query = (
            select(MenuORM)
            .where(MenuORM.deleted_at.is_(None))
            .order_by(MenuORM.level, MenuORM.sort_order, MenuORM.name)
        )

        if parent_id is not None:
            query = query.where(MenuORM.parent_id == parent_id)

        if status:
            query = query.where(MenuORM.status == status)

        if level is not None:
            query = query.where(MenuORM.level == level)

        if search:
            search_filter = or_(
                MenuORM.name.ilike(f"%{search}%"),
                MenuORM.slug.ilike(f"%{search}%"),
                MenuORM.full_path_name.ilike(f"%{search}%"),
                MenuORM.description.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        menus_orm = result.scalars().all()

        # Converter para entidades
        entities = [self._orm_to_entity(menu) for menu in menus_orm]

        # Cachear resultado
        await cache_service.cache_menu_list(
            entities, skip, limit, parent_id, status, search, level
        )

        self.logger.info(
            "Menus listados",
            count=len(entities),
            filters={"parent_id": parent_id, "status": status, "level": level},
        )

        return entities

    @timing_decorator
    async def update(self, menu_id: int, menu: MenuEntity) -> Optional[MenuEntity]:
        """Atualizar menu com validações e cache"""

        # Buscar menu existente
        existing_orm = await self.db.get(MenuORM, menu_id)
        if not existing_orm or existing_orm.deleted_at:
            return None

        # Validações de hierarquia
        if menu.parent_id == menu_id:
            raise ValueError("Menu não pode ser pai de si mesmo")

        if menu.parent_id and not await self.validate_hierarchy_change(
            menu_id, menu.parent_id
        ):
            raise ValueError("Alteração criaria loop na hierarquia")

        # Recalcular level se mudou parent
        if menu.parent_id != existing_orm.parent_id:
            if menu.parent_id:
                parent = await self.get_by_id(menu.parent_id)
                if not parent:
                    raise ValueError(f"Menu pai {menu.parent_id} não encontrado")
                menu.level = parent.level + 1
            else:
                menu.level = 0

        # Aplicar mudanças
        self._entity_to_orm(menu, existing_orm)

        # Recalcular hierarquia se necessário
        if menu.parent_id != existing_orm.parent_id:
            await self._update_hierarchy_paths(menu_id)

        await self.db.commit()

        # Invalidar cache
        cache_service = await self._get_cache_service()
        await cache_service.invalidate_menu_caches(menu_id)

        # Retornar entidade atualizada
        await self.db.refresh(existing_orm)
        result_entity = self._orm_to_entity(existing_orm)

        # Cachear resultado
        await cache_service.cache_menu_item(result_entity)

        self.logger.info("Menu atualizado", menu_id=menu_id, name=result_entity.name)

        return result_entity

    @timing_decorator
    async def delete(self, menu_id: int) -> bool:
        """Excluir menu (soft delete) com validações"""

        # Verificar se tem filhos ativos
        children = await self.get_children(menu_id)
        if children:
            active_children = [c for c in children if c.status == MenuStatus.ACTIVE]
            if active_children:
                raise ValueError(f"Menu possui {len(active_children)} filhos ativos")

        # Soft delete
        query = (
            update(MenuORM)
            .where(and_(MenuORM.id == menu_id, MenuORM.deleted_at.is_(None)))
            .values(deleted_at=func.now())
        )

        result = await self.db.execute(query)

        if result.rowcount == 0:
            return False

        await self.db.commit()

        # Invalidar cache
        cache_service = await self._get_cache_service()
        await cache_service.invalidate_menu_caches(menu_id)

        self.logger.info("Menu excluído", menu_id=menu_id)

        return True

    @timing_decorator
    async def get_hierarchy_tree(
        self,
        user_id: Optional[int] = None,
        context_type: str = "system",
        include_inactive: bool = False,
    ) -> List[MenuEntity]:
        """Buscar árvore hierárquica com cache otimizado"""

        # Tentar cache primeiro
        cache_service = await self._get_cache_service()
        cached_tree = await cache_service.get_menu_tree(user_id, context_type)
        if cached_tree is not None:
            return cached_tree

        # Query recursiva otimizada usando CTE
        query = text(
            """
            WITH RECURSIVE menu_tree AS (
                -- Raiz: menus sem pai
                SELECT
                    id, parent_id, name, slug, url, route_name, icon,
                    level, sort_order, menu_type, status, is_visible, visible_in_menu,
                    permission_name, company_specific, establishment_specific,
                    badge_text, badge_color, css_class, description, help_text,
                    keywords, full_path_name, id_path,
                    created_at, updated_at, created_by, updated_by,
                    ARRAY[id] as path, 0 as depth
                FROM master.menus
                WHERE parent_id IS NULL
                  AND deleted_at IS NULL
                  AND (:include_inactive OR status = 'active')
                  AND is_visible = true

                UNION ALL

                -- Recursivo: filhos
                SELECT
                    m.id, m.parent_id, m.name, m.slug, m.url, m.route_name, m.icon,
                    m.level, m.sort_order, m.menu_type, m.status, m.is_visible, m.visible_in_menu,
                    m.permission_name, m.company_specific, m.establishment_specific,
                    m.badge_text, m.badge_color, m.css_class, m.description, m.help_text,
                    m.keywords, m.full_path_name, m.id_path,
                    m.created_at, m.updated_at, m.created_by, m.updated_by,
                    mt.path || m.id, mt.depth + 1
                FROM master.menus m
                JOIN menu_tree mt ON m.parent_id = mt.id
                WHERE m.deleted_at IS NULL
                  AND (:include_inactive OR m.status = 'active')
                  AND m.is_visible = true
                  AND mt.depth < 4  -- Máximo 5 níveis
            )
            SELECT * FROM menu_tree
            ORDER BY level, sort_order, name
        """
        )

        result = await self.db.execute(query, {"include_inactive": include_inactive})
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
                menu_type=MenuType(row.menu_type) if row.menu_type else MenuType.PAGE,
                status=MenuStatus(row.status) if row.status else MenuStatus.ACTIVE,
                is_visible=row.is_visible,
                visible_in_menu=row.visible_in_menu,
                permission_name=row.permission_name,
                company_specific=row.company_specific,
                establishment_specific=row.establishment_specific,
                badge_text=row.badge_text,
                badge_color=row.badge_color,
                css_class=row.css_class,
                description=row.description,
                help_text=row.help_text,
                keywords=row.keywords or [],
                full_path_name=row.full_path_name,
                id_path=row.id_path or [],
                created_at=row.created_at,
                updated_at=row.updated_at,
                created_by=row.created_by,
                updated_by=row.updated_by,
                children=[],
            )

            menu_dict[entity.id] = entity

            if entity.parent_id is None:
                root_menus.append(entity)
            else:
                parent = menu_dict.get(entity.parent_id)
                if parent:
                    parent.children.append(entity)

        # Cachear resultado
        await cache_service.cache_menu_tree(root_menus, user_id, context_type)

        self.logger.info(
            "Hierarquia de menus carregada",
            total_menus=len(menu_dict),
            root_menus=len(root_menus),
            user_id=user_id,
        )

        return root_menus

    async def get_siblings(self, parent_id: Optional[int]) -> List[MenuEntity]:
        """Buscar menus irmãos (mesmo nível)"""

        query = (
            select(MenuORM)
            .where(and_(MenuORM.parent_id == parent_id, MenuORM.deleted_at.is_(None)))
            .order_by(MenuORM.sort_order, MenuORM.name)
        )

        result = await self.db.execute(query)
        menus_orm = result.scalars().all()

        return [self._orm_to_entity(menu) for menu in menus_orm]

    async def reorder_siblings(
        self, parent_id: Optional[int], menu_orders: List[Dict]
    ) -> bool:
        """Reordenar menus irmãos em lote"""

        try:
            # Update em batch para performance
            for item in menu_orders:
                query = (
                    update(MenuORM)
                    .where(MenuORM.id == item["menu_id"])
                    .values(sort_order=item["sort_order"])
                )
                await self.db.execute(query)

            await self.db.commit()

            # Invalidar cache
            cache_service = await self._get_cache_service()
            await cache_service.invalidate_menu_caches()

            self.logger.info(
                "Menus reordenados", parent_id=parent_id, count=len(menu_orders)
            )

            return True

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Erro ao reordenar menus", error=str(e))
            return False

    async def validate_hierarchy_change(
        self, menu_id: int, new_parent_id: Optional[int]
    ) -> bool:
        """Validar se mudança de hierarquia é válida (não cria loops)"""

        if not new_parent_id:
            return True  # Mover para raiz é sempre válido

        # Verificar se o novo pai é descendente do menu atual
        current_parent_id = new_parent_id

        while current_parent_id:
            if current_parent_id == menu_id:
                return False  # Criaria loop

            parent = await self.get_by_id(current_parent_id)
            if not parent:
                break

            current_parent_id = parent.parent_id

        return True

    async def get_children(
        self, parent_id: int, recursive: bool = False
    ) -> List[MenuEntity]:
        """Buscar filhos de um menu"""

        if recursive:
            # Busca recursiva usando CTE
            query = text(
                """
                WITH RECURSIVE menu_children AS (
                    SELECT id, parent_id, name, slug, level, sort_order,
                           menu_type, status, is_visible
                    FROM master.menus
                    WHERE parent_id = :parent_id
                      AND deleted_at IS NULL

                    UNION ALL

                    SELECT m.id, m.parent_id, m.name, m.slug, m.level, m.sort_order,
                           m.menu_type, m.status, m.is_visible
                    FROM master.menus m
                    JOIN menu_children mc ON m.parent_id = mc.id
                    WHERE m.deleted_at IS NULL
                )
                SELECT * FROM menu_children
                ORDER BY level, sort_order, name
            """
            )

            result = await self.db.execute(query, {"parent_id": parent_id})
            # Simplificada - apenas IDs para este caso de uso
            return []  # Implementação completa seria necessária

        else:
            # Busca direta dos filhos
            query = (
                select(MenuORM)
                .where(
                    and_(MenuORM.parent_id == parent_id, MenuORM.deleted_at.is_(None))
                )
                .order_by(MenuORM.sort_order, MenuORM.name)
            )

            result = await self.db.execute(query)
            menus_orm = result.scalars().all()

            return [self._orm_to_entity(menu) for menu in menus_orm]

    async def count_total(
        self,
        parent_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        """Contar total de menus com filtros"""

        query = select(func.count(MenuORM.id)).where(MenuORM.deleted_at.is_(None))

        if parent_id is not None:
            query = query.where(MenuORM.parent_id == parent_id)

        if status:
            query = query.where(MenuORM.status == status)

        if search:
            search_filter = or_(
                MenuORM.name.ilike(f"%{search}%"),
                MenuORM.slug.ilike(f"%{search}%"),
                MenuORM.full_path_name.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_user_accessible_menus(
        self,
        user_id: int,
        context_type: str = "system",
        context_id: Optional[int] = None,
    ) -> List[MenuEntity]:
        """Buscar menus acessíveis para usuário específico"""

        # Tentar cache primeiro
        cache_service = await self._get_cache_service()
        cached_menus = await cache_service.get_user_menus(
            user_id, context_type, context_id
        )
        if cached_menus is not None:
            return cached_menus

        # Implementação básica - seria expandida com lógica de permissões
        menus = await self.get_hierarchy_tree(user_id, context_type)
        flat_menus = self._flatten_tree(menus)

        # Cachear resultado
        await cache_service.cache_user_menus(
            flat_menus, user_id, context_type, context_id
        )

        return flat_menus

    async def get_menu_path(self, menu_id: int) -> List[MenuEntity]:
        """Buscar caminho completo do menu até a raiz"""

        path = []
        current_id = menu_id

        while current_id:
            menu = await self.get_by_id(current_id)
            if not menu:
                break

            path.insert(0, menu)  # Inserir no início para ordem correta
            current_id = menu.parent_id

        return path

    async def search_menus(
        self,
        query: str,
        user_id: Optional[int] = None,
        context_type: str = "system",
        limit: int = 50,
    ) -> List[MenuEntity]:
        """Busca textual em menus"""

        # Tentar cache primeiro
        cache_service = await self._get_cache_service()
        cached_results = await cache_service.get_search_results(
            query, user_id, context_type, limit
        )
        if cached_results is not None:
            return cached_results

        # Busca com full-text search otimizada
        search_query = (
            select(MenuORM)
            .where(
                and_(
                    MenuORM.deleted_at.is_(None),
                    MenuORM.status == "active",
                    or_(
                        MenuORM.name.ilike(f"%{query}%"),
                        MenuORM.slug.ilike(f"%{query}%"),
                        MenuORM.description.ilike(f"%{query}%"),
                        MenuORM.full_path_name.ilike(f"%{query}%"),
                        func.array_to_string(MenuORM.keywords, " ").ilike(f"%{query}%"),
                    ),
                )
            )
            .order_by(
                # Relevância: nome > slug > descrição > path
                func.case(
                    (MenuORM.name.ilike(f"%{query}%"), 1),
                    (MenuORM.slug.ilike(f"%{query}%"), 2),
                    (MenuORM.description.ilike(f"%{query}%"), 3),
                    else_=4,
                ),
                MenuORM.level,
                MenuORM.sort_order,
            )
            .limit(limit)
        )

        result = await self.db.execute(search_query)
        menus_orm = result.scalars().all()

        entities = [self._orm_to_entity(menu) for menu in menus_orm]

        # Cachear resultado
        await cache_service.cache_search_results(
            entities, query, user_id, context_type, limit
        )

        self.logger.info(
            "Busca de menus realizada", query=query, results_count=len(entities)
        )

        return entities

    async def get_menu_statistics(self) -> Dict[str, Any]:
        """Buscar estatísticas dos menus"""

        # Estatísticas básicas
        stats_query = text(
            """
            SELECT
                COUNT(*) as total_menus,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_menus,
                COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_menus,
                COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_menus,
                COUNT(CASE WHEN parent_id IS NULL THEN 1 END) as root_menus,
                MAX(level) as max_depth,
                COUNT(CASE WHEN permission_name IS NOT NULL THEN 1 END) as menus_with_permissions,
                COUNT(CASE WHEN company_specific = true THEN 1 END) as company_specific_menus,
                COUNT(CASE WHEN establishment_specific = true THEN 1 END) as establishment_specific_menus
            FROM master.menus
            WHERE deleted_at IS NULL
        """
        )

        result = await self.db.execute(stats_query)
        row = result.fetchone()

        # Estatísticas por nível
        level_stats_query = text(
            """
            SELECT level, COUNT(*) as count
            FROM master.menus
            WHERE deleted_at IS NULL
            GROUP BY level
            ORDER BY level
        """
        )

        level_result = await self.db.execute(level_stats_query)
        menus_by_level = {str(r.level): r.count for r in level_result.fetchall()}

        # Estatísticas por tipo
        type_stats_query = text(
            """
            SELECT menu_type, COUNT(*) as count
            FROM master.menus
            WHERE deleted_at IS NULL
            GROUP BY menu_type
        """
        )

        type_result = await self.db.execute(type_stats_query)
        menus_by_type = {r.menu_type: r.count for r in type_result.fetchall()}

        return {
            "total_menus": row.total_menus or 0,
            "active_menus": row.active_menus or 0,
            "inactive_menus": row.inactive_menus or 0,
            "draft_menus": row.draft_menus or 0,
            "root_menus": row.root_menus or 0,
            "max_depth": row.max_depth or 0,
            "menus_with_permissions": row.menus_with_permissions or 0,
            "company_specific_menus": row.company_specific_menus or 0,
            "establishment_specific_menus": row.establishment_specific_menus or 0,
            "menus_by_level": menus_by_level,
            "menus_by_type": menus_by_type,
            "avg_children_per_menu": (row.total_menus - row.root_menus)
            / max(row.root_menus, 1),
        }

    async def bulk_update_status(self, menu_ids: List[int], status: str) -> bool:
        """Atualizar status de múltiplos menus em lote"""

        try:
            query = (
                update(MenuORM)
                .where(and_(MenuORM.id.in_(menu_ids), MenuORM.deleted_at.is_(None)))
                .values(status=status)
            )

            result = await self.db.execute(query)
            await self.db.commit()

            # Invalidar cache
            cache_service = await self._get_cache_service()
            await cache_service.invalidate_menu_caches()

            self.logger.info(
                "Status de menus atualizado em lote",
                menu_ids=menu_ids,
                new_status=status,
                updated_count=result.rowcount,
            )

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Erro na atualização em lote", error=str(e))
            return False

    async def get_recently_modified(
        self, limit: int = 10, user_id: Optional[int] = None
    ) -> List[MenuEntity]:
        """Buscar menus modificados recentemente"""

        query = select(MenuORM).where(MenuORM.deleted_at.is_(None))

        if user_id:
            query = query.where(MenuORM.updated_by == user_id)

        query = query.order_by(MenuORM.updated_at.desc()).limit(limit)

        result = await self.db.execute(query)
        menus_orm = result.scalars().all()

        return [self._orm_to_entity(menu) for menu in menus_orm]

    async def _update_hierarchy_paths(self, menu_id: int):
        """Atualizar caminhos hierárquicos (full_path_name, id_path)"""

        query = text(
            """
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
        """
        )

        await self.db.execute(query, {"menu_id": menu_id})

    def _flatten_tree(self, tree: List[MenuEntity]) -> List[MenuEntity]:
        """Achatar árvore em lista plana"""
        flat_list = []
        for node in tree:
            flat_list.append(node)
            flat_list.extend(self._flatten_tree(node.children))
        return flat_list
