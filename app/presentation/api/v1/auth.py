from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.presentation.schemas.user_legacy import Token, User, UserCreate
from app.infrastructure.auth import (
    create_access_token,
    get_current_active_user,
    get_current_user,
)
from app.infrastructure.database import get_db
from app.infrastructure.rate_limiting import limiter
from app.infrastructure.repositories.user_repository import UserRepository
from app.application.use_cases.auth_use_case import AuthUseCase
from app.infrastructure.services.auth_service import AuthService

router = APIRouter()



@router.post(
    "/login", 
    response_model=Token,
    summary="Fazer Login",
    description="""
    Autentica um usuário e retorna um token JWT para acesso às APIs protegidas.
    
    **Funcionalidades:**
    - Autenticação por email + senha
    - Token JWT com expiração configurável (padrão: 30min)
    - Rate limiting: máximo 5 tentativas por minuto
    - Hash de senha seguro com bcrypt
    
    **Segurança:**
    - Senhas são verificadas com hash bcrypt
    - Tokens JWT assinados com chave secreta de 256-bit
    - Rate limiting previne ataques de força bruta
    - Logs de autenticação para auditoria
    """,
    tags=["Authentication"],
    responses={
        200: {
            "description": "Login realizado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Credenciais inválidas",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect email or password"}
                }
            }
        },
        429: {
            "description": "Muitas tentativas - rate limit excedido",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded: 5 per 1 minute"}
                }
            }
        },
        422: {"description": "Dados de entrada inválidos"}
    }
)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Directly use repository and auth functions to avoid circular imports
    from app.infrastructure.auth import verify_password, create_access_token
    
    user_repository = UserRepository(db)
    
    # Get user by email
    user = await user_repository.get_by_email(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email_address}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/register", 
    response_model=User,
    summary="Registrar Usuário",
    description="""
    Registra um novo usuário no sistema.
    
    **Funcionalidades:**
    - Criação de conta com email único
    - Hash seguro da senha com bcrypt
    - Validação de formato de email
    - Usuário ativo por padrão
    
    **Validações:**
    - Email deve ser único no sistema
    - Senha deve ter pelo menos 8 caracteres
    - Nome completo é obrigatório
    
    **Segurança:**
    - Rate limiting: máximo 3 registros por minuto
    - Senhas são hasheadas antes do armazenamento
    - Não retorna senha na resposta
    """,
    tags=["Authentication"],
    responses={
        200: {
            "description": "Usuário registrado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email_address": "novo@exemplo.com",
                        "full_name": "Novo Usuário",
                        "is_active": True,
                        "is_system_admin": False,
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Email já existe ou dados inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        },
        429: {
            "description": "Rate limit excedido",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded: 3 per 1 minute"}
                }
            }
        },
        422: {"description": "Erro de validação dos dados"}
    }
)
@limiter.limit("3/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user_repository = UserRepository(db)
    auth_service = AuthService()
    auth_use_case = AuthUseCase(user_repository, auth_service)

    try:
        # Convert UserCreate to dict
        user_dict = {
            "email": user_data.email_address,
            "password": user_data.password,
            "full_name": user_data.full_name,
            "is_active": user_data.is_active,
            "is_superuser": user_data.is_system_admin
        }
        return await auth_use_case.register_user(user_dict)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha no registro. Verifique os dados fornecidos."
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.email_address}]