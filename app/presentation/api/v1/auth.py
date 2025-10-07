from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.application.use_cases.auth_use_case import AuthUseCase
from app.infrastructure.auth import create_access_token, oauth2_scheme
from app.infrastructure.database import get_db
from app.infrastructure.rate_limiting import limiter
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.services.auth_service import AuthService
from app.presentation.schemas.user_legacy import Token, UserCreate
from app.presentation.schemas.user_schemas import UserResponse
from config.settings import settings

router = APIRouter()


@router.get("/test", summary="Test endpoint")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return {"message": "API is working", "timestamp": "2025-09-09"}


@router.get("/debug-users", summary="Debug users (DEV ONLY)")
async def debug_users(db=Depends(get_db)):
    """Debug endpoint to check users in database"""
    from sqlalchemy import text

    query = text("""
        SELECT
            u.id,
            u.email_address,
            SUBSTRING(u.password, 1, 30) as password_preview,
            u.is_active,
            p.name as full_name
        FROM master.users u
        LEFT JOIN master.people p ON p.id = u.person_id
        WHERE u.deleted_at IS NULL
        LIMIT 5
    """)

    result = await db.execute(query)
    users = result.fetchall()

    return [
        {
            "id": u.id,
            "email": u.email_address,
            "password_preview": u.password_preview,
            "is_active": u.is_active,
            "full_name": u.full_name
        }
        for u in users
    ]


@router.post("/reset-admin-password", summary="Reset admin password (DEV ONLY)")
async def reset_admin_password(db=Depends(get_db)):
    """Reset admin@proteamcare.com password to 'admin123'"""
    from sqlalchemy import text
    from app.infrastructure.auth import get_password_hash

    email = "admin@proteamcare.com"
    new_password = "admin123"

    # Generate bcrypt hash
    hashed_password = get_password_hash(new_password)

    # Update password
    query = text("""
        UPDATE master.users
        SET password = :password, updated_at = NOW()
        WHERE email_address = :email
        RETURNING id, email_address
    """)

    result = await db.execute(query, {"password": hashed_password, "email": email})
    await db.commit()

    user = result.fetchone()

    if user:
        return {
            "success": True,
            "message": f"Password reset successfully for {email}",
            "user_id": user.id,
            "new_password": new_password
        }
    else:
        raise HTTPException(status_code=404, detail="User not found")


