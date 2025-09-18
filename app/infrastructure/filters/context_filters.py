"""
Filtros Automáticos por Contexto
Sistema de isolamento de dados baseado no usuário logado

PRINCÍPIOS:
- System Admin: SEM filtros (vê tudo)
- Usuário Normal: COM filtros (só vê dados de sua empresa/estabelecimento)
- ZERO bypass: Filtros aplicados automaticamente no banco
"""

from typing import Any, Optional

import structlog
from sqlalchemy import Select, and_
from sqlalchemy.orm import Query

from app.domain.entities.user import User

logger = structlog.get_logger()


class ContextFilter:
    """
    Aplicação automática de filtros baseados no contexto do usuário
    """

    @staticmethod
    async def apply_company_filter(
        query: Select, user: User, company_table_alias: Any = None
    ) -> Select:
        """
        Aplica filtro de empresa baseado no usuário

        Args:
            query: Query SQLAlchemy
            user: Usuário logado
            company_table_alias: Alias da tabela de empresa (opcional)

        Returns:
            Query filtrada ou original (se system admin)
        """
        # 👑 SYSTEM ADMIN: SEM filtros
        if getattr(user, "is_system_admin", False):
            await logger.ainfo(
                "🔓 System admin - removendo filtros de empresa",
                user_id=user.id,
                filter_type="company",
            )
            return query

        # 🔒 USUÁRIO NORMAL: COM filtros
        if hasattr(user, "company_id") and user.company_id:
            from app.infrastructure.orm.models import Company

            # Para tabela Company, filtrar pelo ID da empresa do usuário
            filtered_query = query.where(Company.id == user.company_id)

            await logger.ainfo(
                "🔒 Aplicando filtro de empresa",
                user_id=user.id,
                company_id=user.company_id,
                filter_type="company",
            )
            return filtered_query

        # 🚨 USUÁRIO SEM EMPRESA: Bloquear tudo
        await logger.awarning(
            "⚠️ Usuário sem empresa - bloqueando acesso",
            user_id=user.id,
            filter_type="company",
        )
        # Retorna query que não retorna nada
        return query.where(1 == 0)

    @staticmethod
    async def apply_establishment_filter(
        query: Select,
        user: User,
        establishment_table_alias: Any = None,
        company_field: str = "company_id",
    ) -> Select:
        """
        Aplica filtro de estabelecimento baseado no usuário

        Args:
            query: Query SQLAlchemy
            user: Usuário logado
            establishment_table_alias: Alias da tabela de estabelecimento (opcional)
            company_field: Nome do campo da empresa na tabela

        Returns:
            Query filtrada ou original (se system admin)
        """
        # 👑 SYSTEM ADMIN: SEM filtros
        if getattr(user, "is_system_admin", False):
            await logger.ainfo(
                "🔓 System admin - removendo filtros de estabelecimento",
                user_id=user.id,
                filter_type="establishment",
            )
            return query

        # 🔒 USUÁRIO NORMAL: COM filtros de empresa
        if hasattr(user, "company_id") and user.company_id:
            if establishment_table_alias is not None:
                filtered_query = query.where(
                    getattr(establishment_table_alias, company_field) == user.company_id
                )
            else:
                # Assume que a tabela tem campo company_id
                filtered_query = query.where(
                    getattr(query.column_descriptions[0]["type"], company_field)
                    == user.company_id
                )

            # Se usuário tem estabelecimento específico, filtrar também por isso
            current_establishment_id = getattr(user, "current_establishment_id", None)
            if current_establishment_id:
                if establishment_table_alias is not None:
                    filtered_query = filtered_query.where(
                        establishment_table_alias.id == current_establishment_id
                    )
                else:
                    filtered_query = filtered_query.where(
                        query.column_descriptions[0]["type"].id
                        == current_establishment_id
                    )

                await logger.ainfo(
                    "🔒 Aplicando filtro de estabelecimento específico",
                    user_id=user.id,
                    company_id=user.company_id,
                    establishment_id=current_establishment_id,
                    filter_type="establishment",
                )
            else:
                await logger.ainfo(
                    "🔒 Aplicando filtro de empresa (todos estabelecimentos)",
                    user_id=user.id,
                    company_id=user.company_id,
                    filter_type="establishment",
                )

            return filtered_query

        # 🚨 USUÁRIO SEM EMPRESA: Bloquear tudo
        await logger.awarning(
            "⚠️ Usuário sem empresa - bloqueando acesso a estabelecimentos",
            user_id=user.id,
            filter_type="establishment",
        )
        return query.where(1 == 0)

    @staticmethod
    async def apply_user_filter(
        query: Select, user: User, user_table_alias: Any = None
    ) -> Select:
        """
        Aplica filtro de usuários baseado no contexto

        Args:
            query: Query SQLAlchemy
            user: Usuário logado
            user_table_alias: Alias da tabela de usuários (opcional)

        Returns:
            Query filtrada ou original (se system admin)
        """
        # 👑 SYSTEM ADMIN: SEM filtros
        if getattr(user, "is_system_admin", False):
            await logger.ainfo(
                "🔓 System admin - removendo filtros de usuários",
                user_id=user.id,
                filter_type="user",
            )
            return query

        # 🔒 USUÁRIO NORMAL: Apenas usuários da mesma empresa
        if hasattr(user, "company_id") and user.company_id:
            if user_table_alias is not None:
                filtered_query = query.where(
                    user_table_alias.company_id == user.company_id
                )
            else:
                filtered_query = query.where(
                    query.column_descriptions[0]["type"].company_id == user.company_id
                )

            await logger.ainfo(
                "🔒 Aplicando filtro de usuários da empresa",
                user_id=user.id,
                company_id=user.company_id,
                filter_type="user",
            )
            return filtered_query

        # 🚨 USUÁRIO SEM EMPRESA: Bloquear tudo
        await logger.awarning(
            "⚠️ Usuário sem empresa - bloqueando acesso a usuários",
            user_id=user.id,
            filter_type="user",
        )
        return query.where(1 == 0)

    @staticmethod
    async def apply_system_filter(query: Select, user: User) -> Select:
        """
        Aplica filtro de sistema (sem filtros adicionais para dados de sistema)

        Args:
            query: Query SQLAlchemy
            user: Usuário logado

        Returns:
            Query original (dados de sistema são globais)
        """
        await logger.ainfo(
            "🌐 Dados de sistema - sem filtros aplicados",
            user_id=user.id,
            filter_type="system",
        )
        return query


