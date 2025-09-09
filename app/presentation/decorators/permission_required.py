"""
Permission Required Decorators - Integração com SecurityService
"""

from functools import wraps
from typing import Optional, Callable, Any
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.infrastructure.services.security_service import SecurityService, get_security_service
from app.infrastructure.auth import get_current_user
from app.domain.models.user import User

import structlog

logger = structlog.get_logger()


def require_permission(
    permission: str, 
    context_type: str = 'establishment',
    get_context_id: Optional[Callable[[Any], Optional[int]]] = None
):
    """
    Decorator que verifica se usuário possui permissão específica
    
    Args:
        permission: Nome da permissão (ex: "users.view", "companies.create")
        context_type: Tipo de contexto ("system", "company", "establishment")  
        get_context_id: Função para extrair context_id dos argumentos
        
    Usage:
        @require_permission("users.view")
        async def get_users(): pass
        
        @require_permission("establishments.manage", get_context_id=lambda kwargs: kwargs.get("establishment_id"))
        async def update_establishment(establishment_id: int): pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            security_service: SecurityService = Depends(get_security_service),
            **kwargs
        ):
            # Determinar context_id se função fornecida
            context_id = None
            if get_context_id:
                context_id = get_context_id(kwargs)
            
            # Verificar permissão
            has_permission = await security_service.check_user_permission(
                user_id=current_user.id,
                permission=permission,
                context_type=context_type,
                context_id=context_id
            )
            
            if not has_permission:
                await logger.awarning(
                    "permission_denied",
                    user_id=current_user.id,
                    permission=permission,
                    context_type=context_type,
                    context_id=context_id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_permissions",
                        "message": f"Missing permission: {permission}",
                        "required_permission": permission,
                        "context_type": context_type,
                        "context_id": context_id
                    }
                )
            
            # Log acesso autorizado
            await logger.ainfo(
                "permission_granted",
                user_id=current_user.id,
                permission=permission,
                context_type=context_type,
                context_id=context_id,
                endpoint=func.__name__
            )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_system_admin():
    """
    Decorator que requer privilégios de administrador do sistema
    
    Usage:
        @require_system_admin()
        async def manage_system(): pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            **kwargs
        ):
            if not current_user.is_system_admin:
                await logger.awarning(
                    "system_admin_required",
                    user_id=current_user.id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "system_admin_required",
                        "message": "System administrator privileges required"
                    }
                )
            
            await logger.ainfo(
                "system_admin_access",
                user_id=current_user.id,
                endpoint=func.__name__
            )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_data_access(
    get_target_user_id: Callable[[Any], int]
):
    """
    Decorator que verifica acesso hierárquico a dados de usuário
    
    Args:
        get_target_user_id: Função para extrair ID do usuário alvo dos argumentos
        
    Usage:
        @require_data_access(lambda kwargs: kwargs["user_id"])
        async def get_user_details(user_id: int): pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            security_service: SecurityService = Depends(get_security_service),
            **kwargs
        ):
            target_user_id = get_target_user_id(kwargs)
            
            # Verificar se pode acessar dados do usuário
            can_access = await security_service.can_access_user_data(
                requesting_user_id=current_user.id,
                target_user_id=target_user_id
            )
            
            if not can_access:
                await logger.awarning(
                    "user_data_access_denied",
                    requesting_user_id=current_user.id,
                    target_user_id=target_user_id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "access_denied",
                        "message": "Cannot access user data due to hierarchy restrictions",
                        "target_user_id": target_user_id
                    }
                )
            
            # Log acesso a dados (auditoria LGPD)
            await security_service.log_user_data_access(
                accessed_by_user_id=current_user.id,
                accessed_user_id=target_user_id,
                view_name=func.__name__,
                access_type="read"
            )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_active_user():
    """
    Decorator que verifica se usuário está ativo
    
    Usage:
        @require_active_user()
        async def user_action(): pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            **kwargs
        ):
            if not current_user.is_active:
                await logger.awarning(
                    "inactive_user_access_attempt",
                    user_id=current_user.id,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "account_inactive",
                        "message": "User account is inactive"
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


def require_role_level(min_level: int):
    """
    Decorator que verifica nível mínimo de role
    
    Args:
        min_level: Nível mínimo necessário
        
    Usage:
        @require_role_level(5)  # Nível de gerente ou superior
        async def manager_action(): pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            security_service: SecurityService = Depends(get_security_service),
            **kwargs
        ):
            # Buscar perfis disponíveis para verificar nível
            profiles = await security_service.get_available_profiles(
                user_id=current_user.id
            )
            
            max_level = max([p.get("role_level", 0) for p in profiles], default=0)
            
            if max_level < min_level:
                await logger.awarning(
                    "insufficient_role_level",
                    user_id=current_user.id,
                    max_level=max_level,
                    required_level=min_level,
                    endpoint=func.__name__
                )
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "insufficient_role_level",
                        "message": f"Required role level: {min_level}, current: {max_level}",
                        "required_level": min_level,
                        "current_level": max_level
                    }
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator


# Decorators combinados para uso comum
def require_user_management():
    """Decorator combinado para gestão de usuários"""
    return require_permission("users.manage")


def require_establishment_admin():
    """Decorator combinado para admin de estabelecimento"""
    return require_permission("establishments.admin", context_type="establishment")


def require_company_admin():
    """Decorator combinado para admin de empresa"""
    return require_permission("companies.admin", context_type="company")