"""
Menus CRUD Simples - Endpoints básicos usando estrutura real do banco
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/menus/simple", tags=["Menus CRUD Simples"])
logger = get_logger()


class MenuUpdateRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None


class MenuCreateRequest(BaseModel):
    parent_id: Optional[int] = None
    name: str
    slug: str
    url: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_visible: bool = True


@router.put("/{menu_id}")
async def update_menu_simple(
    menu_id: int,
    update_data: MenuUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualizar menu usando apenas colunas que existem no banco"""
    
    try:
        # Primeiro verificar se o menu existe
        check_query = text("SELECT id, name FROM master.menus WHERE id = :menu_id AND deleted_at IS NULL")
        result = await db.execute(check_query, {"menu_id": menu_id})
        existing_menu = result.fetchone()
        
        if not existing_menu:
            raise HTTPException(status_code=404, detail="Menu não encontrado")
        
        # Construir query de update dinâmicamente apenas com campos que existem
        update_fields = []
        update_values = {"menu_id": menu_id}
        
        if update_data.name is not None:
            update_fields.append("name = :name")
            update_values["name"] = update_data.name
            
        if update_data.slug is not None:
            update_fields.append("slug = :slug")
            update_values["slug"] = update_data.slug
            
        if update_data.url is not None:
            update_fields.append("url = :url")
            update_values["url"] = update_data.url
            
        if update_data.icon is not None:
            update_fields.append("icon = :icon")
            update_values["icon"] = update_data.icon
            
        if update_data.sort_order is not None:
            update_fields.append("sort_order = :sort_order")
            update_values["sort_order"] = update_data.sort_order
            
        if update_data.is_visible is not None:
            update_fields.append("is_visible = :is_visible")
            update_values["is_visible"] = update_data.is_visible
        
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
            SELECT id, parent_id, name, slug, url, icon, level, sort_order, 
                   is_visible, created_at, updated_at
            FROM master.menus 
            WHERE id = :menu_id AND deleted_at IS NULL
        """)
        
        result = await db.execute(select_query, {"menu_id": menu_id})
        updated_menu = result.fetchone()
        
        logger.info("Menu atualizado via CRUD simples", menu_id=menu_id, user_id=current_user.id)
        
        return {
            "success": True,
            "message": "Menu atualizado com sucesso",
            "menu": {
                "id": updated_menu.id,
                "parent_id": updated_menu.parent_id,
                "name": updated_menu.name,
                "slug": updated_menu.slug,
                "url": updated_menu.url,
                "icon": updated_menu.icon,
                "level": updated_menu.level,
                "sort_order": updated_menu.sort_order,
                "is_visible": updated_menu.is_visible,
                "created_at": updated_menu.created_at.isoformat() if updated_menu.created_at else None,
                "updated_at": updated_menu.updated_at.isoformat() if updated_menu.updated_at else None
            }
        }
        
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao atualizar menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/")
async def create_menu_simple(
    menu_data: MenuCreateRequest,
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
                parent_id, name, slug, url, icon, level, sort_order, 
                is_visible, created_at, updated_at
            ) VALUES (
                :parent_id, :name, :slug, :url, :icon, :level, :sort_order,
                :is_visible, NOW(), NOW()
            ) RETURNING id
        """)
        
        result = await db.execute(insert_query, {
            "parent_id": menu_data.parent_id,
            "name": menu_data.name,
            "slug": menu_data.slug,
            "url": menu_data.url,
            "icon": menu_data.icon,
            "level": level,
            "sort_order": menu_data.sort_order,
            "is_visible": menu_data.is_visible
        })
        
        new_menu_id = result.fetchone().id
        await db.commit()
        
        logger.info("Menu criado via CRUD simples", menu_id=new_menu_id, user_id=current_user.id)
        
        return {
            "success": True,
            "message": "Menu criado com sucesso",
            "menu_id": new_menu_id
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao criar menu", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.delete("/{menu_id}")
async def delete_menu_simple(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Excluir menu (soft delete) usando estrutura real do banco"""
    
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
        children_count = result.fetchone().count
        
        if children_count > 0:
            raise HTTPException(status_code=400, detail="Menu possui submenus ativos. Remova os submenus primeiro.")
        
        # Soft delete
        delete_query = text("UPDATE master.menus SET deleted_at = NOW() WHERE id = :menu_id")
        await db.execute(delete_query, {"menu_id": menu_id})
        await db.commit()
        
        logger.info("Menu excluído via CRUD simples", menu_id=menu_id, user_id=current_user.id)
        
        return {
            "success": True,
            "message": "Menu excluído com sucesso"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Erro ao excluir menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/{menu_id}")
async def get_menu_simple(
    menu_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Buscar menu por ID usando estrutura real do banco"""
    
    try:
        query = text("""
            SELECT id, parent_id, name, slug, url, icon, level, sort_order,
                   is_visible, created_at, updated_at
            FROM master.menus 
            WHERE id = :menu_id AND deleted_at IS NULL
        """)
        
        result = await db.execute(query, {"menu_id": menu_id})
        menu = result.fetchone()
        
        if not menu:
            raise HTTPException(status_code=404, detail="Menu não encontrado")
        
        return {
            "id": menu.id,
            "parent_id": menu.parent_id,
            "name": menu.name,
            "slug": menu.slug,
            "url": menu.url,
            "icon": menu.icon,
            "level": menu.level,
            "sort_order": menu.sort_order,
            "is_visible": menu.is_visible,
            "created_at": menu.created_at.isoformat() if menu.created_at else None,
            "updated_at": menu.updated_at.isoformat() if menu.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao buscar menu", error=str(e), menu_id=menu_id)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")