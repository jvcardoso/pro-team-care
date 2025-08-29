from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.domain.models.user import Token, User, UserCreate
from app.infrastructure.auth import (
    create_access_token,
    get_current_active_user,
    get_current_user,
)
from app.infrastructure.database import get_db
from app.infrastructure.rate_limiting import limiter

router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.user_repository import UserRepository
    from app.application.use_cases.auth_use_case import AuthUseCase
    
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(user_repository)
    
    user = await auth_use_case.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await auth_use_case.create_access_token_for_user(user)

@router.post("/register", response_model=User)
@limiter.limit("3/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    from app.infrastructure.repositories.user_repository import UserRepository
    from app.application.use_cases.auth_use_case import AuthUseCase
    
    user_repository = UserRepository(db)
    auth_use_case = AuthUseCase(user_repository)
    
    try:
        return await auth_use_case.register_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.email}]