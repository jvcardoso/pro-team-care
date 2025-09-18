from typing import Dict, List, Optional, Tuple

import structlog
from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.orm.models import Permission, Role, RolePermission
from app.presentation.schemas.role import (
    PermissionCreate,
    PermissionListParams,
    PermissionUpdate,
    RoleCreate,
    RoleListParams,
    RoleUpdate,
)

logger = structlog.get_logger()


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, role_data: RoleCreate) -> Role:
        """Criar novo perfil com permissões"""
        try:
            # Create role
            role_dict = role_data.model_dump(exclude={"permission_ids"})
            role = Role(**role_dict)

            self.db.add(role)
            await self.db.flush()

            # Add permissions if provided
            if role_data.permission_ids:
                await self._add_permissions_to_role(role.id, role_data.permission_ids)

            await self.db.commit()
            await self.db.refresh(role)

            # Load with permissions
            return await self.get_by_id(role.id)

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Error creating role", error=str(e), role_data=role_data.model_dump()
            )
            raise

    async def get_by_id(self, role_id: int) -> Optional[Role]:
        """Buscar perfil por ID com permissões"""
        try:
            stmt = text(
                """
                SELECT r.*,
                       json_agg(
                           json_build_object(
                               'id', p.id,
                               'name', p.name,
                               'display_name', p.display_name,
                               'description', p.description,
                               'module', p.module,
                               'action', p.action,
                               'resource', p.resource,
                               'context_level', p.context_level,
                               'is_active', p.is_active
                           ) ORDER BY p.module, p.action
                       ) FILTER (WHERE p.id IS NOT NULL) as permissions
                FROM master.roles r
                LEFT JOIN master.role_permissions rp ON r.id = rp.role_id
                LEFT JOIN master.permissions p ON rp.permission_id = p.id AND p.is_active = true
                WHERE r.id = :role_id
                GROUP BY r.id
                """
            )

            result = await self.db.execute(stmt, {"role_id": role_id})
            row = result.fetchone()

            if not row:
                return None

            # Convert to Role object
            role_data = dict(row._mapping)
            permissions = role_data.pop("permissions", [])

            role = Role(**role_data)

            # Add permissions as attribute
            if permissions and permissions != [None]:
                role.permissions = [Permission(**perm) for perm in permissions if perm]
            else:
                role.permissions = []

            return role

        except Exception as e:
            logger.error("Error getting role by id", error=str(e), role_id=role_id)
            raise

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Buscar perfil por nome"""
        try:
            stmt = text(
                """
                SELECT * FROM master.roles
                WHERE name = :name
                LIMIT 1
            """
            )

            result = await self.db.execute(stmt, {"name": name})
            row = result.fetchone()

            if row:
                return Role(**dict(row._mapping))
            return None

        except Exception as e:
            logger.error("Error getting role by name", error=str(e), name=name)
            raise

    async def list_roles(self, params: RoleListParams) -> Tuple[List[Role], int]:
        """Listar perfis com filtros e paginação"""
        try:
            # Build WHERE conditions
            conditions = ["1=1"]
            bind_params = {}

            if params.context_type:
                conditions.append("r.context_type = :context_type")
                bind_params["context_type"] = params.context_type

            if params.is_active is not None:
                conditions.append("r.is_active = :is_active")
                bind_params["is_active"] = params.is_active

            if params.is_system_role is not None:
                conditions.append("r.is_system_role = :is_system_role")
                bind_params["is_system_role"] = params.is_system_role

            if params.level_min is not None:
                conditions.append("r.level >= :level_min")
                bind_params["level_min"] = params.level_min

            if params.level_max is not None:
                conditions.append("r.level <= :level_max")
                bind_params["level_max"] = params.level_max

            if params.search:
                conditions.append(
                    """
                    (r.name ILIKE :search
                     OR r.display_name ILIKE :search
                     OR r.description ILIKE :search)
                """
                )
                bind_params["search"] = f"%{params.search}%"

            where_clause = " AND ".join(conditions)

            # Count total
            count_stmt = text(
                f"""
                SELECT COUNT(*)
                FROM master.roles r
                WHERE {where_clause}
            """
            )

            count_result = await self.db.execute(count_stmt, bind_params)
            total = count_result.scalar()

            # Get paginated results
            offset = (params.page - 1) * params.size
            bind_params.update({"limit": params.size, "offset": offset})

            stmt = text(
                f"""
                SELECT r.*,
                       COUNT(rp.permission_id) as permission_count
                FROM master.roles r
                LEFT JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE {where_clause}
                GROUP BY r.id
                ORDER BY r.level DESC, r.display_name
                LIMIT :limit OFFSET :offset
            """
            )

            result = await self.db.execute(stmt, bind_params)
            rows = result.fetchall()

            roles = []
            for row in rows:
                role_data = dict(row._mapping)
                role_data.pop("permission_count", None)  # Remove count field
                roles.append(Role(**role_data))

            return roles, total

        except Exception as e:
            logger.error(
                "Error listing roles", error=str(e), params=params.model_dump()
            )
            raise

    async def update(self, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        """Atualizar perfil"""
        try:
            # Check if role exists and is not system role
            existing_role = await self.get_by_id(role_id)
            if not existing_role:
                return None

            if existing_role.is_system_role:
                raise ValueError("Perfis do sistema não podem ser editados")

            # Update role fields
            update_data = role_data.model_dump(
                exclude_unset=True, exclude={"permission_ids"}
            )

            if update_data:
                set_clauses = []
                bind_params = {"role_id": role_id}

                for field, value in update_data.items():
                    set_clauses.append(f"{field} = :{field}")
                    bind_params[field] = value

                set_clauses.append("updated_at = now()")

                stmt = text(
                    f"""
                    UPDATE master.roles
                    SET {', '.join(set_clauses)}
                    WHERE id = :role_id
                """
                )

                await self.db.execute(stmt, bind_params)

            # Update permissions if provided
            if role_data.permission_ids is not None:
                await self._update_role_permissions(role_id, role_data.permission_ids)

            await self.db.commit()
            return await self.get_by_id(role_id)

        except Exception as e:
            await self.db.rollback()
            logger.error("Error updating role", error=str(e), role_id=role_id)
            raise

    async def delete(self, role_id: int) -> bool:
        """Excluir perfil (soft delete se em uso)"""
        try:
            # Check if role exists and is not system role
            role = await self.get_by_id(role_id)
            if not role:
                return False

            if role.is_system_role:
                raise ValueError("Perfis do sistema não podem ser excluídos")

            # Check if role is in use
            usage_stmt = text(
                """
                SELECT COUNT(*)
                FROM master.user_roles
                WHERE role_id = :role_id AND deleted_at IS NULL
            """
            )

            usage_result = await self.db.execute(usage_stmt, {"role_id": role_id})
            usage_count = usage_result.scalar()

            if usage_count > 0:
                # Soft delete - just deactivate
                stmt = text(
                    """
                    UPDATE master.roles
                    SET is_active = false, updated_at = now()
                    WHERE id = :role_id
                """
                )
                await self.db.execute(stmt, {"role_id": role_id})
                logger.info(
                    "Role deactivated due to usage",
                    role_id=role_id,
                    usage_count=usage_count,
                )
            else:
                # Hard delete - remove role and permissions
                await self._remove_all_permissions_from_role(role_id)

                stmt = text("DELETE FROM master.roles WHERE id = :role_id")
                await self.db.execute(stmt, {"role_id": role_id})
                logger.info("Role deleted permanently", role_id=role_id)

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting role", error=str(e), role_id=role_id)
            raise

    async def _add_permissions_to_role(
        self, role_id: int, permission_ids: List[int]
    ) -> None:
        """Adicionar permissões ao perfil"""
        if not permission_ids:
            return

        # Remove duplicates and ensure permissions exist
        unique_permission_ids = list(set(permission_ids))

        valid_permissions_stmt = text(
            """
            SELECT id FROM master.permissions
            WHERE id = ANY(:permission_ids) AND is_active = true
        """
        )

        result = await self.db.execute(
            valid_permissions_stmt, {"permission_ids": unique_permission_ids}
        )
        valid_ids = [row[0] for row in result.fetchall()]

        if not valid_ids:
            return

        # Insert role permissions
        values = []
        for perm_id in valid_ids:
            values.append(f"({role_id}, {perm_id}, now())")

        if values:
            stmt = text(
                f"""
                INSERT INTO master.role_permissions (role_id, permission_id, granted_at)
                VALUES {', '.join(values)}
                ON CONFLICT (role_id, permission_id) DO NOTHING
            """
            )

            await self.db.execute(stmt)

    async def _update_role_permissions(
        self, role_id: int, permission_ids: List[int]
    ) -> None:
        """Atualizar permissões do perfil (substitui todas)"""
        # Remove all existing permissions
        await self._remove_all_permissions_from_role(role_id)

        # Add new permissions
        if permission_ids:
            await self._add_permissions_to_role(role_id, permission_ids)

    async def _remove_all_permissions_from_role(self, role_id: int) -> None:
        """Remover todas as permissões do perfil"""
        stmt = text("DELETE FROM master.role_permissions WHERE role_id = :role_id")
        await self.db.execute(stmt, {"role_id": role_id})

    async def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Buscar permissões de um perfil"""
        try:
            stmt = text(
                """
                SELECT p.*
                FROM master.permissions p
                JOIN master.role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = :role_id AND p.is_active = true
                ORDER BY p.module, p.action
            """
            )

            result = await self.db.execute(stmt, {"role_id": role_id})
            return [Permission(**dict(row._mapping)) for row in result.fetchall()]

        except Exception as e:
            logger.error(
                "Error getting role permissions", error=str(e), role_id=role_id
            )
            raise


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_permissions(
        self, params: PermissionListParams
    ) -> Tuple[List[Permission], int]:
        """Listar permissões com filtros"""
        try:
            conditions = ["1=1"]
            bind_params = {}

            if params.module:
                conditions.append("module = :module")
                bind_params["module"] = params.module

            if params.action:
                conditions.append("action = :action")
                bind_params["action"] = params.action

            if params.resource:
                conditions.append("resource = :resource")
                bind_params["resource"] = params.resource

            if params.context_level:
                conditions.append("context_level = :context_level")
                bind_params["context_level"] = params.context_level

            if params.is_active is not None:
                conditions.append("is_active = :is_active")
                bind_params["is_active"] = params.is_active

            if params.search:
                conditions.append(
                    """
                    (name ILIKE :search
                     OR display_name ILIKE :search
                     OR description ILIKE :search)
                """
                )
                bind_params["search"] = f"%{params.search}%"

            where_clause = " AND ".join(conditions)

            # Count total
            count_stmt = text(
                f"""
                SELECT COUNT(*) FROM master.permissions WHERE {where_clause}
            """
            )
            count_result = await self.db.execute(count_stmt, bind_params)
            total = count_result.scalar()

            # Get paginated results
            offset = (params.page - 1) * params.size
            bind_params.update({"limit": params.size, "offset": offset})

            stmt = text(
                f"""
                SELECT * FROM master.permissions
                WHERE {where_clause}
                ORDER BY module, action, resource
                LIMIT :limit OFFSET :offset
            """
            )

            result = await self.db.execute(stmt, bind_params)
            permissions = [
                Permission(**dict(row._mapping)) for row in result.fetchall()
            ]

            return permissions, total

        except Exception as e:
            logger.error("Error listing permissions", error=str(e))
            raise

    async def get_permissions_grouped_by_module(self) -> Dict[str, List[Permission]]:
        """Buscar permissões agrupadas por módulo"""
        try:
            stmt = text(
                """
                SELECT * FROM master.permissions
                WHERE is_active = true
                ORDER BY module, action, resource
            """
            )

            result = await self.db.execute(stmt)
            permissions = [
                Permission(**dict(row._mapping)) for row in result.fetchall()
            ]

            # Group by module
            grouped = {}
            for perm in permissions:
                if perm.module not in grouped:
                    grouped[perm.module] = []
                grouped[perm.module].append(perm)

            return grouped

        except Exception as e:
            logger.error("Error getting permissions grouped by module", error=str(e))
            raise
