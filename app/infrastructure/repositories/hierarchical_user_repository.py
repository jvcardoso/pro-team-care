"""
HIERARCHICAL USER REPOSITORY - IMPLEMENTAÇÃO UNIFICADA
Combina vw_users_complete + sistema hierárquico de permissões
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.infrastructure.repositories.user_repository import UserRepository


class AccessLevel(Enum):
    """Níveis de acesso hierárquico"""

    FULL = "full"  # ROOT - Acesso total
    COMPANY = "company"  # Admin Empresa - Dados da empresa
    ESTABLISHMENT = "establishment"  # Admin Estabelecimento - Dados do estabelecimento
    SELF = "self"  # Próprios dados
    COLLEAGUE = "colleague"  # Colega de trabalho
    NONE = "none"  # Sem acesso


class HierarchicalUserRepository(UserRepository):
    """
    Repository unificado com controle hierárquico completo
    Integra vw_users_complete + sistema de permissões hierárquicas
    """

    async def get_user_with_hierarchical_control(
        self, requesting_user_id: int, target_user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Busca usuário com controle hierárquico completo
        Retorna dados baseado no nível de acesso do solicitante
        """
        try:
            # 1. Verificar acesso hierárquico
            access_level = await self._get_access_level(
                requesting_user_id, target_user_id
            )

            if access_level == AccessLevel.NONE:
                self.logger.warning(
                    "Access denied",
                    requesting_user_id=requesting_user_id,
                    target_user_id=target_user_id,
                )
                return None

            # 2. Buscar dados baseado no nível de acesso
            if access_level == AccessLevel.FULL:
                return await self._get_full_user_data(target_user_id)
            elif access_level == AccessLevel.COMPANY:
                return await self._get_company_user_data(target_user_id)
            elif access_level == AccessLevel.ESTABLISHMENT:
                return await self._get_establishment_user_data(target_user_id)
            elif access_level == AccessLevel.SELF:
                return await self._get_personal_user_data(target_user_id)
            else:  # COLLEAGUE
                return await self._get_colleague_user_data(target_user_id)

        except Exception as e:
            self.logger.error(
                "Error in hierarchical user access",
                requesting_user_id=requesting_user_id,
                target_user_id=target_user_id,
                error=str(e),
            )
            raise

    async def list_accessible_users(
        self,
        requesting_user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        company_filter: Optional[int] = None,
        establishment_filter: Optional[int] = None,
        hierarchy_filter: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lista usuários acessíveis com controle hierárquico
        """
        try:
            # 1. Obter lista de usuários acessíveis
            accessible_users = await self._get_accessible_user_ids(requesting_user_id)

            if not accessible_users:
                return [], 0

            # 2. Construir query com filtros
            query_conditions = [
                "vc.user_id = ANY(:accessible_users)",
                "vc.user_is_active = true",
            ]
            query_params = {"accessible_users": list(accessible_users.keys())}

            # Aplicar filtros
            if search:
                query_conditions.append(
                    "(vc.person_name ILIKE :search OR vc.user_email ILIKE :search)"
                )
                query_params["search"] = f"%{search}%"

            if role_filter:
                query_conditions.append("vc.role_name = :role_filter")
                query_params["role_filter"] = role_filter

            if company_filter:
                query_conditions.append("vc.company_id = :company_filter")
                query_params["company_filter"] = company_filter

            if establishment_filter:
                query_conditions.append("vc.establishment_id = :establishment_filter")
                query_params["establishment_filter"] = establishment_filter

            if hierarchy_filter:
                hierarchy_users = [
                    uid
                    for uid, access in accessible_users.items()
                    if access.access_level == hierarchy_filter
                ]
                if hierarchy_users:
                    query_conditions.append("vc.user_id = ANY(:hierarchy_users)")
                    query_params["hierarchy_users"] = hierarchy_users
                else:
                    return [], 0

            # 3. Query principal
            main_query = f"""
            SELECT DISTINCT
                vc.user_id,
                vc.user_email,
                vc.user_is_active,
                vc.user_is_system_admin,
                vc.user_last_login_at,
                vc.user_created_at,
                vc.person_name,
                vc.person_status,
                vc.company_id,
                vc.establishment_code,
                vc.establishment_type,
                vc.role_name,
                vc.role_display_name,
                vc.role_level,
                -- Classificação hierárquica
                CASE
                    WHEN vc.user_is_system_admin THEN 'ROOT'
                    WHEN EXISTS(
                        SELECT 1 FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = vc.user_id
                        AND r.context_type = 'company'
                        AND r.level >= 80
                    ) THEN 'ADMIN_EMPRESA'
                    WHEN EXISTS(
                        SELECT 1 FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = vc.user_id
                        AND r.context_type = 'establishment'
                        AND r.level >= 60
                    ) THEN 'ADMIN_ESTABELECIMENTO'
                    ELSE 'USUARIO_COMUM'
                END as hierarchy_level,
                COUNT(*) OVER() as total_count
            FROM master.vw_users_complete vc
            WHERE {' AND '.join(query_conditions)}
            ORDER BY
                CASE
                    WHEN vc.user_is_system_admin THEN 1
                    WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = vc.user_id AND r.level >= 80) THEN 2
                    WHEN EXISTS(SELECT 1 FROM master.user_roles ur JOIN master.roles r ON ur.role_id = r.id WHERE ur.user_id = vc.user_id AND r.level >= 60) THEN 3
                    ELSE 4
                END,
                vc.person_name
            LIMIT :limit OFFSET :skip
            """

            query_params.update({"limit": limit, "skip": skip})

            # 4. Executar query
            result = await self.db.execute(text(main_query), query_params)
            rows = result.fetchall()

            total = rows[0].total_count if rows else 0

            # 5. Processar dados baseado no nível de acesso
            users = []
            for row in rows:
                user_data = dict(row._mapping)
                access_info = accessible_users.get(user_data["user_id"])

                # Aplicar mascaramento baseado no acesso
                if access_info:
                    user_data = await self._apply_data_masking(
                        user_data, access_info.access_level
                    )
                    user_data["access_reason"] = access_info.reason

                users.append(user_data)

            # 6. Log da operação para auditoria
            await self._log_user_list_access(
                requesting_user_id, len(users), search, role_filter
            )

            return users, total

        except Exception as e:
            self.logger.error(
                "Error listing accessible users",
                requesting_user_id=requesting_user_id,
                error=str(e),
            )
            raise

    async def _get_access_level(
        self, requesting_user_id: int, target_user_id: int
    ) -> AccessLevel:
        """Determina o nível de acesso hierárquico"""
        try:
            # Usar função SQL para verificar acesso hierárquico
            result = await self.db.execute(
                text(
                    "SELECT access_level, reason FROM master.get_accessible_users_hierarchical(:user_id) WHERE accessible_user_id = :target_id"
                ),
                {"user_id": requesting_user_id, "target_id": target_user_id},
            )

            row = result.fetchone()

            if not row:
                return AccessLevel.NONE

            # Mapear resultado SQL para enum
            access_map = {
                "full": AccessLevel.FULL,
                "company": AccessLevel.COMPANY,
                "establishment": AccessLevel.ESTABLISHMENT,
                "self": AccessLevel.SELF,
            }

            return access_map.get(row.access_level, AccessLevel.COLLEAGUE)

        except Exception as e:
            self.logger.error("Error determining access level", error=str(e))
            return AccessLevel.NONE

    async def _get_accessible_user_ids(self, requesting_user_id: int) -> Dict[int, Any]:
        """Obtém todos os IDs de usuários acessíveis"""
        try:
            result = await self.db.execute(
                text(
                    "SELECT accessible_user_id, access_level, reason FROM master.get_accessible_users_hierarchical(:user_id)"
                ),
                {"user_id": requesting_user_id},
            )

            accessible_users = {}
            for row in result.fetchall():
                accessible_users[row.accessible_user_id] = type(
                    "AccessInfo",
                    (),
                    {"access_level": row.access_level, "reason": row.reason},
                )()

            return accessible_users

        except Exception as e:
            self.logger.error("Error getting accessible user IDs", error=str(e))
            return {}

    async def _get_full_user_data(self, user_id: int) -> Dict[str, Any]:
        """Dados completos para ROOT (com mascaramento de segurança)"""
        query = text(
            """
        SELECT
            user_id, user_email, user_is_active, user_is_system_admin,
            user_last_login_at, user_password_changed_at, user_created_at,
            person_name, person_tax_id, person_birth_date, person_status,
            company_id, establishment_code, establishment_type,
            role_name, role_display_name, role_level,
            -- Campos mascarados de segurança
            CASE WHEN user_two_factor_secret IS NOT NULL
                 THEN 'CONFIGURED' ELSE 'NOT_CONFIGURED' END as two_factor_status,
            CASE WHEN user_two_factor_recovery_codes IS NOT NULL
                 THEN 'AVAILABLE' ELSE 'NOT_AVAILABLE' END as recovery_codes_status,
            -- LGPD info (apenas para ROOT)
            person_lgpd_consent_version,
            person_lgpd_consent_given_at,
            person_lgpd_data_retention_expires_at
        FROM master.vw_users_complete
        WHERE user_id = :user_id
        """
        )

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        return dict(row._mapping) if row else None

    async def _get_company_user_data(self, user_id: int) -> Dict[str, Any]:
        """Dados empresariais para Admin Empresa"""
        query = text(
            """
        SELECT
            user_id, user_email, user_is_active, user_is_system_admin,
            user_last_login_at, user_created_at,
            person_name, person_tax_id, person_status,
            company_id, establishment_code, establishment_type,
            role_name, role_display_name, role_level,
            -- Status 2FA sem detalhes
            CASE WHEN user_two_factor_secret IS NOT NULL
                 THEN true ELSE false END as has_two_factor
        FROM master.vw_users_complete
        WHERE user_id = :user_id
        """
        )

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        return dict(row._mapping) if row else None

    async def _get_establishment_user_data(self, user_id: int) -> Dict[str, Any]:
        """Dados básicos para Admin Estabelecimento"""
        query = text(
            """
        SELECT
            user_id, user_email, user_is_active,
            person_name, person_status,
            establishment_code, role_display_name
        FROM master.vw_users_complete
        WHERE user_id = :user_id
        """
        )

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        return dict(row._mapping) if row else None

    async def _get_personal_user_data(self, user_id: int) -> Dict[str, Any]:
        """Dados pessoais completos (próprios dados)"""
        query = text(
            """
        SELECT
            user_id, user_email, user_is_active, user_last_login_at,
            user_preferences, user_notification_settings,
            person_name, person_birth_date, person_tax_id,
            company_id, establishment_code, role_name,
            -- 2FA completo para próprios dados
            CASE WHEN user_two_factor_secret IS NOT NULL
                 THEN true ELSE false END as has_two_factor,
            user_two_factor_recovery_codes IS NOT NULL as has_recovery_codes
        FROM master.vw_users_complete
        WHERE user_id = :user_id
        """
        )

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        return dict(row._mapping) if row else None

    async def _get_colleague_user_data(self, user_id: int) -> Dict[str, Any]:
        """Dados mínimos para colegas"""
        query = text(
            """
        SELECT
            user_id, user_email, person_name,
            establishment_code, role_display_name
        FROM master.vw_users_complete
        WHERE user_id = :user_id
        """
        )

        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        return dict(row._mapping) if row else None

    async def _apply_data_masking(
        self, user_data: Dict[str, Any], access_level: str
    ) -> Dict[str, Any]:
        """Aplica mascaramento baseado no nível de acesso"""
        if access_level == "full":
            # ROOT: dados já vem mascarados da query
            return user_data
        elif access_level in ["company", "establishment"]:
            # Remover dados sensíveis se existirem
            sensitive_fields = [
                "person_tax_id",
                "person_birth_date",
                "user_preferences",
            ]
            for field in sensitive_fields:
                if field in user_data and access_level == "establishment":
                    user_data[field] = "***MASKED***"
        elif access_level == "colleague":
            # Manter apenas dados básicos
            basic_fields = [
                "user_id",
                "user_email",
                "person_name",
                "establishment_code",
                "role_display_name",
            ]
            user_data = {k: v for k, v in user_data.items() if k in basic_fields}

        return user_data

    async def _log_user_list_access(
        self, user_id: int, count: int, search: str, role_filter: str
    ):
        """Log de auditoria para listagem de usuários"""
        try:
            log_data = {
                "action": "list_users",
                "user_count": count,
                "search_term": search,
                "role_filter": role_filter,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.logger.info("User list accessed", user_id=user_id, **log_data)

        except Exception as e:
            self.logger.warning("Failed to log user list access", error=str(e))

    async def get_user_hierarchy_info(self, user_id: int) -> Dict[str, Any]:
        """Obtém informações de hierarquia do usuário"""
        try:
            query = text(
                """
            SELECT
                user_id,
                user_email,
                person_name,
                CASE
                    WHEN user_is_system_admin THEN 'ROOT'
                    WHEN EXISTS(
                        SELECT 1 FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = vc.user_id
                        AND r.context_type = 'company'
                        AND r.level >= 80
                    ) THEN 'ADMIN_EMPRESA'
                    WHEN EXISTS(
                        SELECT 1 FROM master.user_roles ur
                        JOIN master.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = vc.user_id
                        AND r.context_type = 'establishment'
                        AND r.level >= 60
                    ) THEN 'ADMIN_ESTABELECIMENTO'
                    ELSE 'USUARIO_COMUM'
                END as hierarchy_level,
                (SELECT ARRAY_AGG(DISTINCT ur2.context_id::text)
                 FROM master.user_roles ur2
                 JOIN master.roles r2 ON ur2.role_id = r2.id
                 WHERE ur2.user_id = vc.user_id
                   AND r2.context_type = 'company'
                   AND ur2.deleted_at IS NULL
                ) as accessible_companies,
                (SELECT ARRAY_AGG(DISTINCT ur3.context_id::text)
                 FROM master.user_roles ur3
                 JOIN master.roles r3 ON ur3.role_id = r3.id
                 WHERE ur3.user_id = vc.user_id
                   AND r3.context_type = 'establishment'
                   AND ur3.deleted_at IS NULL
                ) as accessible_establishments
            FROM master.vw_users_complete vc
            WHERE user_id = :user_id
            LIMIT 1
            """
            )

            result = await self.db.execute(query, {"user_id": user_id})
            row = result.fetchone()

            return dict(row._mapping) if row else None

        except Exception as e:
            self.logger.error(
                "Error getting user hierarchy info", user_id=user_id, error=str(e)
            )
            raise
