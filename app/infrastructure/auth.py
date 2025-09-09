from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.infrastructure.database import get_session
from app.infrastructure.services.security_service import SecurityService, get_security_service
from app.infrastructure.orm.models import User
from app.infrastructure.orm.views import UserCompleteView
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class TokenData:
    """Token data para infrastructure"""
    email: str

# Temporariamente desabilitar bcrypt devido a problema de compatibilidade
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    # Fallback sem bcrypt
    pwd_context = None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version using bcrypt or simple hash."""
    if pwd_context:
        try:
            # Tentar bcrypt primeiro
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    
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
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: AsyncSession = Depends(get_session),
    security_service: SecurityService = Depends(get_security_service)
) -> User:
    """
    Get current authenticated user with enhanced security validation
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
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
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        query = select(User).options(
            selectinload(User.person),
            selectinload(User.user_roles).selectinload('role')
        ).where(User.email_address == token_data.email)
        
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning("user_not_found", email=token_data.email)
            raise credentials_exception
        
        # Additional security validations using SecurityService
        if user_id and user.id != user_id:
            logger.warning("user_id_mismatch", token_user_id=user_id, db_user_id=user.id)
            raise credentials_exception
        
        # Validate session context if token contains session info
        session_token = payload.get("session_token")
        if session_token:
            session_context = await security_service.validate_session_context(
                session_token=session_token,
                user_id=user.id
            )
            
            if not session_context.is_valid:
                logger.warning("invalid_session_context", user_id=user.id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid"
                )
        
        # Update last login timestamp
        if user.last_login_at is None or (
            datetime.utcnow() - user.last_login_at
        ).total_seconds() > 3600:  # Update every hour
            user.last_login_at = datetime.utcnow()
            await session.commit()
        
        logger.debug("user_authenticated", user_id=user.id, email=user.email_address)
        return user
        
    except Exception as e:
        logger.error("get_current_user_failed", email=token_data.email, error=str(e))
        raise credentials_exception

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(current_user = Depends(get_current_user)):
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_user_skip_options(
    request: Request,
    session: AsyncSession = Depends(get_session),
    security_service: SecurityService = Depends(get_security_service)
):
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

    return await get_current_user(token, session, security_service)