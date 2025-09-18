"""
Gerenciador de Sessões Seguras com Troca de Perfil
Integra com as tabelas user_sessions e context_switches
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from structlog import get_logger


class SecureSessionManager:
    """
    Gerenciador de sessões seguras com capacidade de troca de perfil
    """

    def __init__(self, db):
        self.db = db
        self.logger = get_logger()

    async def create_secure_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None,
        initial_role_id: Optional[int] = None,
        initial_context_type: Optional[str] = None,
        initial_context_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Criar sessão segura inicial
        """
        try:
            # Gerar tokens seguros
            session_token = str(uuid.uuid4())
            refresh_token = secrets.token_urlsafe(64)

            # Definir expiração (2 horas para sessão, 7 dias para refresh)
            expires_at = datetime.utcnow() + timedelta(hours=2)
            refresh_expires_at = datetime.utcnow() + timedelta(days=7)

            # Inserir sessão no banco
            insert_query = text(
                """
                INSERT INTO master.user_sessions (
                    user_id, session_token, refresh_token,
                    active_role_id, active_context_type, active_context_id,
                    ip_address, user_agent, device_fingerprint,
                    expires_at, refresh_expires_at
                ) VALUES (
                    :user_id, :session_token, :refresh_token,
                    :active_role_id, :active_context_type, :active_context_id,
                    :ip_address, :user_agent, :device_fingerprint,
                    :expires_at, :refresh_expires_at
                ) RETURNING id
            """
            )

            result = await self.db.execute(
                insert_query,
                {
                    "user_id": user_id,
                    "session_token": session_token,
                    "refresh_token": refresh_token,
                    "active_role_id": initial_role_id,
                    "active_context_type": initial_context_type,
                    "active_context_id": initial_context_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "device_fingerprint": device_fingerprint,
                    "expires_at": expires_at,
                    "refresh_expires_at": refresh_expires_at,
                },
            )

            session_id = result.scalar()
            await self.db.commit()

            self.logger.info(
                "Secure session created", user_id=user_id, session_id=str(session_id)
            )

            return {
                "session_id": str(session_id),
                "session_token": session_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
                "refresh_expires_at": refresh_expires_at,
                "active_context": {
                    "role_id": initial_role_id,
                    "context_type": initial_context_type,
                    "context_id": initial_context_id,
                },
            }

        except Exception as e:
            await self.db.rollback()
            self.logger.error(
                "Error creating secure session", user_id=user_id, error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar sessão segura",
            )

    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validar sessão e retornar contexto atual
        """
        try:
            query = text(
                """
                SELECT
                    us.id as session_id,
                    us.user_id,
                    us.active_role_id,
                    us.active_context_type,
                    us.active_context_id,
                    us.impersonated_user_id,
                    us.expires_at,
                    u.email_address as user_email,
                    u.is_system_admin,
                    impersonated_u.email_address as impersonated_email,
                    r.name as role_name,
                    r.display_name as role_display_name
                FROM master.user_sessions us
                JOIN master.users u ON us.user_id = u.id
                LEFT JOIN master.users impersonated_u ON us.impersonated_user_id = impersonated_u.id
                LEFT JOIN master.roles r ON us.active_role_id = r.id
                WHERE us.session_token = :session_token
                  AND us.is_active = true
                  AND us.expires_at > CURRENT_TIMESTAMP
            """
            )

            result = await self.db.execute(query, {"session_token": session_token})
            session_data = result.fetchone()

            if not session_data:
                return None

            # Atualizar última atividade
            await self.db.execute(
                text(
                    "UPDATE master.user_sessions SET last_activity_at = CURRENT_TIMESTAMP WHERE session_token = :token"
                ),
                {"token": session_token},
            )
            await self.db.commit()

            return dict(session_data._mapping)

        except Exception as e:
            self.logger.error(
                "Error validating session",
                session_token=session_token[:20],
                error=str(e),
            )
            return None

    async def get_available_profiles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obter perfis disponíveis para o usuário (incluindo personificação para ROOT)
        """
        try:
            # Verificar se é ROOT
            user_query = text(
                "SELECT is_system_admin FROM master.users WHERE id = :user_id"
            )
            user_result = await self.db.execute(user_query, {"user_id": user_id})
            user_data = user_result.fetchone()

            if not user_data:
                return []

            is_root = user_data.is_system_admin

            if is_root:
                # ROOT pode assumir qualquer perfil
                query = text(
                    """
                    SELECT DISTINCT
                        ur.role_id,
                        r.name as role_name,
                        r.display_name as role_display_name,
                        r.level,
                        ur.context_type,
                        ur.context_id,
                        ur.user_id,
                        CASE
                            WHEN ur.context_type = 'system' THEN 'Sistema Global'
                            WHEN ur.context_type = 'company' THEN
                                COALESCE((SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = ur.context_id), 'Empresa Desconhecida')
                            WHEN ur.context_type = 'establishment' THEN
                                COALESCE((SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = ur.context_id), 'Estabelecimento Desconhecido')
                            ELSE 'Contexto Desconhecido'
                        END as context_name,
                        CASE WHEN ur.user_id != :user_id THEN true ELSE false END as is_impersonation,
                        ur.user_id as target_user_id,
                        u.email_address as target_user_email
                    FROM master.user_roles ur
                    JOIN master.roles r ON ur.role_id = r.id
                    JOIN master.users u ON ur.user_id = u.id
                    WHERE ur.deleted_at IS NULL
                      AND u.is_active = true
                    ORDER BY ur.user_id = :user_id DESC, r.level DESC
                    LIMIT 20
                """
                )
            else:
                # Usuários comuns veem apenas seus próprios perfis
                query = text(
                    """
                    SELECT
                        ur.role_id,
                        r.name as role_name,
                        r.display_name as role_display_name,
                        ur.context_type,
                        ur.context_id,
                        CASE
                            WHEN ur.context_type = 'system' THEN 'Sistema Global'
                            WHEN ur.context_type = 'company' THEN
                                COALESCE((SELECT p.name FROM master.companies c JOIN master.people p ON c.person_id = p.id WHERE c.id = ur.context_id), 'Empresa Desconhecida')
                            WHEN ur.context_type = 'establishment' THEN
                                COALESCE((SELECT p.name FROM master.establishments e JOIN master.people p ON e.person_id = p.id WHERE e.id = ur.context_id), 'Estabelecimento Desconhecido')
                            ELSE 'Contexto Desconhecido'
                        END as context_name,
                        false as is_impersonation,
                        :user_id as target_user_id,
                        '' as target_user_email
                    FROM master.user_roles ur
                    JOIN master.roles r ON ur.role_id = r.id
                    WHERE ur.user_id = :user_id
                      AND ur.deleted_at IS NULL
                    ORDER BY r.level DESC
                """
                )

            result = await self.db.execute(query, {"user_id": user_id})
            profiles = []

            for row in result.fetchall():
                profiles.append(dict(row._mapping))

            return profiles

        except Exception as e:
            self.logger.error(
                "Error getting available profiles", user_id=user_id, error=str(e)
            )
            return []

    async def switch_context(
        self,
        session_token: str,
        new_role_id: Optional[int] = None,
        new_context_type: Optional[str] = None,
        new_context_id: Optional[int] = None,
        impersonated_user_id: Optional[int] = None,
        switch_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Trocar contexto/perfil da sessão
        """
        try:
            # Buscar sessão atual
            current_session = await self.validate_session(session_token)
            if not current_session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Sessão inválida ou expirada",
                )

            # Verificar se pode fazer a troca (ROOT pode tudo, outros apenas seus perfis)
            if not current_session["is_system_admin"] and impersonated_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Apenas administradores podem personificar usuários",
                )

            # Registrar mudança de contexto
            context_switch_query = text(
                """
                INSERT INTO master.context_switches (
                    session_id, user_id,
                    previous_role_id, previous_context_type, previous_context_id, previous_impersonated_user_id,
                    new_role_id, new_context_type, new_context_id, new_impersonated_user_id,
                    switch_reason, ip_address, user_agent
                ) VALUES (
                    :session_id, :user_id,
                    :prev_role_id, :prev_context_type, :prev_context_id, :prev_impersonated_user_id,
                    :new_role_id, :new_context_type, :new_context_id, :new_impersonated_user_id,
                    :switch_reason, :ip_address, :user_agent
                )
            """
            )

            await self.db.execute(
                context_switch_query,
                {
                    "session_id": current_session["session_id"],
                    "user_id": current_session["user_id"],
                    "prev_role_id": current_session["active_role_id"],
                    "prev_context_type": current_session["active_context_type"],
                    "prev_context_id": current_session["active_context_id"],
                    "prev_impersonated_user_id": current_session[
                        "impersonated_user_id"
                    ],
                    "new_role_id": new_role_id,
                    "new_context_type": new_context_type,
                    "new_context_id": new_context_id,
                    "new_impersonated_user_id": impersonated_user_id,
                    "switch_reason": switch_reason,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                },
            )

            # Atualizar sessão
            update_session_query = text(
                """
                UPDATE master.user_sessions
                SET
                    active_role_id = COALESCE(:new_role_id, active_role_id),
                    active_context_type = COALESCE(:new_context_type, active_context_type),
                    active_context_id = COALESCE(:new_context_id, active_context_id),
                    impersonated_user_id = COALESCE(:impersonated_user_id, impersonated_user_id),
                    last_activity_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_token = :session_token
            """
            )

            await self.db.execute(
                update_session_query,
                {
                    "new_role_id": new_role_id,
                    "new_context_type": new_context_type,
                    "new_context_id": new_context_id,
                    "impersonated_user_id": impersonated_user_id,
                    "session_token": session_token,
                },
            )

            await self.db.commit()

            # Retornar nova sessão
            updated_session = await self.validate_session(session_token)

            self.logger.info(
                "Context switched",
                session_id=current_session["session_id"],
                new_context_type=new_context_type,
                impersonated_user_id=impersonated_user_id,
                reason=switch_reason,
            )

            return {
                "success": True,
                "message": "Contexto alterado com sucesso",
                "session_data": updated_session,
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(
                "Error switching context",
                session_token=session_token[:20],
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao trocar contexto",
            )

    async def terminate_session(
        self, session_token: str, reason: str = "User logout"
    ) -> bool:
        """
        Terminar sessão
        """
        try:
            query = text(
                """
                UPDATE master.user_sessions
                SET
                    is_active = false,
                    terminated_at = CURRENT_TIMESTAMP,
                    termination_reason = :reason
                WHERE session_token = :session_token
                  AND is_active = true
            """
            )

            result = await self.db.execute(
                query, {"session_token": session_token, "reason": reason}
            )

            await self.db.commit()

            affected_rows = result.rowcount
            if affected_rows > 0:
                self.logger.info(
                    "Session terminated",
                    session_token=session_token[:20],
                    reason=reason,
                )
                return True

            return False

        except Exception as e:
            await self.db.rollback()
            self.logger.error(
                "Error terminating session",
                session_token=session_token[:20],
                error=str(e),
            )
            return False

    async def cleanup_expired_sessions(self) -> int:
        """
        Limpar sessões expiradas
        """
        try:
            query = text(
                """
                UPDATE master.user_sessions
                SET
                    is_active = false,
                    terminated_at = CURRENT_TIMESTAMP,
                    termination_reason = 'Expired'
                WHERE is_active = true
                  AND expires_at < CURRENT_TIMESTAMP
            """
            )

            result = await self.db.execute(query)
            await self.db.commit()

            cleaned_sessions = result.rowcount
            if cleaned_sessions > 0:
                self.logger.info("Expired sessions cleaned", count=cleaned_sessions)

            return cleaned_sessions

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error cleaning expired sessions", error=str(e))
            return 0
