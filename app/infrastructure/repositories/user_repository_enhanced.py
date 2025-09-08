"""
Enhanced User Repository com melhorias de segurança baseadas na view users_complete
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from structlog import get_logger

from app.infrastructure.entities.user import UserEntity
from app.domain.entities.user import User
from app.infrastructure.repositories.user_repository import UserRepository


class EnhancedUserRepository(UserRepository):
    """
    Repository aprimorado com recursos de segurança baseados na view users_complete
    """
    
    async def get_user_complete_secure(self, user_id: int, requesting_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca dados completos do usuário com controle de segurança
        - Usuário comum: só seus próprios dados (sem campos sensíveis)
        - Admin: dados completos (com campos sensíveis mascarados)
        """
        try:
            # Verificar se o usuário solicitante é admin
            requesting_user = await self.db.get(UserEntity, requesting_user_id)
            is_admin = requesting_user and requesting_user.is_system_admin
            is_self = (user_id == requesting_user_id)
            
            if not is_admin and not is_self:
                # Usuário não pode ver dados de outros
                return None
            
            # Query base usando a view
            if is_admin:
                # Admin vê dados completos (mascarados)
                query = text("""
                    SELECT 
                        user_id, user_email, user_is_active, user_is_system_admin,
                        user_last_login_at, user_password_changed_at,
                        person_name, person_tax_id, person_birth_date, person_status,
                        company_id, establishment_code, establishment_type,
                        role_name, role_display_name, role_level,
                        -- Campos mascarados de segurança
                        CASE WHEN user_two_factor_secret IS NOT NULL 
                             THEN 'CONFIGURED' ELSE 'NOT_CONFIGURED' END as two_factor_status,
                        CASE WHEN user_two_factor_recovery_codes IS NOT NULL 
                             THEN 'AVAILABLE' ELSE 'NOT_AVAILABLE' END as recovery_codes_status,
                        -- LGPD info (apenas para admins)
                        person_lgpd_consent_version,
                        person_lgpd_consent_given_at,
                        person_lgpd_data_retention_expires_at
                    FROM master.vw_users_complete 
                    WHERE user_id = :user_id
                    ORDER BY user_establishment_is_primary DESC NULLS LAST
                """)
            else:
                # Usuário comum vê apenas dados básicos próprios
                query = text("""
                    SELECT 
                        user_id, user_email, user_is_active,
                        user_last_login_at,
                        person_name, person_birth_date,
                        company_id, establishment_code,
                        role_name, role_display_name,
                        -- Status 2FA sem detalhes
                        CASE WHEN user_two_factor_secret IS NOT NULL 
                             THEN true ELSE false END as has_two_factor
                    FROM master.vw_users_complete 
                    WHERE user_id = :user_id
                    ORDER BY user_establishment_is_primary DESC NULLS LAST
                """)
            
            result = await self.db.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            
            if not rows:
                return None
            
            # Converter para dicionário
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            self.logger.error("Error fetching secure user data", user_id=user_id, error=str(e))
            raise

    async def list_users_with_context(
        self, 
        requesting_user_id: int,
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        establishment_filter: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lista usuários com contexto completo baseado na view users_complete
        Aplica filtros de segurança baseados no usuário solicitante
        """
        try:
            # Verificar permissões do usuário solicitante
            requesting_user = await self.db.get(UserEntity, requesting_user_id)
            if not requesting_user:
                return [], 0
                
            is_admin = requesting_user.is_system_admin
            
            # Query base diferente para admin vs usuário comum
            if is_admin:
                # Admin vê todos os usuários com dados completos
                base_query = text("""
                    SELECT DISTINCT
                        user_id, user_email, user_is_active, user_is_system_admin,
                        user_last_login_at, user_created_at,
                        person_name, person_status, person_tax_id,
                        establishment_code, establishment_type,
                        role_name, role_display_name, role_level,
                        COUNT(*) OVER() as total_count
                    FROM master.vw_users_complete 
                    WHERE user_is_active = true
                """)
            else:
                # Usuário comum vê apenas colegas do mesmo estabelecimento
                base_query = text("""
                    SELECT DISTINCT
                        vc.user_id, vc.user_email, vc.person_name,
                        vc.establishment_code, vc.role_display_name,
                        COUNT(*) OVER() as total_count
                    FROM master.vw_users_complete vc
                    WHERE vc.user_is_active = true
                    AND vc.establishment_id IN (
                        SELECT establishment_id 
                        FROM master.vw_users_complete 
                        WHERE user_id = :requesting_user_id
                    )
                """)
            
            # Aplicar filtros adicionais
            conditions = []
            params = {"requesting_user_id": requesting_user_id}
            
            if search:
                conditions.append("(person_name ILIKE :search OR user_email ILIKE :search)")
                params["search"] = f"%{search}%"
            
            if role_filter:
                conditions.append("role_name = :role_filter")
                params["role_filter"] = role_filter
                
            if establishment_filter:
                conditions.append("establishment_id = :establishment_filter")
                params["establishment_filter"] = establishment_filter
            
            # Construir query final
            if conditions:
                query = base_query + " AND " + " AND ".join(conditions)
            else:
                query = base_query
                
            query += " ORDER BY person_name LIMIT :limit OFFSET :skip"
            params.update({"limit": limit, "skip": skip})
            
            # Executar query
            result = await self.db.execute(query, params)
            rows = result.fetchall()
            
            total = rows[0].total_count if rows else 0
            
            # Converter para lista de dicionários
            columns = [col for col in result.keys() if col != 'total_count']
            users = [dict(zip(columns, [getattr(row, col) for col in columns])) for row in rows]
            
            return users, total
            
        except Exception as e:
            self.logger.error("Error listing users with context", error=str(e))
            raise

    async def get_user_roles_and_permissions(self, user_id: int) -> Dict[str, Any]:
        """
        Obtém roles e permissões do usuário de forma segura
        """
        try:
            query = text("""
                SELECT 
                    user_id,
                    role_name,
                    role_display_name,
                    role_level,
                    role_context_type,
                    user_role_context_id,
                    user_role_status,
                    user_role_expires_at,
                    user_establishment_permissions,
                    establishment_code,
                    establishment_type,
                    company_id
                FROM master.vw_users_complete 
                WHERE user_id = :user_id 
                AND role_name IS NOT NULL
                AND user_role_status = 'active'
                ORDER BY role_level ASC
            """)
            
            result = await self.db.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            
            if not rows:
                return {
                    "user_id": user_id,
                    "roles": [],
                    "permissions": {},
                    "establishments": []
                }
            
            # Agrupar dados
            roles = []
            permissions = {}
            establishments = set()
            
            for row in rows:
                # Role info
                role_info = {
                    "name": row.role_name,
                    "display_name": row.role_display_name,
                    "level": row.role_level,
                    "context_type": row.role_context_type,
                    "context_id": row.user_role_context_id,
                    "expires_at": row.user_role_expires_at
                }
                
                if role_info not in roles:
                    roles.append(role_info)
                
                # Permissions
                if row.user_establishment_permissions:
                    perms = row.user_establishment_permissions
                    if isinstance(perms, dict):
                        permissions.update(perms)
                
                # Establishments
                if row.establishment_code:
                    establishments.add(row.establishment_code)
            
            return {
                "user_id": user_id,
                "roles": roles,
                "permissions": permissions,
                "establishments": list(establishments)
            }
            
        except Exception as e:
            self.logger.error("Error fetching user roles and permissions", user_id=user_id, error=str(e))
            raise

    async def audit_user_access(self, user_id: int, action: str, context: str) -> None:
        """
        Registra auditoria de acesso a dados sensíveis
        """
        try:
            audit_query = text("""
                INSERT INTO master.audit_logs 
                (user_id, action, context, timestamp, metadata)
                VALUES (:user_id, :action, :context, NOW(), :metadata)
            """)
            
            metadata = {
                "source": "enhanced_user_repository",
                "sensitive_data_access": True
            }
            
            await self.db.execute(audit_query, {
                "user_id": user_id,
                "action": action,
                "context": context,
                "metadata": metadata
            })
            
            await self.db.commit()
            
        except Exception as e:
            self.logger.warning("Failed to log audit", user_id=user_id, action=action, error=str(e))
            # Não falhar a operação principal por causa de auditoria