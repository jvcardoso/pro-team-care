from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.domain.entities.user import User
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User as UserORM
from app.infrastructure.services.security_service import (
    SecurityService,
    get_security_service,
)
from app.infrastructure.services.tenant_context_service import get_tenant_context
from config.settings import settings

logger = structlog.get_logger()


@dataclass
class TokenData:
    """Token data para infrastructure"""

    email: str


# Configurar bcrypt com tratamento de erro mais robusto
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    bcrypt_available = True
except Exception as e:
    logger.warning(f"Bcrypt initialization failed: {e}. Using fallback.")
    pwd_context = None
    bcrypt_available = False
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version using bcrypt or simple hash."""
    if pwd_context and bcrypt_available:
        try:
            # Tentar bcrypt primeiro
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Bcrypt verification failed: {e}")

    # Fallback para hash simples (SHA256) - para desenvolvimento
    import hashlib

    simple_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return simple_hash == hashed_password


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for the given password."""
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass

    # Fallback para hash simples (SHA256) - para desenvolvimento
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with the given data and expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db=Depends(get_db),
    security_service: SecurityService = Depends(get_security_service),
) -> User:
    """
    Get current authenticated user with enhanced security validation
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Set system tenant context for authentication (allows access to all users)
    tenant_service = get_tenant_context()
    await tenant_service.set_database_context(db, 0)

    try:
        # Decode JWT token
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id")

        if email is None or not isinstance(email, str):
            raise credentials_exception

        token_data = TokenData(email=email)

    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise credentials_exception

    try:
        # Query user using new ORM model
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query = (
            select(UserORM)
            .options(selectinload(UserORM.user_roles))
            .where(UserORM.email_address == token_data.email)
        )

        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning("user_not_found", email=token_data.email)
            raise credentials_exception

        # Additional security validations using SecurityService
        if user_id and user.id != user_id:
            logger.warning(
                "user_id_mismatch", token_user_id=user_id, db_user_id=user.id
            )
            raise credentials_exception

        # Validate session context if token contains session info
        session_token = payload.get("session_token")
        if session_token:
            session_context = await security_service.validate_session_context(
                session_token=session_token, user_id=user.id
            )

            if not session_context.is_valid:
                logger.warning("invalid_session_context", user_id=user.id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid",
                )

        # Update last login timestamp
        if (
            user.last_login_at is None
            or (datetime.utcnow() - user.last_login_at).total_seconds() > 3600
        ):  # Update every hour
            user.last_login_at = datetime.utcnow()
            await db.commit()

        # Convert ORM user to domain user
        # Access attributes directly - SQLAlchemy should provide actual values after loading
        domain_user = User(
            id=getattr(user, "id", 0),
            person_id=getattr(user, "person_id", 0),
            company_id=getattr(user, "company_id", 0),
            email_address=getattr(user, "email_address", ""),
            password=getattr(user, "password", ""),
            is_active=getattr(user, "is_active", True),
            is_system_admin=getattr(user, "is_system_admin", False),
            created_at=getattr(user, "created_at", datetime.utcnow()),
            updated_at=getattr(user, "updated_at", datetime.utcnow()),
            email_verified_at=getattr(user, "email_verified_at", None),
            remember_token=getattr(user, "remember_token", None),
            preferences=getattr(user, "preferences", None),
            notification_settings=getattr(user, "notification_settings", None),
            two_factor_secret=getattr(user, "two_factor_secret", None),
            two_factor_recovery_codes=getattr(user, "two_factor_recovery_codes", None),
            last_login_at=getattr(user, "last_login_at", None),
            password_changed_at=getattr(user, "password_changed_at", None),
            deleted_at=getattr(user, "deleted_at", None),
        )

        logger.debug(
            "user_authenticated",
            user_id=domain_user.id,
            email=domain_user.email_address,
        )
        return domain_user

    except Exception as e:
        logger.error("get_current_user_failed", email=token_data.email, error=str(e))
        raise credentials_exception


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user=Depends(get_current_user)):
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_current_user_skip_options(
    request: Request,
    db=Depends(get_db),
    security_service: SecurityService = Depends(get_security_service),
) -> Optional[User]:
    """
    Versão modificada de get_current_user que ignora requisições OPTIONS
    para resolver problemas de CORS preflight
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return None

    # Para outros métodos, obter token do header Authorization
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]  # Remove 'Bearer '

    if not token or token.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user(token, db, security_service)
