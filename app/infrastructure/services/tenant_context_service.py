"""
Serviço de contexto multi-tenant
Gerencia o contexto da empresa atual para isolamento de dados
"""

from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session


class TenantContextService:
    """Serviço para gerenciar contexto multi-tenant"""

    def __init__(self):
        self._current_company_id: Optional[int] = None

    @property
    def current_company_id(self) -> Optional[int]:
        """Obter ID da empresa atual"""
        return self._current_company_id

    def set_company_id(self, company_id: Optional[int]) -> None:
        """Definir ID da empresa atual"""
        self._current_company_id = company_id

    async def set_database_context(
        self, session: AsyncSession, company_id: Optional[int]
    ) -> None:
        """Definir contexto da empresa na sessão do banco de dados"""
        if company_id is not None and company_id != -1:
            await session.execute(
                text("SELECT master.set_current_company_id(:company_id)"),
                {"company_id": company_id},
            )
        else:
            # Reset context or global access
            await session.execute(text("SELECT master.set_current_company_id(0)"))

    @asynccontextmanager
    async def company_context(self, company_id: int):
        """Context manager para executar operações no contexto de uma empresa específica"""
        previous_company_id = self._current_company_id

        try:
            # Definir novo contexto
            self.set_company_id(company_id)

            # Aplicar contexto no banco de dados
            async with async_session() as session:
                await self.set_database_context(session, company_id)
                yield session

        finally:
            # Restaurar contexto anterior
            self.set_company_id(previous_company_id)

            # Restaurar contexto no banco de dados
            async with async_session() as session:
                await self.set_database_context(session, previous_company_id)

    async def get_user_company_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[int]:
        """Obter company_id de um usuário específico"""
        result = await session.execute(
            text("SELECT company_id FROM master.users WHERE id = :user_id"),
            {"user_id": user_id},
        )

        row = result.fetchone()
        return row.company_id if row else None

    async def validate_company_access(
        self, session: AsyncSession, user_id: int, company_id: int
    ) -> bool:
        """Validar se um usuário tem acesso a uma empresa específica"""
        user_company_id = await self.get_user_company_id(session, user_id)
        return user_company_id == company_id

    async def get_company_users_count(
        self, session: AsyncSession, company_id: int
    ) -> int:
        """Obter quantidade de usuários de uma empresa"""
        # Definir contexto temporariamente
        await self.set_database_context(session, company_id)

        result = await session.execute(text("SELECT COUNT(*) FROM master.users"))

        return result.scalar() or 0

    async def get_company_people_count(
        self, session: AsyncSession, company_id: int
    ) -> int:
        """Obter quantidade de pessoas de uma empresa"""
        # Definir contexto temporariamente
        await self.set_database_context(session, company_id)

        result = await session.execute(text("SELECT COUNT(*) FROM master.people"))

        return result.scalar() or 0


# Instância global do serviço
tenant_context = TenantContextService()


def get_tenant_context() -> TenantContextService:
    """Dependency injection para obter o contexto multi-tenant"""
    return tenant_context


async def setup_tenant_session(
    session: AsyncSession, company_id: Optional[int] = None
) -> AsyncSession:
    """Configurar sessão com contexto multi-tenant"""
    if company_id is None:
        company_id = tenant_context.current_company_id

    if company_id is not None:
        await tenant_context.set_database_context(session, company_id)

    return session
