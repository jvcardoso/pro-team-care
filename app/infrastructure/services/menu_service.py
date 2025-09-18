"""
Menu Service - Sistema de menus dinâmicos baseado em permissões
Integra com views PostgreSQL e sistema de segurança
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, select, text

from app.infrastructure.cache.decorators import cache_invalidate, cached
from app.infrastructure.orm.views import MenuHierarchyView
from app.infrastructure.services.security_service import SecurityService

logger = structlog.get_logger()


@dataclass
class MenuItem:
    """Menu item with permissions and context"""

    id: int
    name: str
    slug: str
    path: str
    url: Optional[str]
    route_name: Optional[str]
    route_params: Optional[Dict[str, Any]]
    level: int
    sort_order: int
    parent_id: Optional[int]
    icon: Optional[str]
    badge_text: Optional[str]
    badge_color: Optional[str]
    css_class: Optional[str]
    description: Optional[str]
    help_text: Optional[str]
    permission_name: Optional[str]
    is_visible: bool
    visible_in_menu: bool
    children: List["MenuItem"]


@dataclass
class MenuContext:
    """Context for menu rendering"""

    user_id: int
    company_id: Optional[int]
    establishment_id: Optional[int]
    role_level: int
    is_system_admin: bool
    active_permissions: List[str]


class MenuService:
    """
    Serviço de menus dinâmicos com base em permissões e contexto organizacional
    """

    def __init__(self, session, security_service: SecurityService):
        self.session = session
        self.security_service = security_service

    @cached(
        ttl=300,  # 5 minutos
        key_prefix="menu_tree",
        invalidate_patterns=["cache:func:*menu*"],
    )
    async def get_user_menu_tree(
        self,
        user_id: int,
        menu_type: str = "main",
        company_id: Optional[int] = None,
        establishment_id: Optional[int] = None,
    ) -> List[MenuItem]:
        """
        Busca árvore de menus para usuário baseado em permissões
        """
        try:
            # Buscar contexto do usuário
            context = await self._get_menu_context(
                user_id=user_id,
                company_id=company_id,
                establishment_id=establishment_id,
            )

            # Buscar menus com hierarquia
            query = (
                select(MenuHierarchyView)
                .where(
                    and_(
                        MenuHierarchyView.menu_type == menu_type,
                        MenuHierarchyView.status == "ACTIVE",
                        MenuHierarchyView.is_visible == True,
                        MenuHierarchyView.deleted_at.is_(None),
                    )
                )
                .order_by(
                    MenuHierarchyView.level.asc(), MenuHierarchyView.sort_order.asc()
                )
            )

            result = await self.session.execute(query)
            menu_data = result.scalars().all()

            # Filtrar por permissões
            filtered_menus = []
            for menu_item in menu_data:
                if await self._user_can_access_menu(context, menu_item):
                    filtered_menus.append(menu_item)

            # Construir árvore
            menu_tree = self._build_menu_tree(filtered_menus)

            await logger.ainfo(
                "user_menu_tree_built",
                user_id=user_id,
                menu_type=menu_type,
                total_items=len(filtered_menus),
                tree_roots=len(menu_tree),
            )

            return menu_tree

        except Exception as e:
            await logger.aerror(
                "menu_tree_build_failed",
                user_id=user_id,
                menu_type=menu_type,
                error=str(e),
            )
            return []

    async def get_contextual_menu(
        self,
        user_id: int,
        context_type: str,  # "dashboard", "profile", "admin", "reports"
        context_data: Optional[Dict[str, Any]] = None,
    ) -> List[MenuItem]:
        """
        Busca menu contextual baseado na tela/módulo atual
        """
        try:
            # Buscar menus específicos do contexto
            query = text(
                """
                SELECT * FROM master.fn_get_contextual_menu(
                    :user_id, :context_type, :context_data
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "context_type": context_type,
                    "context_data": context_data or {},
                },
            )

            contextual_items = []
            for row in result.fetchall():
                contextual_items.append(
                    MenuItem(
                        id=row.id,
                        name=row.name,
                        slug=row.slug,
                        path=row.path,
                        url=row.url,
                        route_name=row.route_name,
                        route_params=row.route_params,
                        level=0,  # Contextual menus are flat
                        sort_order=row.sort_order,
                        parent_id=None,
                        icon=row.icon,
                        badge_text=row.badge_text,
                        badge_color=row.badge_color,
                        css_class=row.css_class,
                        description=row.description,
                        help_text=row.help_text,
                        permission_name=row.permission_name,
                        is_visible=row.is_visible,
                        visible_in_menu=row.visible_in_menu,
                        children=[],
                    )
                )

            await logger.ainfo(
                "contextual_menu_built",
                user_id=user_id,
                context_type=context_type,
                items_count=len(contextual_items),
            )

            return contextual_items

        except Exception as e:
            await logger.aerror(
                "contextual_menu_failed",
                user_id=user_id,
                context_type=context_type,
                error=str(e),
            )
            return []

    async def get_breadcrumb_path(
        self,
        user_id: int,
        current_route: str,
        route_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Gera breadcrumb baseado na rota atual
        """
        try:
            query = text(
                """
                SELECT * FROM master.fn_build_breadcrumb(
                    :user_id, :current_route, :route_params
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "current_route": current_route,
                    "route_params": route_params or {},
                },
            )

            breadcrumb = []
            for row in result.fetchall():
                breadcrumb.append(
                    {
                        "name": row.name,
                        "url": row.url,
                        "route_name": row.route_name,
                        "route_params": row.route_params,
                        "is_active": row.is_active,
                    }
                )

            return breadcrumb

        except Exception as e:
            await logger.aerror(
                "breadcrumb_build_failed",
                user_id=user_id,
                current_route=current_route,
                error=str(e),
            )
            return []

    async def get_user_shortcuts(self, user_id: int, limit: int = 10) -> List[MenuItem]:
        """
        Busca shortcuts/favoritos do usuário
        """
        try:
            query = text(
                """
                SELECT m.*, us.sort_order as user_sort_order
                FROM master.user_shortcuts us
                JOIN master.vw_menu_hierarchy m ON m.id = us.menu_id
                WHERE us.user_id = :user_id
                  AND us.is_active = true
                  AND m.status = 'ACTIVE'
                  AND m.deleted_at IS NULL
                ORDER BY us.sort_order, m.name
                LIMIT :limit
            """
            )

            result = await self.session.execute(
                query, {"user_id": user_id, "limit": limit}
            )

            shortcuts = []
            for row in result.fetchall():
                shortcuts.append(
                    MenuItem(
                        id=row.id,
                        name=row.name,
                        slug=row.slug,
                        path=row.path,
                        url=row.url,
                        route_name=row.route_name,
                        route_params=row.route_params,
                        level=0,
                        sort_order=row.user_sort_order,
                        parent_id=None,
                        icon=row.icon,
                        badge_text=row.badge_text,
                        badge_color=row.badge_color,
                        css_class=row.css_class,
                        description=row.description,
                        help_text=row.help_text,
                        permission_name=row.permission_name,
                        is_visible=row.is_visible,
                        visible_in_menu=row.visible_in_menu,
                        children=[],
                    )
                )

            await logger.ainfo(
                "user_shortcuts_retrieved",
                user_id=user_id,
                shortcuts_count=len(shortcuts),
            )

            return shortcuts

        except Exception as e:
            await logger.aerror("user_shortcuts_failed", user_id=user_id, error=str(e))
            return []

    async def add_user_shortcut(
        self, user_id: int, menu_id: int, sort_order: Optional[int] = None
    ) -> bool:
        """
        Adiciona shortcut para usuário
        """
        try:
            query = text(
                """
                INSERT INTO master.user_shortcuts (user_id, menu_id, sort_order, is_active)
                VALUES (:user_id, :menu_id, :sort_order, true)
                ON CONFLICT (user_id, menu_id)
                DO UPDATE SET sort_order = :sort_order, is_active = true
            """
            )

            await self.session.execute(
                query,
                {
                    "user_id": user_id,
                    "menu_id": menu_id,
                    "sort_order": sort_order or 999,
                },
            )

            await self.session.commit()

            await logger.ainfo("user_shortcut_added", user_id=user_id, menu_id=menu_id)

            return True

        except Exception as e:
            await logger.aerror(
                "add_shortcut_failed", user_id=user_id, menu_id=menu_id, error=str(e)
            )
            return False

    async def _get_menu_context(
        self,
        user_id: int,
        company_id: Optional[int] = None,
        establishment_id: Optional[int] = None,
    ) -> MenuContext:
        """
        Busca contexto completo para renderização de menus
        """
        # Buscar perfis disponíveis do usuário
        profiles = await self.security_service.get_available_profiles(user_id)

        # Buscar permissões ativas
        permissions = await self.security_service.get_user_permissions(user_id)

        # Determinar contexto atual (primeiro perfil ativo ou padrão)
        current_profile = profiles[0] if profiles else None

        return MenuContext(
            user_id=user_id,
            company_id=company_id
            or (current_profile.get("company_id") if current_profile else None),
            establishment_id=establishment_id
            or (current_profile.get("establishment_id") if current_profile else None),
            role_level=current_profile.get("role_level", 0) if current_profile else 0,
            is_system_admin=(
                current_profile.get("is_system_admin", False)
                if current_profile
                else False
            ),
            active_permissions=permissions,
        )

    async def _user_can_access_menu(self, context: MenuContext, menu_item) -> bool:
        """
        Verifica se usuário pode acessar item de menu
        """
        try:
            # Se não tem permissão requerida, pode acessar
            if not menu_item.permission_name:
                return True

            # Admins podem acessar tudo
            if context.is_system_admin:
                return True

            # Verificar permissão específica
            if menu_item.permission_name in context.active_permissions:
                return True

            # Verificar contexto específico (company/establishment)
            if menu_item.company_specific and not context.company_id:
                return False

            if menu_item.establishment_specific and not context.establishment_id:
                return False

            return False

        except Exception as e:
            await logger.aerror(
                "menu_access_check_failed",
                user_id=context.user_id,
                menu_id=menu_item.id,
                error=str(e),
            )
            return False

    def _build_menu_tree(self, menu_items: List) -> List[MenuItem]:
        """
        Constrói árvore hierárquica de menus
        """
        # Converter para MenuItem objects
        items = []
        for item in menu_items:
            menu_item = MenuItem(
                id=item.id,
                name=item.name,
                slug=item.slug,
                path=item.path,
                url=item.url,
                route_name=item.route_name,
                route_params=item.route_params,
                level=item.level,
                sort_order=item.sort_order,
                parent_id=item.parent_id,
                icon=item.icon,
                badge_text=item.badge_text,
                badge_color=item.badge_color,
                css_class=item.css_class,
                description=item.description,
                help_text=item.help_text,
                permission_name=item.permission_name,
                is_visible=item.is_visible,
                visible_in_menu=item.visible_in_menu,
                children=[],
            )
            items.append(menu_item)

        # Organizar em árvore
        items_by_id = {item.id: item for item in items}
        roots = []

        for item in items:
            if item.parent_id and item.parent_id in items_by_id:
                items_by_id[item.parent_id].children.append(item)
            else:
                roots.append(item)

        return roots


# Factory function para dependency injection
def get_menu_service(db, security_service: SecurityService) -> MenuService:
    """Factory function for MenuService"""
    return MenuService(db, security_service)
