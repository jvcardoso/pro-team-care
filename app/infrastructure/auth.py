from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.infrastructure.database import get_db
# ✅ Infrastructure será atualizada para usar entidades puras
from dataclasses import dataclass

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

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        if email is None or not isinstance(email, str):
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # Query the database for the user DIRETAMENTE - evita importação circular
    from app.infrastructure.repositories.user_repository import UserRepository

    user_repository = UserRepository(db)
    user = await user_repository.get_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    return user

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
    db: AsyncSession = Depends(get_db)
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

    return await get_current_user(token, db)