@router.post(
    "/login",
    response_model=Token,
    summary="Fazer Login (Mock Temporário)",
    description="""
    Endpoint de login temporário para desenvolvimento.
    Aceita credenciais mock para compatibilidade com frontend.

    **Credenciais aceitas:**
    - admin@example.com / admin123
    - admin@proteamcare.com / password

    **Nota:** Este é um endpoint temporário. O endpoint real será reabilitado após correções.
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
                        "expires_in": 1800,
                    }
                }
            },
        },
        401: {"description": "Credenciais inválidas"},
    },
)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    """Login with real database authentication"""
    from passlib.context import CryptContext
    from sqlalchemy import text

    # Query user with password
    query = text(
        """
        SELECT
            u.id,
            u.email_address,
            u.password,
            u.is_active,
            p.name as full_name
        FROM master.users u
        LEFT JOIN master.people p ON p.id = u.person_id
        WHERE u.email_address = :email AND u.deleted_at IS NULL
    """
    )

    result = await db.execute(query, {"email": form_data.username})
    user_row = result.fetchone()

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_row.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password using the same method as auth infrastructure (with fallback)
    from app.infrastructure.auth import verify_password

    if not verify_password(form_data.password, user_row.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_row.email_address, "user_id": user_row.id},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post(
    "/register",
    response_model=UserResponse,
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
                        "created_at": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        400: {
            "description": "Email já existe ou dados inválidos",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
        429: {
            "description": "Rate limit excedido",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded: 3 per 1 minute"}
                }
            },
        },
        422: {"description": "Erro de validação dos dados"},
    },
)
@limiter.limit("3/minute")
async def register_user(request: Request, user_data: UserCreate, db=Depends(get_db)):
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
            "is_superuser": user_data.is_system_admin,
        }
        user_entity = await auth_use_case.register_user(user_dict)
        # Convert to UserResponse
        return UserResponse.model_validate(user_entity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha no registro. Verifique os dados fornecidos.",
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Access Token",
    description="""
    Refresh an expired or about-to-expire access token.

    **Requirements:**
    - Valid refresh token in Authorization header
    - User must still exist and be active

    **Returns:**
    - New access token
    - Token type (bearer)
    - Expiration time in seconds
    """,
    tags=["Authentication"],
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800,
                    }
                }
            },
        },
        401: {"description": "Invalid or expired refresh token"},
        403: {"description": "User is inactive"},
    },
)
async def refresh_access_token(
    request: Request,
    db=Depends(get_db),
):
    """Refresh access token using current valid token"""
    from jose import JWTError, jwt
    from sqlalchemy import text

    # Get token from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]  # Remove 'Bearer '

    # Decode token (allow expired tokens for refresh)
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},
        )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Query user
    query = text(
        """
        SELECT
            u.id,
            u.email_address,
            u.is_active,
            u.is_system_admin
        FROM master.users u
        WHERE u.email_address = :email AND u.deleted_at IS NULL
    """
    )

    result = await db.execute(query, {"email": email})
    user_row = result.fetchone()

    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_row.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_row.email_address}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.get("/me", response_model=None)
async def read_users_me(
    token: str = Depends(oauth2_scheme), db=Depends(get_db)
) -> dict:
    """Get current user profile with database connection"""
    import structlog
    from jose import JWTError, jwt
    from sqlalchemy import text

    logger = structlog.get_logger()

    # Decode token
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id")

        logger.info("Token decoded", email=email, user_id=user_id)

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        logger.error("JWT decode error", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

    # Query user with JOIN to people table and related company/establishment data
    query = text(
        """
        SELECT
            u.id,
            u.email_address,
            u.is_active,
            u.is_system_admin,
            u.created_at,
            u.updated_at,
            u.company_id,
            u.establishment_id,
            u.context_type,
            p.name as full_name,
            cp.name as company_name,
            ep.name as establishment_name
        FROM master.users u
        LEFT JOIN master.people p ON p.id = u.person_id AND p.deleted_at IS NULL
        LEFT JOIN master.companies c ON c.id = u.company_id AND c.deleted_at IS NULL
        LEFT JOIN master.people cp ON cp.id = c.person_id AND cp.deleted_at IS NULL
        LEFT JOIN master.establishments e ON e.id = u.establishment_id AND e.deleted_at IS NULL
        LEFT JOIN master.people ep ON ep.id = e.person_id AND ep.deleted_at IS NULL
        WHERE u.email_address = :email AND u.deleted_at IS NULL
    """
    )

    result = await db.execute(query, {"email": email})
    user_row = result.fetchone()

    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if not user_row.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    # Query related establishments if user has a company
    establishments = []
    if user_row.company_id:
        establishments_query = text(
            """
            SELECT e.id, p.name as name
            FROM master.establishments e
            JOIN master.people p ON p.id = e.person_id
            WHERE e.company_id = :company_id AND e.deleted_at IS NULL AND p.deleted_at IS NULL
            ORDER BY p.name
            """
        )
        establishments_result = await db.execute(
            establishments_query, {"company_id": user_row.company_id}
        )
        establishments = [
            {"id": row.id, "name": row.name} for row in establishments_result.fetchall()
        ]

    return {
        "id": user_row.id,
        "email_address": user_row.email_address,
        "full_name": user_row.full_name,
        "is_active": user_row.is_active,
        "is_system_admin": user_row.is_system_admin,
        "created_at": user_row.created_at.isoformat() if user_row.created_at else None,
        "updated_at": user_row.updated_at.isoformat() if user_row.updated_at else None,
        "company_id": user_row.company_id,
        "establishment_id": user_row.establishment_id,
        "context_type": user_row.context_type,
        "company_name": user_row.company_name,
        "establishment_name": user_row.establishment_name,
        "establishments": establishments,
    }
