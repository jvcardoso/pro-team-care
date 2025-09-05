"""
Menus CRUD API - Presentation Layer
Endpoints FastAPI compatíveis com estrutura real do banco de dados
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from structlog import get_logger
from pydantic import BaseModel
from datetime import datetime

from app.infrastructure.database import get_db
from app.infrastructure.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/menus/crud", tags=["Menus CRUD"])
logger = get_logger()


# Schemas compatíveis com a estrutura real do banco
class MenuCreateSchema(BaseModel):
    parent_id: Optional[int] = None
    name: str
    slug: str
    url: Optional[str] = None
    route_name: Optional[str] = None
    route_params: Optional[str] = None
    icon: Optional[str] = None
    permission_name: Optional[str] = None
    description: Optional[str] = None
    is_visible: bool = True
    visible_in_menu: bool = True


class MenuUpdateSchema(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    route_name: Optional[str] = None
    route_params: Optional[str] = None
    icon: Optional[str] = None
    permission_name: Optional[str] = None
    description: Optional[str] = None
    is_visible: Optional[bool] = None
    visible_in_menu: Optional[bool] = None
    sort_order: Optional[int] = None


class MenuListSchema(BaseModel):
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    level: int
    sort_order: int
    is_visible: bool
    visible_in_menu: bool
    permission_name: Optional[str]
    has_children: bool
    children_count: int
    icon: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    created_by: Optional[int]
    updated_by: Optional[int]


class MenuDetailedSchema(BaseModel):
    id: int
    parent_id: Optional[int]
    name: str
    slug: str
    url: Optional[str]
    route_name: Optional[str]
    route_params: Optional[str]
    level: int
    sort_order: int
    is_visible: bool
    visible_in_menu: bool
    permission_name: Optional[str]
    icon: Optional[str]
    description: Optional[str]
    has_children: bool
    children_count: int
    created_at: Optional[str]
    updated_at: Optional[str]
    created_by: Optional[int]
    updated_by: Optional[int]


class MenuListResponse(BaseModel):
    data: List[MenuListSchema]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class MenuOperationResultSchema(BaseModel):
    success: bool
    message: str
    errors: List[str] = []
    warnings: List[str] = []


@router.post(
    "/",
    response_model=MenuDetailedSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Menu",
    description="Cria um novo menu compatível com a estrutura real do banco de dados"
)
async def create_menu(
    menu_data: MenuCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Criar novo menu usando apenas colunas que existem no banco"""

    try:
        # Verificar se slug já existe no mesmo nível
        check_slug_query = text("""
            SELECT id FROM master.menus
            WHERE slug = :slug AND parent_id IS NOT DISTINCT FROM :parent_id
            AND deleted_at IS NULL
        """)

        result = await db.execute(check_slug_query, {
            "slug": menu_data.slug,
            "parent_id": menu_data.parent_id
        })

        if result.fetchone():
            raise HTTPException(status_code=400, detail="Slug já existe neste nível")

        # Determinar nível baseado no parent
        level = 0
        if menu_data.parent_id:
            level_query = text("SELECT level FROM master.menus WHERE id = :parent_id AND deleted_at IS NULL")
            result = await db.execute(level_query, {"parent_id": menu_data.parent_id})
            parent = result.fetchone()
            if parent:
                level = parent.level + 1
            else:
                raise HTTPException(status_code=400, detail="Menu pai não encontrado")

        # Inserir novo menu
        insert_query = text("""
            INSERT INTO master.menus (
                parent_id, name, slug, url, route_name, route_params, icon,
                permission_name, description, level, sort_order,
                is_visible, visible_in_menu, created_at, updated_at
            ) VALUES (
                :parent_id, :name, :slug, :url, :route_name, :route_params, :icon,
                :permission_name, :description, :level, :sort_order,
                :is_visible, :visible_in_menu, NOW(), NOW()
            ) RETURNING id
        """)

        result = await db.execute(insert_query, {
            "parent_id": menu_data.parent_id,
            "name": menu_data.name,
            "slug": menu_data.slug,
            "url": menu_data.url,
            "route_name": menu_data.route_name,
            "route_params": menu_data.route_params,
            "icon": menu_data.icon,
            "permission_name": menu_data.permission_name,
            "description": menu_data.description,
            "level": level,
            "sort_order": 0,  # TODO: implementar auto-ordenação
            "is_visible": menu_data.is_visible,
            "visible_in_menu": menu_data.visible_in_menu
        })

        new_menu_row = result.fetchone()
        if not new_menu_row:
            raise HTTPException(status_code=500, detail="Erro ao obter ID do menu criado")

        new_menu_id = new_menu_row.id
        await db.commit()

        # Buscar menu criado
        select_query = text("""
            SELECT id, parent_id, name, slug, url, route_name, route_params,
                   icon, permission_name, description, level, sort_order,
                   is_visible, visible_in_menu, created_at, updated_at
            FROM master.menus
            WHERE id = :menu_id AND deleted_at IS NULL
        """)

        result = await db.execute(select_query, {"menu_id": new_menu_id})
        menu = result.fetchone()

        if not menu:
            raise HTTPException(status_code=500, detail="Erro ao buscar menu criado")

        logger.info("Menu criado via CRUD", menu_id=new_menu_id, user_id=current_user.id)

        return MenuDetailedSchema(
            id=menu.id,
            parent_id=menu.parent_id,
            name=menu.name,
            slug=menu.slug,
            url=menu.url,
            route_name=menu.route_name,
            route_params=menu.route_params,
            level=menu.level,
            sort_order=menu.sort_order,
            is_visible=menu.is_visible,
            visible_in_menu=menu.visible_in_menu,
            permission_name=menu.permission_name,
            icon=menu.icon,
            description=menu.description,
            has_children=False,  # Novo menu não tem filhos
            children_count=0,
            created_at=menu.created_at.isoformat() if menu.created_at else "",
            updated_at=menu.updated_at.isoformat() if menu.updated_at else "",
            created_by=current_user.id,
            updated_by=current_user.id
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao criar menu", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get(
    "/",
    response_model=MenuListResponse,
    summary="Listar Menus",
    description="Lista menus com paginação compatível com a estrutura do banco"
)
async def get_menus(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Listar menus com paginação"""

    try:
        # Construir query base
        base_query = """
            SELECT
                m.id, m.parent_id, m.name, m.slug, m.level, m.sort_order,
                m.is_visible, m.visible_in_menu, m.permission_name, m.icon,
                m.created_at, m.updated_at,
                CASE WHEN COUNT(c.id) > 0 THEN true ELSE false END as has_children,
                COUNT(c.id) as children_count
            FROM master.menus m
            LEFT JOIN master.menus c ON c.parent_id = m.id AND c.deleted_at IS NULL
            WHERE m.deleted_at IS NULL
            AND m.is_visible = true
            AND m.visible_in_menu = true
        """

        count_query = "SELECT COUNT(*) as total FROM master.menus WHERE deleted_at IS NULL AND is_visible = true AND visible_in_menu = true"

        params = {}
        where_conditions = []

        if parent_id is not None:
            where_conditions.append("m.parent_id = :parent_id")
            params["parent_id"] = parent_id

        if search:
            where_conditions.append("(m.name ILIKE :search OR m.slug ILIKE :search)")
            params["search"] = f"%{search}%"

        if where_conditions:
            where_clause = " AND " + " AND ".join(where_conditions)
            base_query += where_clause
            count_query += where_clause

        base_query += " GROUP BY m.id ORDER BY m.level, m.sort_order, m.name"
        base_query += " LIMIT :limit OFFSET :skip"

        params["limit"] = limit
        params["skip"] = skip

        # Executar queries
        result = await db.execute(text(base_query), params)
        menus = result.fetchall()

        result = await db.execute(text(count_query), params)
        total_row = result.fetchone()
        total = total_row.total if total_row else 0

        # Converter para schemas
        menu_schemas = []
        for menu in menus:
            schema = MenuListSchema(
                id=menu.id,
                parent_id=menu.parent_id,
                name=menu.name,
                slug=menu.slug,
                level=menu.level,
                sort_order=menu.sort_order,
                is_visible=menu.is_visible,
                visible_in_menu=menu.visible_in_menu,
                permission_name=menu.permission_name,
                has_children=menu.has_children,
                children_count=menu.children_count,
                icon=menu.icon,
                created_at=menu.created_at.isoformat() if menu.created_at else None,
                updated_at=menu.updated_at.isoformat() if menu.updated_at else None,
                created_by=None,  # TODO: implementar quando campo existir
                updated_by=None
            )
            menu_schemas.append(schema)

        # Calcular paginação
        page = (skip // limit) + 1
        has_next = skip + limit < total
        has_prev = skip > 0

        logger.info("Menus listados via API", count=len(menus), total=total, user_id=current_user.id)

        return MenuListResponse(
            data=menu_schemas,
            total=total,
            page=page,
            per_page=limit,
            has_next=has_next,
            has_prev=has_prev
        )

    except Exception as e:
        logger.error("Erro ao listar menus", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get(
    "/{menu_id}",
    response_model=MenuDetailedSchema,
    summary="Buscar Menu por ID",
    description="Retorna dados completos de um menu específico"
)
async def get_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Buscar menu por ID"""

    try:
        query = text("""
            SELECT
                m.id, m.parent_id, m.name, m.slug, m.url, m.route_name, m.route_params,
                m.icon, m.permission_name, m.description, m.level, m.sort_order,
                m.is_visible, m.visible_in_menu, m.created_at, m.updated_at,
                CASE WHEN COUNT(c.id) > 0 THEN true ELSE false END as has_children,
                COUNT(c.id) as children_count
            FROM master.menus m
            LEFT JOIN master.menus c ON c.parent_id = m.id AND c.deleted_at IS NULL
            WHERE m.id = :menu_id AND m.deleted_at IS NULL
            GROUP BY m.id
        """)

        result = await db.execute(query, {"menu_id": menu_id})
        menu = result.fetchone()

        if not menu:
            raise HTTPException(status_code=404, detail="Menu não encontrado")

        return MenuDetailedSchema(
            id=menu.id,
            parent_id=menu.parent_id,
            name=menu.name,
            slug=menu.slug,
            url=menu.url,
            route_name=menu.route_name,
            route_params=menu.route_params,
            level=menu.level,
            sort_order=menu.sort_order,
            is_visible=menu.is_visible,
            visible_in_menu=menu.visible_in_menu,
            permission_name=menu.permission_name,
            icon=menu.icon,
            description=menu.description,
            has_children=menu.has_children,
            children_count=menu.children_count,
            created_at=menu.created_at.isoformat() if menu.created_at else None,
            updated_at=menu.updated_at.isoformat() if menu.updated_at else None,
            created_by=None,  # TODO: implementar quando campo existir
            updated_by=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao buscar menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.put(
    "/{menu_id}",
    response_model=MenuDetailedSchema,
    summary="Atualizar Menu",
    description="Atualiza dados de um menu existente"
)
async def update_menu(
    menu_id: int,
    menu_data: MenuUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualizar menu com validações"""

    try:
        # Verificar se menu existe
        check_query = text("SELECT id, name FROM master.menus WHERE id = :menu_id AND deleted_at IS NULL")
        result = await db.execute(check_query, {"menu_id": menu_id})
        existing_menu = result.fetchone()

        if not existing_menu:
            raise HTTPException(status_code=404, detail="Menu não encontrado")

        # Verificar slug único se foi fornecido
        if menu_data.slug:
            check_slug_query = text("""
                SELECT id FROM master.menus
                WHERE slug = :slug AND parent_id IS NOT DISTINCT FROM :parent_id
                AND id != :menu_id AND deleted_at IS NULL
            """)

            result = await db.execute(check_slug_query, {
                "slug": menu_data.slug,
                "parent_id": menu_data.parent_id,
                "menu_id": menu_id
            })

            if result.fetchone():
                raise HTTPException(status_code=400, detail="Slug já existe neste nível")

        # Construir query de update dinamicamente
        update_fields = []
        update_values = {"menu_id": menu_id}

        if menu_data.name is not None:
            update_fields.append("name = :name")
            update_values["name"] = str(menu_data.name)

        if menu_data.slug is not None:
            update_fields.append("slug = :slug")
            update_values["slug"] = str(menu_data.slug)

        if menu_data.url is not None:
            update_fields.append("url = :url")
            update_values["url"] = str(menu_data.url)

        if menu_data.route_name is not None:
            update_fields.append("route_name = :route_name")
            update_values["route_name"] = str(menu_data.route_name)

        if menu_data.route_params is not None:
            update_fields.append("route_params = :route_params")
            update_values["route_params"] = str(menu_data.route_params)

        if menu_data.icon is not None:
            update_fields.append("icon = :icon")
            update_values["icon"] = str(menu_data.icon)

        if menu_data.permission_name is not None:
            update_fields.append("permission_name = :permission_name")
            update_values["permission_name"] = str(menu_data.permission_name)

        if menu_data.description is not None:
            update_fields.append("description = :description")
            update_values["description"] = str(menu_data.description)

        if menu_data.is_visible is not None:
            update_fields.append("is_visible = :is_visible")
            update_values["is_visible"] = bool(menu_data.is_visible)

        if menu_data.visible_in_menu is not None:
            update_fields.append("visible_in_menu = :visible_in_menu")
            update_values["visible_in_menu"] = bool(menu_data.visible_in_menu)

        if menu_data.sort_order is not None:
            update_fields.append("sort_order = :sort_order")
            update_values["sort_order"] = int(menu_data.sort_order)

        if not update_fields:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

        # Executar update
        update_query = text(f"""
            UPDATE master.menus
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :menu_id AND deleted_at IS NULL
        """)

        await db.execute(update_query, update_values)
        await db.commit()

        # Buscar menu atualizado
        select_query = text("""
            SELECT
                m.id, m.parent_id, m.name, m.slug, m.url, m.route_name, m.route_params,
                m.icon, m.permission_name, m.description, m.level, m.sort_order,
                m.is_visible, m.visible_in_menu, m.created_at, m.updated_at,
                CASE WHEN COUNT(c.id) > 0 THEN true ELSE false END as has_children,
                COUNT(c.id) as children_count
            FROM master.menus m
            LEFT JOIN master.menus c ON c.parent_id = m.id AND c.deleted_at IS NULL
            WHERE m.id = :menu_id AND m.deleted_at IS NULL
            GROUP BY m.id
        """)

        result = await db.execute(select_query, {"menu_id": menu_id})
        updated_menu = result.fetchone()

        if not updated_menu:
            raise HTTPException(status_code=500, detail="Erro ao buscar menu atualizado")

        logger.info("Menu atualizado via API", menu_id=menu_id, updated_by=current_user.id)

        return MenuDetailedSchema(
            id=updated_menu.id,
            parent_id=updated_menu.parent_id,
            name=updated_menu.name,
            slug=updated_menu.slug,
            url=updated_menu.url,
            route_name=updated_menu.route_name,
            route_params=updated_menu.route_params,
            level=updated_menu.level,
            sort_order=updated_menu.sort_order,
            is_visible=updated_menu.is_visible,
            visible_in_menu=updated_menu.visible_in_menu,
            permission_name=updated_menu.permission_name,
            icon=updated_menu.icon,
            description=updated_menu.description,
            has_children=updated_menu.has_children,
            children_count=updated_menu.children_count,
            created_at=updated_menu.created_at.isoformat() if updated_menu.created_at else None,
            updated_at=updated_menu.updated_at.isoformat() if updated_menu.updated_at else None,
            created_by=None,
            updated_by=current_user.id
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao atualizar menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Menu",
    description="Exclui um menu do sistema (soft delete)"
)
async def delete_menu(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Excluir menu (soft delete)"""

    try:
        # Verificar se menu existe
        check_query = text("SELECT id, name FROM master.menus WHERE id = :menu_id AND deleted_at IS NULL")
        result = await db.execute(check_query, {"menu_id": menu_id})
        existing_menu = result.fetchone()

        if not existing_menu:
            raise HTTPException(status_code=404, detail="Menu não encontrado")

        # Verificar se tem filhos ativos
        children_query = text("SELECT COUNT(*) as count FROM master.menus WHERE parent_id = :menu_id AND deleted_at IS NULL")
        result = await db.execute(children_query, {"menu_id": menu_id})
        children_row = result.fetchone()
        children_count = children_row.count if children_row and hasattr(children_row, 'count') else 0

        if children_count > 0:
            raise HTTPException(status_code=400, detail="Menu possui submenus ativos. Remova os submenus primeiro.")

        # Soft delete
        delete_query = text("UPDATE master.menus SET deleted_at = NOW() WHERE id = :menu_id")
        await db.execute(delete_query, {"menu_id": menu_id})
        await db.commit()

        logger.info("Menu excluído via API", menu_id=menu_id, deleted_by=current_user.id)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao excluir menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")