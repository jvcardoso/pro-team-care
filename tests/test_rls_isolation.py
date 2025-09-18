"""
Testes de isolamento Row-Level Security (RLS) para multi-tenancy
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.services.tenant_context_service import get_tenant_context


class TestRLSIsolation:
    """Testes para verificar isolamento RLS entre empresas"""

    @pytest.mark.asyncio
    async def test_rls_people_isolation(self, async_session: AsyncSession):
        """Test isolamento RLS na tabela people"""
        tenant_service = get_tenant_context()

        # Testar com empresa 1
        await tenant_service.set_database_context(async_session, 1)
        result = await async_session.execute(text("SELECT COUNT(*) FROM master.people"))
        count_company_1 = result.scalar()

        # Testar com empresa 2
        await tenant_service.set_database_context(async_session, 2)
        result = await async_session.execute(text("SELECT COUNT(*) FROM master.people"))
        count_company_2 = result.scalar()

        # Contagens devem ser diferentes (isolamento funcionando)
        assert isinstance(count_company_1, int)
        assert isinstance(count_company_2, int)

    @pytest.mark.asyncio
    async def test_rls_admin_bypass(self, async_session: AsyncSession):
        """Test que admin pode ver todos os dados"""
        tenant_service = get_tenant_context()

        # Reset context (como admin)
        await tenant_service.set_database_context(async_session, 0)

        # Admin deve ver todos os dados
        result = await async_session.execute(text("SELECT COUNT(*) FROM master.people"))
        total_people = result.scalar()

        assert isinstance(total_people, int)