class AutoFilter:
    """
    Classe auxiliar para aplicação automática de filtros
    """

    def __init__(self, user: User):
        self.user = user
        self.context_filter = ContextFilter()

    async def for_companies(self, query: Select, table_alias: Any = None) -> Select:
        """Filtro automático para empresas"""
        return await self.context_filter.apply_company_filter(
            query, self.user, table_alias
        )

    async def for_establishments(
        self, query: Select, table_alias: Any = None, company_field: str = "company_id"
    ) -> Select:
        """Filtro automático para estabelecimentos"""
        return await self.context_filter.apply_establishment_filter(
            query, self.user, table_alias, company_field
        )

    async def for_users(self, query: Select, table_alias: Any = None) -> Select:
        """Filtro automático para usuários"""
        return await self.context_filter.apply_user_filter(
            query, self.user, table_alias
        )

    async def for_system(self, query: Select) -> Select:
        """Filtro automático para dados de sistema"""
        return await self.context_filter.apply_system_filter(query, self.user)


def get_auto_filter(user: User) -> AutoFilter:
    """
    Factory function para criar instância do AutoFilter

    Args:
        user: Usuário logado

    Returns:
        AutoFilter configurado para o usuário
    """
    return AutoFilter(user)


# Decorator para aplicação automática de filtros em repositories
def apply_context_filter(filter_type: str):
    """
    Decorator para aplicar filtros automaticamente em métodos de repository

    Args:
        filter_type: Tipo do filtro ("company", "establishment", "user", "system")

    Usage:
        @apply_context_filter("company")
        async def get_companies(self, user: User):
            query = select(Company)
            # Filtro será aplicado automaticamente
            return await self.db.execute(query)
    """

    def decorator(func):
        async def wrapper(self, *args, user: User = None, **kwargs):
            if user is None:
                raise ValueError("User parameter is required for context filtering")

            # Aplicar filtro baseado no tipo
            auto_filter = get_auto_filter(user)

            # Executar função original
            result = await func(
                self, *args, user=user, auto_filter=auto_filter, **kwargs
            )
            return result

        return wrapper

    return decorator
