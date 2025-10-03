"""
Use Case para processo de ativação de empresas

Este use case implementa toda a lógica de negócio para:
1. Envio de email de aceite de contrato
2. Registro de aceite de contrato
3. Envio de email de criação de usuário gestor
4. Validação de tokens
5. Consulta de status de ativação
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.infrastructure.orm.models import Company, People, User
from app.infrastructure.services.email_service import EmailService
from app.presentation.schemas.company_activation import (
    AcceptContractResponse,
    CompanyActivationStatus,
    SendEmailResponse,
    ValidateTokenResponse,
)


class CompanyActivationUseCase:
    """Use case para gestão de ativação de empresas"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()

    async def send_contract_email(
        self,
        company_id: int,
        recipient_email: str,
        recipient_name: str,
    ) -> SendEmailResponse:
        """
        Envia email de aceite de contrato para empresa

        Args:
            company_id: ID da empresa
            recipient_email: Email do destinatário
            recipient_name: Nome do destinatário

        Returns:
            SendEmailResponse com resultado do envio

        Raises:
            ValueError: Se empresa não encontrada ou status inválido
        """
        # Buscar empresa com dados de pessoa
        company_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == company_id)
        )
        result = await self.db.execute(company_query)
        company = result.scalar_one_or_none()

        if not company:
            raise ValueError(f"Empresa {company_id} não encontrada")

        if not company.people:
            raise ValueError("Empresa sem dados de pessoa vinculados")

        # Verificar se já está ativa
        if company.access_status == "active":
            raise ValueError("Empresa já está ativa. Não é necessário enviar email de ativação.")

        # Verificar se contrato já foi aceito
        if company.access_status == "contract_signed":
            raise ValueError("Contrato já foi aceito. Empresa aguardando criação de usuário.")

        # Gerar token de aceite de contrato (expira em 7 dias)
        contract_token = EmailService.generate_token()

        # Atualizar empresa
        company.activation_sent_at = datetime.utcnow()
        company.activation_sent_to = recipient_email

        # Armazenar token em metadata temporário
        if not company.metadata_:
            company.metadata_ = {}

        company.metadata_["contract_token"] = contract_token
        company.metadata_["contract_token_expires_at"] = (
            datetime.utcnow() + timedelta(days=7)
        ).isoformat()

        # Marcar metadata como modificado para SQLAlchemy detectar a mudança
        flag_modified(company, "metadata_")

        await self.db.commit()
        await self.db.refresh(company)

        # Enviar email
        email_sent = await self.email_service.send_contract_acceptance_email(
            company_name=company.people.name,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            contract_token=contract_token,
        )

        if not email_sent:
            raise ValueError("Falha ao enviar email. Tente novamente.")

        return SendEmailResponse(
            success=True,
            message="Email de aceite de contrato enviado com sucesso",
            company_id=company.id,
            sent_to=recipient_email,
            sent_at=company.activation_sent_at,
        )

    async def accept_contract(
        self,
        contract_token: str,
        accepted_by_name: str,
        accepted_by_email: str,
        ip_address: str,
        terms_version: str = "1.0",
        accepted_by_cpf: str = None,
    ) -> AcceptContractResponse:
        """
        Registra aceite de contrato e envia email de criação de usuário

        Args:
            contract_token: Token de aceite do contrato
            accepted_by_name: Nome de quem aceita
            accepted_by_email: Email de quem aceita
            ip_address: IP de origem
            terms_version: Versão dos termos
            accepted_by_cpf: CPF de quem aceita (opcional, compliance)

        Returns:
            AcceptContractResponse com resultado

        Raises:
            ValueError: Se token inválido ou expirado
        """
        # Buscar empresa pelo token em metadata
        companies_query = select(Company).options(selectinload(Company.people))
        result = await self.db.execute(companies_query)
        companies = result.scalars().all()

        company = None
        for c in companies:
            if c.metadata_ and c.metadata_.get("contract_token") == contract_token:
                company = c
                break

        if not company:
            raise ValueError("Token de contrato inválido")

        # Verificar expiração do token
        token_expires_at_str = company.metadata_.get("contract_token_expires_at")
        if token_expires_at_str:
            token_expires_at = datetime.fromisoformat(token_expires_at_str)
            if datetime.utcnow() > token_expires_at:
                raise ValueError("Token de contrato expirado. Entre em contato com o suporte.")

        # Verificar se já foi aceito
        if company.access_status == "contract_signed":
            raise ValueError("Contrato já foi aceito anteriormente")

        if company.access_status == "active":
            raise ValueError("Empresa já está ativa")

        # Registrar aceite de contrato
        company.access_status = "contract_signed"
        company.contract_accepted_at = datetime.utcnow()
        company.contract_accepted_by = f"{accepted_by_name} <{accepted_by_email}>"
        company.contract_ip_address = ip_address
        company.contract_terms_version = terms_version

        # Salvar CPF no metadata (compliance LGPD)
        if accepted_by_cpf:
            if not company.metadata_:
                company.metadata_ = {}
            company.metadata_["contract_accepted_by_cpf"] = accepted_by_cpf
            flag_modified(company, "metadata_")

        # Limpar token de contrato usado
        if company.metadata_:
            company.metadata_.pop("contract_token", None)
            company.metadata_.pop("contract_token_expires_at", None)
            flag_modified(company, "metadata_")

        await self.db.commit()
        await self.db.refresh(company)

        # Gerar token de criação de usuário (expira em 24h)
        user_creation_token = EmailService.generate_token()

        # Armazenar token de criação de usuário
        if not company.metadata_:
            company.metadata_ = {}

        company.metadata_["user_creation_token"] = user_creation_token
        company.metadata_["user_creation_token_expires_at"] = (
            datetime.utcnow() + timedelta(hours=24)
        ).isoformat()
        company.metadata_["user_creation_email"] = accepted_by_email

        # Marcar metadata como modificado
        flag_modified(company, "metadata_")

        # Atualizar status para pending_user
        company.access_status = "pending_user"

        await self.db.commit()
        await self.db.refresh(company)

        # Enviar email de criação de usuário
        email_sent = await self.email_service.send_create_manager_email(
            company_name=company.people.name,
            recipient_email=accepted_by_email,
            recipient_name=accepted_by_name,
            user_creation_token=user_creation_token,
        )

        if not email_sent:
            # Não falhar aqui, apenas registrar
            print(f"AVISO: Email de criação de usuário não foi enviado para {accepted_by_email}")

        return AcceptContractResponse(
            success=True,
            message="Contrato aceito com sucesso",
            company_id=company.id,
            access_status=company.access_status,
            contract_accepted_at=company.contract_accepted_at,
            next_step="Email de criação de usuário enviado. Verifique sua caixa de entrada.",
        )

    async def validate_user_creation_token(
        self, user_creation_token: str
    ) -> ValidateTokenResponse:
        """
        Valida token de criação de usuário

        Args:
            user_creation_token: Token de criação de usuário

        Returns:
            ValidateTokenResponse com resultado da validação
        """
        # Buscar empresa pelo token
        companies_query = select(Company).options(selectinload(Company.people))
        result = await self.db.execute(companies_query)
        companies = result.scalars().all()

        company = None
        for c in companies:
            if (
                c.metadata_
                and c.metadata_.get("user_creation_token") == user_creation_token
            ):
                company = c
                break

        if not company:
            return ValidateTokenResponse(
                valid=False,
                error_message="Token de criação de usuário inválido",
            )

        # Verificar expiração
        token_expires_at_str = company.metadata_.get("user_creation_token_expires_at")
        if token_expires_at_str:
            token_expires_at = datetime.fromisoformat(token_expires_at_str)
            if datetime.utcnow() > token_expires_at:
                return ValidateTokenResponse(
                    valid=False,
                    company_id=company.id,
                    company_name=company.people.name,
                    token_type="user_creation",
                    expires_at=token_expires_at,
                    expired=True,
                    error_message="Token de criação expirado. Entre em contato com o suporte.",
                )

        return ValidateTokenResponse(
            valid=True,
            company_id=company.id,
            company_name=company.people.name,
            token_type="user_creation",
            expires_at=token_expires_at if token_expires_at_str else None,
            expired=False,
        )

    async def create_manager_user_from_token(
        self,
        user_creation_token: str,
        user_name: str,
        user_email: str,
        password: str,
    ) -> dict:
        """
        Cria usuário gestor usando token de criação

        Args:
            user_creation_token: Token de criação
            user_name: Nome do usuário
            user_email: Email do usuário
            password: Senha

        Returns:
            dict com dados do usuário criado

        Raises:
            ValueError: Se token inválido ou usuário já existe
        """
        from app.infrastructure.auth import get_password_hash

        # Validar token
        validation = await self.validate_user_creation_token(user_creation_token)
        if not validation.valid:
            raise ValueError(validation.error_message or "Token inválido")

        company_id = validation.company_id

        # Buscar empresa
        company_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == company_id)
        )
        result = await self.db.execute(company_query)
        company = result.scalar_one_or_none()

        if not company:
            raise ValueError("Empresa não encontrada")

        # Verificar se já existe usuário
        existing_user_query = select(User).where(
            and_(User.email_address == user_email, User.company_id == company_id)
        )
        existing_result = await self.db.execute(existing_user_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("Usuário já existe para esta empresa")

        # Criar usuário
        new_user = User(
            person_id=company.person_id,
            company_id=company.id,
            establishment_id=None,
            email_address=user_email,
            password=get_password_hash(password),
            context_type="company",
            status="active",
            is_active=True,
            activated_at=datetime.utcnow(),
        )

        self.db.add(new_user)

        # Atualizar empresa para status ativo
        company.access_status = "active"
        company.activated_at = datetime.utcnow()
        company.activated_by_user_id = None  # Será atualizado após commit

        # Limpar token usado
        if company.metadata_:
            company.metadata_.pop("user_creation_token", None)
            company.metadata_.pop("user_creation_token_expires_at", None)
            flag_modified(company, "metadata_")

        await self.db.commit()
        await self.db.refresh(new_user)
        await self.db.refresh(company)

        # Atualizar com ID do usuário
        company.activated_by_user_id = new_user.id
        await self.db.commit()

        return {
            "user_id": new_user.id,
            "email": new_user.email_address,
            "company_id": company.id,
            "access_status": company.access_status,
        }

    async def get_company_activation_status(
        self, company_id: int
    ) -> CompanyActivationStatus:
        """
        Retorna status detalhado de ativação da empresa

        Args:
            company_id: ID da empresa

        Returns:
            CompanyActivationStatus com informações detalhadas
        """
        # Buscar empresa
        company_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == company_id)
        )
        result = await self.db.execute(company_query)
        company = result.scalar_one_or_none()

        if not company:
            raise ValueError(f"Empresa {company_id} não encontrada")

        # Verificar se tem usuário ativo
        user_query = select(User).where(
            and_(
                User.company_id == company_id,
                User.context_type == "company",
                User.status == "active",
            )
        )
        user_result = await self.db.execute(user_query)
        has_active_user = user_result.scalar_one_or_none() is not None

        # Calcular métricas
        days_since_creation = (
            (datetime.utcnow() - company.created_at).days
            if company.created_at
            else None
        )
        days_since_contract_sent = (
            (datetime.utcnow() - company.activation_sent_at).days
            if company.activation_sent_at
            else None
        )

        is_overdue = False
        if days_since_contract_sent is not None and days_since_contract_sent > 7:
            is_overdue = True

        return CompanyActivationStatus(
            company_id=company.id,
            company_name=company.people.name,
            access_status=company.access_status,
            contract_sent=company.activation_sent_at is not None,
            contract_sent_at=company.activation_sent_at,
            contract_sent_to=company.activation_sent_to,
            contract_accepted=company.contract_accepted_at is not None,
            contract_accepted_at=company.contract_accepted_at,
            contract_accepted_by=company.contract_accepted_by,
            contract_terms_version=company.contract_terms_version,
            has_active_user=has_active_user,
            activated_at=company.activated_at,
            activated_by_user_id=company.activated_by_user_id,
            days_since_creation=days_since_creation,
            days_since_contract_sent=days_since_contract_sent,
            is_overdue=is_overdue,
        )

    async def resend_contract_email(self, company_id: int) -> SendEmailResponse:
        """
        Reenvia email de aceite de contrato

        Args:
            company_id: ID da empresa

        Returns:
            SendEmailResponse

        Raises:
            ValueError: Se empresa em status inválido
        """
        company_query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.id == company_id)
        )
        result = await self.db.execute(company_query)
        company = result.scalar_one_or_none()

        if not company:
            raise ValueError(f"Empresa {company_id} não encontrada")

        if company.access_status == "active":
            raise ValueError("Empresa já está ativa")

        if company.access_status == "contract_signed":
            raise ValueError("Contrato já foi aceito. Empresa aguardando criação de usuário.")

        # Usar email anterior ou solicitar novo
        if not company.activation_sent_to:
            raise ValueError("Nenhum email de ativação foi enviado anteriormente. Use o endpoint de envio inicial.")

        # Reenviar para o mesmo email
        return await self.send_contract_email(
            company_id=company_id,
            recipient_email=company.activation_sent_to,
            recipient_name="Gestor",  # Nome genérico no reenvio
        )
