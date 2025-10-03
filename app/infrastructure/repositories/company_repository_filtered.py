"""
Company Repository com Filtros Automáticos
Implementa isolamento de dados baseado no usuário logado
"""

from typing import List, Optional

import structlog
from sqlalchemy import and_, or_, select, func
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.user import User
from app.infrastructure.filters.context_filters import get_auto_filter

from app.infrastructure.orm.models import (
    Company,
    People,
    Establishments,
    Client,
    Professional,
    User as UserModel,
)
from app.infrastructure.repositories.company_repository import CompanyRepository

logger = structlog.get_logger()


class FilteredCompanyRepository(CompanyRepository):
    """
    Repository de empresas com filtros automáticos aplicados
    """

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_companies_filtered(
        self,
        user: User,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 100,
    ) -> List[Company]:
        """
        Buscar empresas aplicando filtros baseados no usuário

        Args:
            user: Usuário logado
            is_active: Filtro por status ativo (opcional) - baseado em people.status
            page: Página da paginação
            size: Tamanho da página

        Returns:
            Lista de empresas filtradas baseadas no contexto do usuário
        """
        try:
            # Usar alias para Company para evitar problemas de correlação
            company_alias = aliased(Company)

            # Construir query base com contagens calculadas no banco usando subqueries correlacionadas
            establishments_count_sub = select(func.count(Establishments.id)).where(Establishments.company_id == company_alias.id).correlate(company_alias).scalar_subquery().label('establishments_count')
            clients_count_sub = select(func.count(func.distinct(Client.id))).select_from(Establishments).join(Client, Client.establishment_id == Establishments.id).where(Establishments.company_id == company_alias.id).correlate(company_alias).scalar_subquery().label('clients_count')
            professionals_count_sub = select(func.count(func.distinct(Professional.id))).select_from(Establishments).join(Professional, Professional.establishment_id == Establishments.id).where(Establishments.company_id == company_alias.id).correlate(company_alias).scalar_subquery().label('professionals_count')
            users_count_sub = select(func.count(UserModel.id)).where(UserModel.company_id == company_alias.id).correlate(company_alias).scalar_subquery().label('users_count')

            query = (
                select(company_alias)
                .add_columns(
                    establishments_count_sub,
                    clients_count_sub,
                    professionals_count_sub,
                    users_count_sub
                )
                .join(People, company_alias.person_id == People.id)
                .where(company_alias.deleted_at.is_(None))  # Excluir registros deletados
                .options(selectinload(company_alias.people))
            )

            # Aplicar filtro de status se especificado (baseado na tabela people)
            if is_active is not None:
                status_value = "active" if is_active else "inactive"
                query = query.where(People.status == status_value)

            # 🔒 APLICAR FILTROS DE CONTEXTO AUTOMATICAMENTE
            auto_filter = get_auto_filter(user)
            query = await auto_filter.for_companies(query, company_alias)

            # Aplicar paginação
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            # Executar query
            result = await self.db.execute(query)
            rows = result.all()

            # Processar resultados e adicionar contagens aos objetos Company
            companies = []
            for row in rows:
                company = row[0]  # Company object
                company.establishments_count = row[1] or 0
                company.clients_count = row[2] or 0
                company.professionals_count = row[3] or 0
                company.users_count = row[4] or 0
                companies.append(company)

            await logger.ainfo(
                "✅ Empresas carregadas com filtros",
                user_id=user.id,
                is_system_admin=getattr(user, "is_system_admin", False),
                company_count=len(companies),
                page=page,
                size=size,
            )

            return list(companies)

        except Exception as e:
            await logger.aerror(
                "❌ Erro ao carregar empresas filtradas", user_id=user.id, error=str(e)
            )
            raise

    async def get_company_by_id_filtered(
        self, user: User, company_id: int
    ) -> Optional[Company]:
        """
        Buscar empresa por ID aplicando filtros de segurança

        Args:
            user: Usuário logado
            company_id: ID da empresa

        Returns:
            Empresa se o usuário tem acesso, None caso contrário
        """
        try:
            # Construir query
            query = (
                select(Company)
                .options(
                    selectinload(Company.people).selectinload(People.phones),
                    selectinload(Company.people).selectinload(People.emails),
                    selectinload(Company.people).selectinload(People.addresses),
                )
                .where(Company.id == company_id)
            )

            # 🔒 APLICAR FILTROS DE CONTEXTO
            auto_filter = get_auto_filter(user)
            query = await auto_filter.for_companies(query, Company)

            # Executar query
            result = await self.db.execute(query)
            company = result.scalar_one_or_none()

            if company:
                await logger.ainfo(
                    "✅ Empresa encontrada com acesso autorizado",
                    user_id=user.id,
                    company_id=company_id,
                    is_system_admin=getattr(user, "is_system_admin", False),
                )
            else:
                await logger.awarning(
                    "🚫 Empresa não encontrada ou acesso negado",
                    user_id=user.id,
                    company_id=company_id,
                    is_system_admin=getattr(user, "is_system_admin", False),
                )

            return company

        except Exception as e:
            await logger.aerror(
                "❌ Erro ao buscar empresa por ID",
                user_id=user.id,
                company_id=company_id,
                error=str(e),
            )
            raise

    async def get_companies_by_cnpj_filtered(
        self, user: User, cnpj: str
    ) -> Optional[Company]:
        """
        Buscar empresa por CNPJ aplicando filtros de segurança

        Args:
            user: Usuário logado
            cnpj: CNPJ da empresa

        Returns:
            Empresa se o usuário tem acesso, None caso contrário
        """
        try:
            # Construir query
            query = (
                select(Company)
                .join(People, Company.person_id == People.id)
                .options(
                    selectinload(Company.people).selectinload(People.phones),
                    selectinload(Company.people).selectinload(People.emails),
                    selectinload(Company.people).selectinload(People.addresses),
                )
                .where(People.tax_id == cnpj)
            )

            # 🔒 APLICAR FILTROS DE CONTEXTO
            auto_filter = get_auto_filter(user)
            query = await auto_filter.for_companies(query, Company)

            # Executar query
            result = await self.db.execute(query)
            company = result.scalar_one_or_none()

            if company:
                await logger.ainfo(
                    "✅ Empresa encontrada por CNPJ com acesso autorizado",
                    user_id=user.id,
                    cnpj=cnpj,
                    company_id=company.id,
                    is_system_admin=getattr(user, "is_system_admin", False),
                )
            else:
                await logger.awarning(
                    "🚫 Empresa não encontrada por CNPJ ou acesso negado",
                    user_id=user.id,
                    cnpj=cnpj,
                    is_system_admin=getattr(user, "is_system_admin", False),
                )

            return company

        except Exception as e:
            await logger.aerror(
                "❌ Erro ao buscar empresa por CNPJ",
                user_id=user.id,
                cnpj=cnpj,
                error=str(e),
            )
            raise

    async def count_companies_filtered(
        self, user: User, is_active: Optional[bool] = None
    ) -> int:
        """
        Contar empresas aplicando filtros baseados no usuário

        Args:
            user: Usuário logado
            is_active: Filtro por status ativo (opcional)

        Returns:
            Número de empresas que o usuário pode ver
        """
        try:
            from sqlalchemy import func

            # Construir query de contagem
            query = select(func.count(Company.id)).join(
                People, Company.person_id == People.id
            )

            # Aplicar filtro de status se especificado (baseado na tabela people)
            if is_active is not None:
                status_value = "active" if is_active else "inactive"
                query = query.where(People.status == status_value)

            # 🔒 APLICAR FILTROS DE CONTEXTO
            auto_filter = get_auto_filter(user)
            query = await auto_filter.for_companies(query, Company)

            # Executar query
            result = await self.db.execute(query)
            count = result.scalar() or 0

            await logger.ainfo(
                "📊 Contagem de empresas filtradas",
                user_id=user.id,
                is_system_admin=getattr(user, "is_system_admin", False),
                total_count=count,
            )

            return count

        except Exception as e:
            await logger.aerror(
                "❌ Erro ao contar empresas filtradas", user_id=user.id, error=str(e)
            )
            raise


# Factory function para criar instância filtrada
async def get_filtered_company_repository(
    db: AsyncSession,
) -> FilteredCompanyRepository:
    """
    Factory para criar repository de empresas com filtros

    Args:
        db: Sessão do banco de dados

    Returns:
        Repository filtrado configurado
    """
    return FilteredCompanyRepository(db)
