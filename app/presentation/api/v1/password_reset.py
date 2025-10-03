"""
Endpoints para recuperação de senha

Implementação segura do fluxo de recuperação de senha:
1. POST /forgot-password - Solicita reset de senha
2. POST /validate-reset-token - Valida token de reset
3. POST /reset-password - Redefine senha com token
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.auth import get_password_hash
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User
from app.infrastructure.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["password-reset"])


# ======================
# REQUEST/RESPONSE SCHEMAS
# ======================


class ForgotPasswordRequest(BaseModel):
    """Request para solicitar reset de senha"""

    email: EmailStr


class ValidateResetTokenRequest(BaseModel):
    """Request para validar token de reset"""

    token: str


class ResetPasswordRequest(BaseModel):
    """Request para redefinir senha"""

    token: str
    new_password: str


class GenericResponse(BaseModel):
    """Response genérica"""

    success: bool
    message: str


# ======================
# ENDPOINTS
# ======================


@router.post("/forgot-password", response_model=GenericResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Solicita reset de senha

    **Endpoint público** (não requer autenticação)

    **Segurança**:
    - Sempre retorna sucesso (não revela se email existe)
    - Token válido por 1 hora
    - Rate limiting aplicado (máx 3/hora por IP)

    **Fluxo**:
    1. Usuário digita email
    2. Sistema gera token único
    3. Email enviado com link de reset
    4. Mensagem genérica mostrada ao usuário
    """
    try:
        # Buscar usuário por email (com relacionamento person)
        query = (
            select(User)
            .options(selectinload(User.person))
            .where(User.email_address == request.email)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        # Se usuário existe, enviar email
        if user:
            # Gerar token de reset (válido 1h)
            reset_token = EmailService.generate_token()

            # Salvar token nos campos específicos do modelo
            user.password_reset_token = reset_token
            user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)

            await db.commit()

            # Enviar email
            email_service = EmailService()

            # Buscar nome do usuário via relacionamento com People
            user_name = "Usuário"
            if user.person:
                user_name = user.person.name or "Usuário"

            await email_service.send_password_reset_email(
                email=request.email,
                reset_token=reset_token,
                user_name=user_name,
            )

        # SEMPRE retornar sucesso (não revelar se email existe)
        return GenericResponse(
            success=True,
            message="Se o email existir, você receberá um link para redefinir sua senha.",
        )

    except Exception as e:
        # Log do erro mas retorna mensagem genérica
        print(f"Erro em forgot_password: {str(e)}")
        return GenericResponse(
            success=True,
            message="Se o email existir, você receberá um link para redefinir sua senha.",
        )


@router.post("/validate-reset-token", response_model=GenericResponse)
async def validate_reset_token(
    request: ValidateResetTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Valida token de reset de senha

    **Endpoint público** (não requer autenticação)

    **Validações**:
    - Token existe?
    - Token não expirou? (1h)
    - Usuário ativo?
    """
    try:
        # Buscar usuário pelo token
        query = select(User).where(User.password_reset_token == request.token)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido",
            )

        # Verificar expiração
        if user.password_reset_expires_at:
            if datetime.utcnow() > user.password_reset_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token expirado",
                )

        # Verificar se usuário está ativo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário inativo",
            )

        return GenericResponse(
            success=True,
            message="Token válido",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro em validate_reset_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao validar token",
        )


@router.post("/reset-password", response_model=GenericResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Redefine senha usando token

    **Endpoint público** (não requer autenticação)

    **Fluxo**:
    1. Valida token
    2. Atualiza senha com hash bcrypt
    3. Invalida token usado
    4. Usuário pode fazer login com nova senha

    **Segurança**:
    - Senha hashada com bcrypt
    - Token invalidado após uso
    - Validação de força de senha no frontend
    """
    try:
        # Buscar usuário pelo token
        query = select(User).where(User.password_reset_token == request.token)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido",
            )

        # Verificar expiração
        if user.password_reset_expires_at:
            if datetime.utcnow() > user.password_reset_expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token expirado. Solicite um novo link.",
                )

        # Validar nova senha (mínimo 8 caracteres)
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha deve ter no mínimo 8 caracteres",
            )

        # Atualizar senha
        user.password = get_password_hash(request.new_password)
        user.password_changed_at = datetime.utcnow()

        # Limpar token usado
        user.password_reset_token = None
        user.password_reset_expires_at = None

        await db.commit()

        return GenericResponse(
            success=True,
            message="Senha redefinida com sucesso! Você já pode fazer login.",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro em reset_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao redefinir senha",
        )
