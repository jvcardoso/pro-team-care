"""
Menu Repository - Sistema de Menus Dinâmicos
Responsável por buscar e filtrar menus baseado em permissões de usuário
"""

import os
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

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
                logger.warning("Método lento detectado",
                              method=func.__name__,
                              execution_time=f"{execution_time:.3f}s",
                              threshold="100ms")

            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error("Erro em método com timing",
                        method=func.__name__,
                        execution_time=f"{execution_time:.3f}s",
                        error=str(e))
            raise

    return wrapper


class MenuRepository:
    """Repository para gerenciamento de menus dinâmicos"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @timing_decorator
    async def get_user_menus(
        self,
        user_id: int,
        context_type: str = "establishment",
        context_id: Optional[int] = None,
        include_dev_menus: bool = False
    ) -> List[dict]:
        """
        Busca menus permitidos para usuário baseado em suas permissões
        e contexto atual (system/company/establishment).
        
        Args:
            user_id: ID do usuário
            context_type: Tipo de contexto (system/company/establishment)
            context_id: ID do contexto específico
            include_dev_menus: Se deve incluir menus de desenvolvimento
            
        Returns:
            Lista de menus em formato flat (será convertida em tree depois)
        """
        
        logger.info("Buscando menus dinâmicos", 
                   user_id=user_id, 
                   context_type=context_type, 
                   context_id=context_id)
        
        # Query complexa usando a view vw_menu_hierarchy
        query = text("""
            WITH user_info AS (
                SELECT 
                    u.id,
                    u.is_system_admin,
                    u.email_address,
                    u.is_active
                FROM master.users u 
                WHERE u.id = :user_id
                AND u.is_active = true
                AND u.deleted_at IS NULL
            ),
            user_permissions AS (
                SELECT DISTINCT p.name as permission_name
                FROM master.users u
                JOIN master.user_roles ur ON u.id = ur.user_id
                JOIN master.role_permissions rp ON ur.role_id = rp.role_id  
                JOIN master.permissions p ON rp.permission_id = p.id
                WHERE u.id = :user_id 
                AND ur.status = 'active'
                AND ur.deleted_at IS NULL
                AND p.is_active = true
                AND (
                    -- Validar contexto da role
                    (ur.context_type = :context_type AND ur.context_id = :context_id)
                    OR 
                    -- ROOT ignora contexto de role
                    EXISTS (SELECT 1 FROM user_info ui WHERE ui.is_system_admin = true)
                )
            ),
            filtered_menus AS (
                SELECT 
                    m.id,
                    m.parent_id,
                    m.name,
                    m.slug,
                    m.url,
                    m.route_name,
                    m.route_params,
                    m.icon,
                    m.level,
                    m.sort_order,
                    m.badge_text,
                    m.badge_color,
                    m.full_path_name,
                    m.id_path,
                    m.type,
                    m.permission_name,
                    m.company_specific,
                    m.establishment_specific,
                    ui.is_system_admin
                FROM master.vw_menu_hierarchy m
                CROSS JOIN user_info ui  -- Garantir info do usuário em cada linha
                WHERE m.is_active = true 
                AND m.is_visible = true
                AND m.visible_in_menu = true
                AND (
                    -- 🔑 ROOT: VÊ TUDO (controlado por include_dev_menus)
                    (
                        ui.is_system_admin = true
                    )
                    OR
                    -- Usuário normal: validação de permissões
                    (
                        ui.is_system_admin = false
                        AND (
                            -- Menu sem permissão específica (público)
                            m.permission_name IS NULL
                            OR 
                            -- Usuário tem a permissão necessária
                            EXISTS (
                                SELECT 1 FROM user_permissions up 
                                WHERE up.permission_name = m.permission_name
                            )
                        )
                    )
                )
                -- Filtros de contexto empresa/estabelecimento
                AND (
                    -- ROOT ignora restrições de contexto
                    ui.is_system_admin = true
                    OR 
                    -- Usuário normal: validar contexto
                    (
                        ui.is_system_admin = false
                        AND (
                            (m.company_specific = false AND m.establishment_specific = false)
                            OR 
                            (m.company_specific = true AND :context_type IN ('company', 'establishment'))
                            OR
                            (m.establishment_specific = true AND :context_type = 'establishment')
                        )
                    )
                )
            )
            SELECT 
                id,
                parent_id,
                name,
                slug,
                url,
                route_name,
                route_params,
                icon,
                level,
                sort_order,
                badge_text,
                badge_color,
                full_path_name,
                id_path,
                type,
                permission_name,
                is_system_admin
            FROM filtered_menus
            ORDER BY level, sort_order, name
        """)
        
        # Determinar se deve mostrar menus de desenvolvimento
        # ROOT em development ou explicitamente solicitado
        if include_dev_menus is None:
            include_dev_menus = (
                context_type == "system" and 
                os.getenv('ENVIRONMENT', 'production') == 'development'
            )
        
        try:
            result = await self.db.execute(query, {
                "user_id": user_id,
                "context_type": context_type,
                "context_id": context_id,
                "include_dev_menus": include_dev_menus
            })
            
            rows = result.fetchall()
            menus = []
            for row in rows:
                # Converter row para dict manualmente
                menu_dict = {
                    'id': row[0],
                    'parent_id': row[1],
                    'name': row[2],
                    'slug': row[3],
                    'url': row[4],
                    'route_name': row[5],
                    'route_params': row[6],
                    'icon': row[7],
                    'level': row[8],
                    'sort_order': row[9],
                    'badge_text': row[10],
                    'badge_color': row[11],
                    'full_path_name': row[12],
                    'id_path': row[13],
                    'type': row[14],
                    'permission_name': row[15],
                    'is_system_admin': row[16]
                }
                menus.append(menu_dict)
            
            # Log resultado
            is_root = menus[0]['is_system_admin'] if menus else False
            logger.info("Menus encontrados", 
                       user_id=user_id, 
                       total_menus=len(menus),
                       is_root=is_root,
                       context_type=context_type)
            
            # Remover campo is_system_admin do resultado (usado apenas para controle)
            for menu in menus:
                menu.pop('is_system_admin', None)
            
            return menus
            
        except Exception as e:
            logger.error("Erro ao buscar menus", 
                        user_id=user_id, 
                        error=str(e))
            raise
    
    async def get_menu_tree(self, flat_menus: List[dict]) -> List[dict]:
        """
        Converte lista plana de menus em árvore hierárquica.
        
        Args:
            flat_menus: Lista plana de menus do banco
            
        Returns:
            Lista hierárquica (árvore) de menus
        """
        
        if not flat_menus:
            return []
        
        # Mapear menus por ID para acesso rápido
        menu_map = {menu['id']: menu for menu in flat_menus}
        
        # Inicializar children para todos os menus
        for menu in menu_map.values():
            menu['children'] = []
        
        # Construir hierarquia
        root_menus = []
        
        for menu in flat_menus:
            if menu['parent_id'] is None:
                # Menu raiz
                root_menus.append(menu)
            elif menu['parent_id'] in menu_map:
                # Adicionar como filho do parent
                parent = menu_map[menu['parent_id']]
                parent['children'].append(menu)
        
        # Ordenar children por sort_order
        def sort_children(menu_list):
            for menu in menu_list:
                if menu['children']:
                    menu['children'].sort(key=lambda x: (x['sort_order'], x['name']))
                    sort_children(menu['children'])  # Recursivo
        
        sort_children(root_menus)
        
        return root_menus
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca informações básicas do usuário para validação.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com informações do usuário ou None se não encontrado
        """
        
        query = text("""
            SELECT 
                u.id,
                u.email_address,
                u.is_system_admin,
                u.is_active,
                p.name,
                p.person_type
            FROM master.users u
            JOIN master.people p ON u.person_id = p.id
            WHERE u.id = :user_id
            AND u.deleted_at IS NULL
        """)
        
        try:
            result = await self.db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            if row:
                return {
                    "id": row[0],
                    "email": row[1], 
                    "is_system_admin": row[2],
                    "is_active": row[3],
                    "name": row[4],
                    "person_type": row[5]
                }
            
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar informações do usuário", 
                        user_id=user_id, 
                        error=str(e))
            return None
    
    async def get_context_info(
        self, 
        context_type: str, 
        context_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Busca informações do contexto atual (sistema/empresa/estabelecimento).
        
        Args:
            context_type: Tipo do contexto
            context_id: ID do contexto
            
        Returns:
            Dict com informações do contexto
        """
        
        if context_type == "system":
            return {
                "type": "system", 
                "id": context_id or 1, 
                "name": "Sistema Global",
                "description": "Administração do sistema"
            }
        
        elif context_type == "company" and context_id:
            query = text("""
                SELECT id, social_name, trade_name, document_number
                FROM master.companies 
                WHERE id = :id AND deleted_at IS NULL
            """)
            
            try:
                result = await self.db.execute(query, {"id": context_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "type": "company",
                        "id": row[0],
                        "name": row[1] or row[2],  # social_name ou trade_name
                        "trade_name": row[2],
                        "document": row[3],
                        "description": f"Empresa {row[1]}"
                    }
            except Exception as e:
                logger.error("Erro ao buscar empresa", 
                           context_id=context_id, 
                           error=str(e))
        
        elif context_type == "establishment" and context_id:
            query = text("""
                SELECT 
                    e.id, 
                    e.trade_name, 
                    e.email,
                    c.social_name as company_name
                FROM master.establishments e
                JOIN master.companies c ON e.company_id = c.id
                WHERE e.id = :id AND e.deleted_at IS NULL
            """)
            
            try:
                result = await self.db.execute(query, {"id": context_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "type": "establishment",
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "company_name": row[3],
                        "description": f"Estabelecimento {row[1]}"
                    }
            except Exception as e:
                logger.error("Erro ao buscar estabelecimento", 
                           context_id=context_id, 
                           error=str(e))
        
        # Fallback para contextos inválidos
        return {
            "type": context_type,
            "id": context_id,
            "name": f"{context_type.title()} {context_id}",
            "description": f"Contexto {context_type}"
        }

    async def log_menu_access(
        self, 
        user_id: int, 
        context_type: str, 
        context_id: Optional[int],
        total_menus: int,
        is_root: bool = False,
        ip_address: Optional[str] = None
    ):
        """
        Log de auditoria para acesso a menus (especialmente importante para ROOT).
        
        Args:
            user_id: ID do usuário
            context_type: Tipo do contexto
            context_id: ID do contexto  
            total_menus: Quantidade de menus retornados
            is_root: Se é usuário ROOT
            ip_address: IP do usuário
        """
        
        # Log especial para ROOT
        if is_root:
            query = text("""
                INSERT INTO master.activity_logs (
                    user_id,
                    action_type,
                    resource_type,
                    resource_id,
                    details,
                    ip_address,
                    created_at
                ) VALUES (
                    :user_id,
                    'MENU_ACCESS',
                    'menu_system',
                    :user_id,
                    :details,
                    :ip_address,
                    now()
                )
            """)
            
            details = {
                "action": "dynamic_menu_load",
                "is_root": True,
                "context_type": context_type,
                "context_id": context_id,
                "total_menus": total_menus,
                "timestamp": "now()"
            }
            
            try:
                await self.db.execute(query, {
                    "user_id": user_id,
                    "details": str(details),  # JSON como string
                    "ip_address": ip_address
                })
                await self.db.commit()
                
                logger.info("ROOT menu access logged", 
                           user_id=user_id, 
                           total_menus=total_menus)
                
            except Exception as e:
                logger.error("Erro ao logar acesso ROOT", 
                           user_id=user_id, 
                           error=str(e))