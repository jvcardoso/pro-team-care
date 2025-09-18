from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.dto.user_dto import UserCreateWithInvitation, UserResponse
from app.domain.entities.user import User as UserDomain
from app.infrastructure.auth import get_password_hash
from app.infrastructure.orm.models import Company, Establishments, People, User
from app.infrastructure.services.email_service import EmailService


class UserManagementUseCase:
    """Use case para gestão de usuários com ativação por email"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()

    async def create_company_manager(
        self,
        email: str,
        company_id: int,
        invited_by_user_id: Optional[int] = None,
    ) -> UserResponse:
        """
        Cria usuário gestor para empresa

        Args:
            email: Email do gestor
            company_id: ID da empresa
            invited_by_user_id: ID do usuário que fez o convite

        Returns:
            UserResponse: Dados do usuário criado
        """
        # Verificar se empresa existe
        company_query = select(Company).where(Company.id == company_id)
        company_result = await self.db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise ValueError("Empresa não encontrada")

        # Verificar se usuário já existe
        existing_user_query = select(User).where(
            and_(User.email_address == email, User.company_id == company_id)
        )
        existing_user_result = await self.db.execute(existing_user_query)
        existing_user = existing_user_result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Usuário já existe para esta empresa")

        # Buscar dados da empresa/pessoa
        company_data_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == company_id)
        )
        company_data_result = await self.db.execute(company_data_query)
        company_data = company_data_result.scalar_one()

        if not company_data.people:
            raise ValueError("Empresa não possui dados de pessoa vinculados")

        # Gerar tokens
        activation_token = EmailService.generate_token()
        activation_expires_at = EmailService.get_token_expiry(24)  # 24 horas

        # Criar usuário
        new_user = User(
            person_id=company_data.person_id,
            company_id=company_id,
            establishment_id=None,  # Gestor da empresa não tem estabelecimento específico
            email_address=email,
            password=get_password_hash(
                "temp_password_will_be_changed"
            ),  # Senha temporária
            context_type="company",
            status="pending",
            activation_token=activation_token,
            activation_expires_at=activation_expires_at,
            invited_by_user_id=invited_by_user_id,
            invited_at=datetime.utcnow(),
            is_active=False,  # Será ativado após confirmação
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Enviar email de ativação
        await self.email_service.send_activation_email(
            email=email,
            activation_token=activation_token,
            user_name=company_data.people.name,
            company_name=company_data.people.name,
            context_type="company",
        )

        return UserResponse(
            id=new_user.id,
            email_address=new_user.email_address,
            context_type=new_user.context_type,
            status=new_user.status,
            company_id=new_user.company_id,
            establishment_id=new_user.establishment_id,
            created_at=new_user.created_at,
        )

    async def create_establishment_manager(
        self,
        email: str,
        establishment_id: int,
        invited_by_user_id: Optional[int] = None,
    ) -> UserResponse:
        """
        Cria usuário gestor para estabelecimento

        Args:
            email: Email do gestor
            establishment_id: ID do estabelecimento
            invited_by_user_id: ID do usuário que fez o convite

        Returns:
            UserResponse: Dados do usuário criado
        """
        # Verificar se estabelecimento existe
        establishment_query = (
            select(Establishments)
            .options(
                selectinload(Establishments.person),
                selectinload(Establishments.company),
            )
            .where(Establishments.id == establishment_id)
        )
        establishment_result = await self.db.execute(establishment_query)
        establishment = establishment_result.scalar_one_or_none()

        if not establishment:
            raise ValueError("Estabelecimento não encontrado")

        # Verificar se usuário já existe
        existing_user_query = select(User).where(
            and_(
                User.email_address == email,
                User.company_id == establishment.company_id,
                User.establishment_id == establishment_id,
            )
        )
        existing_user_result = await self.db.execute(existing_user_query)
        existing_user = existing_user_result.scalar_one_or_none()

        if existing_user:
            raise ValueError("Usuário já existe para este estabelecimento")

        # Gerar tokens
        activation_token = EmailService.generate_token()
        activation_expires_at = EmailService.get_token_expiry(24)  # 24 horas

        # Criar usuário
        new_user = User(
            person_id=establishment.person_id,
            company_id=establishment.company_id,
            establishment_id=establishment_id,
            email_address=email,
            password=get_password_hash(
                "temp_password_will_be_changed"
            ),  # Senha temporária
            context_type="establishment",
            status="pending",
            activation_token=activation_token,
            activation_expires_at=activation_expires_at,
            invited_by_user_id=invited_by_user_id,
            invited_at=datetime.utcnow(),
            is_active=False,  # Será ativado após confirmação
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Buscar dados da empresa para o email
        company_data_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == establishment.company_id)
        )
        company_data_result = await self.db.execute(company_data_query)
        company_data = company_data_result.scalar_one()

        # Enviar email de ativação
        await self.email_service.send_activation_email(
            email=email,
            activation_token=activation_token,
            user_name=establishment.person.name,
            company_name=company_data.people.name,
            context_type="establishment",
        )

        return UserResponse(
            id=new_user.id,
            email_address=new_user.email_address,
            context_type=new_user.context_type,
            status=new_user.status,
            company_id=new_user.company_id,
            establishment_id=new_user.establishment_id,
            created_at=new_user.created_at,
        )

    async def activate_user(
        self, activation_token: str, new_password: str
    ) -> UserResponse:
        """
        Ativa usuário usando token de ativação

        Args:
            activation_token: Token de ativação
            new_password: Nova senha do usuário

        Returns:
            UserResponse: Dados do usuário ativado
        """
        # Buscar usuário pelo token
        user_query = select(User).where(User.activation_token == activation_token)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("Token de ativação inválido")

        # Verificar se token não expirou
        if not EmailService.is_token_valid(user.activation_expires_at):
            raise ValueError("Token de ativação expirado")

        # Verificar se usuário já foi ativado
        if user.status == "active":
            raise ValueError("Usuário já foi ativado")

        # Ativar usuário
        user.password = get_password_hash(new_password)
        user.status = "active"
        user.is_active = True
        user.activated_at = datetime.utcnow()
        user.activation_token = None  # Limpar token usado
        user.activation_expires_at = None

        await self.db.commit()
        await self.db.refresh(user)

        return UserResponse(
            id=user.id,
            email_address=user.email_address,
            context_type=user.context_type,
            status=user.status,
            company_id=user.company_id,
            establishment_id=user.establishment_id,
            created_at=user.created_at,
            activated_at=user.activated_at,
        )

    async def resend_activation_email(self, user_id: int) -> bool:
        """
        Reenvia email de ativação para um usuário

        Args:
            user_id: ID do usuário

        Returns:
            bool: True se email foi enviado
        """
        # Buscar usuário
        user_query = (
            select(User)
            .options(
                selectinload(User.person),
                selectinload(User.company),
                selectinload(User.establishment),
            )
            .where(User.id == user_id)
        )
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise ValueError("Usuário não encontrado")

        if user.status == "active":
            raise ValueError("Usuário já está ativo")

        # Gerar novo token
        activation_token = EmailService.generate_token()
        activation_expires_at = EmailService.get_token_expiry(24)

        user.activation_token = activation_token
        user.activation_expires_at = activation_expires_at

        await self.db.commit()

        # Buscar dados da empresa
        company_data_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == user.company_id)
        )
        company_data_result = await self.db.execute(company_data_query)
        company_data = company_data_result.scalar_one()

        # Enviar email
        return await self.email_service.send_activation_email(
            email=user.email_address,
            activation_token=activation_token,
            user_name=user.person.name,
            company_name=company_data.people.name,
            context_type=user.context_type,
        )
