"""
Endpoints para ativação de usuários e gestão de convites
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto.user_dto import (
    CompanyManagerInvite,
    EstablishmentManagerInvite,
    ResendActivation,
    UserActivation,
    UserResponse,
)
from app.application.use_cases.user_management_use_case import UserManagementUseCase
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User

router = APIRouter(prefix="/user-activation", tags=["user-activation"])


@router.post("/invite-company-manager", response_model=UserResponse)
async def invite_company_manager(
    invite_data: CompanyManagerInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Convida um gestor para uma empresa

    - Cria usuário com status 'pending'
    - Envia email de ativação
    - Define contexto como 'company'
    """
    try:
        use_case = UserManagementUseCase(db)
        user = await use_case.create_company_manager(
            email=invite_data.email,
            company_id=invite_data.company_id,
            invited_by_user_id=current_user.id,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/invite-establishment-manager", response_model=UserResponse)
async def invite_establishment_manager(
    invite_data: EstablishmentManagerInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Convida um gestor para um estabelecimento

    - Cria usuário com status 'pending'
    - Envia email de ativação
    - Define contexto como 'establishment'
    - Vincula ao estabelecimento específico
    """
    try:
        use_case = UserManagementUseCase(db)
        user = await use_case.create_establishment_manager(
            email=invite_data.email,
            establishment_id=invite_data.establishment_id,
            invited_by_user_id=current_user.id,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/activate", response_model=UserResponse)
async def activate_user(
    activation_data: UserActivation,
    db: AsyncSession = Depends(get_db),
):
    """
    Ativa conta de usuário usando token de ativação

    - Valida token de ativação
    - Define senha do usuário
    - Ativa a conta (status: pending → active)
    - Remove token de ativação
    """
    try:
        use_case = UserManagementUseCase(db)
        user = await use_case.activate_user(
            activation_token=activation_data.activation_token,
            new_password=activation_data.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/resend-activation")
async def resend_activation_email(
    resend_data: ResendActivation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reenvia email de ativação para um usuário

    - Gera novo token de ativação
    - Envia novo email de ativação
    - Apenas usuários com status 'pending' podem receber reenvio
    """
    try:
        use_case = UserManagementUseCase(db)
        success = await use_case.resend_activation_email(resend_data.user_id)

        if success:
            return {"message": "Email de ativação reenviado com sucesso"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao enviar email de ativação",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.get("/validate-token/{token}")
async def validate_activation_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Valida se token de ativação é válido

    - Verifica se token existe
    - Verifica se token não expirou
    - Retorna informações básicas do usuário
    """
    try:
        from sqlalchemy import select

        from app.infrastructure.orm.models import User
        from app.infrastructure.services.email_service import EmailService

        # Buscar usuário pelo token
        user_query = select(User).where(User.activation_token == token)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token de ativação inválido",
            )

        # Verificar se token não expirou
        if not EmailService.is_token_valid(user.activation_expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de ativação expirado",
            )

        # Verificar se usuário já foi ativado
        if user.status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário já foi ativado",
            )

        return {
            "valid": True,
            "email": user.email_address,
            "context_type": user.context_type,
            "expires_at": user.activation_expires_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )
