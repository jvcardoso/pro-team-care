"""
API Endpoints para Sistema de Sessões Seguras e Troca de Perfil
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.infrastructure.database import get_db
from app.infrastructure.auth import get_current_user, get_current_user_skip_options
from app.infrastructure.security.secure_session_manager import SecureSessionManager
from app.domain.entities.user import User

router = APIRouter(prefix="/secure-sessions", tags=["Secure Sessions"])


class ProfileSwitchRequest(BaseModel):
    """Request para troca de perfil"""
    role_id: Optional[int] = None
    context_type: Optional[str] = None  # 'system', 'company', 'establishment'
    context_id: Optional[int] = None
    impersonated_user_id: Optional[int] = None
    reason: Optional[str] = None


@router.get(
    "/available-profiles",
    summary="Obter perfis disponíveis para troca",
    description="""
    Retorna lista de perfis/contextos que o usuário pode assumir.
    
    **Para usuários ROOT:**
    - Todos os perfis do sistema
    - Possibilidade de personificar qualquer usuário
    - Listagem com identificação de personificação
    
    **Para usuários comuns:**
    - Apenas seus próprios perfis
    - Diferentes contextos (empresa/estabelecimento) se aplicável
    
    **Resposta incluí:**
    - role_id, role_name, role_display_name
    - context_type, context_id, context_name  
    - is_impersonation (se é personificação)
    - target_user_id, target_user_email (usuário alvo)
    """,
    responses={
        200: {
            "description": "Lista de perfis disponíveis",
            "content": {
                "application/json": {
                    "example": {
                        "profiles": [
                            {
                                "role_id": 1,
                                "role_name": "super_admin",
                                "role_display_name": "Super Administrador",
                                "context_type": "system",
                                "context_id": None,
                                "context_name": "Sistema Global",
                                "is_impersonation": False,
                                "target_user_id": 5,
                                "target_user_email": "admin@proteamcare.com"
                            },
                            {
                                "role_id": 3,
                                "role_name": "admin_empresa",
                                "role_display_name": "Admin Empresa",
                                "context_type": "company",
                                "context_id": 1,
                                "context_name": "Empresa ABC",
                                "is_impersonation": True,
                                "target_user_id": 2,
                                "target_user_email": "admin@empresa.com"
                            }
                        ],
                        "total_profiles": 2,
                        "user_is_root": True
                    }
                }
            }
        }
    }
)
async def get_available_profiles(
    request: Request,
    current_user: User = Depends(get_current_user_skip_options),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Obter perfis disponíveis para o usuário"""
    
    # Handle OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {}
    
    # current_user pode ser None para requests OPTIONS
    if current_user is None:
        return {}
    
    session_manager = SecureSessionManager(db)
    
    try:
        profiles = await session_manager.get_available_profiles(current_user.id)
        
        return {
            "profiles": profiles,
            "total_profiles": len(profiles),
            "user_is_root": current_user.is_system_admin,
            "current_user_id": current_user.id,
            "current_user_email": current_user.email_address
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter perfis disponíveis: {str(e)}"
        )


@router.post(
    "/switch-profile",
    summary="Trocar perfil/contexto da sessão",
    description="""
    Permite trocar de perfil/contexto durante a sessão ativa.
    
    **Recursos disponíveis:**
    - **Troca de role**: Assumir diferentes papéis
    - **Troca de contexto**: Mudar entre empresas/estabelecimentos
    - **Personificação (ROOT apenas)**: Assumir identidade de outro usuário
    - **Auditoria automática**: Todas as trocas são registradas
    
    **Validações de segurança:**
    - Usuário só pode assumir perfis autorizados
    - ROOT pode personificar qualquer usuário
    - Motivo obrigatório para personificação
    - Registro completo na auditoria
    
    **Exemplos de uso:**
    
    **Admin multi-empresa:**
    ```json
    {
        "context_type": "company",
        "context_id": 2,
        "reason": "Verificar relatórios da filial"
    }
    ```
    
    **ROOT personificando usuário:**
    ```json
    {
        "impersonated_user_id": 123,
        "reason": "Investigar problema reportado pelo usuário"
    }
    ```
    """,
    responses={
        200: {
            "description": "Contexto alterado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Contexto alterado para: Admin Empresa (Empresa ABC)",
                        "new_context": {
                            "role_name": "admin_empresa",
                            "context_type": "company",
                            "context_id": 2,
                            "context_name": "Empresa ABC",
                            "impersonated_user_id": None,
                            "effective_user_email": "admin@proteamcare.com"
                        },
                        "switched_at": "2025-09-06T15:30:00Z"
                    }
                }
            }
        },
        403: {"description": "Não autorizado para esta troca"},
        401: {"description": "Sessão inválida"}
    }
)
async def switch_profile(
    switch_request: ProfileSwitchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Trocar perfil/contexto da sessão atual"""
    
    # Obter token da sessão (simplificado - em produção usar header Authorization)
    session_token = request.headers.get('session-token')
    if not session_token:
        # Fallback: extrair do Authorization header
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]  # Remove 'Bearer '
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sessão não encontrado"
            )
    
    session_manager = SecureSessionManager(db)
    
    try:
        # Obter IP e User-Agent
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')
        
        result = await session_manager.switch_context(
            session_token=session_token,
            new_role_id=switch_request.role_id,
            new_context_type=switch_request.context_type,
            new_context_id=switch_request.context_id,
            impersonated_user_id=switch_request.impersonated_user_id,
            switch_reason=switch_request.reason,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao trocar contexto: {str(e)}"
        )


@router.get(
    "/current-context",
    summary="Obter contexto atual da sessão",
    description="""
    Retorna informações detalhadas sobre o contexto atual da sessão.
    
    **Informações incluídas:**
    - Usuário atual vs usuário personificado
    - Role ativo e suas permissões
    - Contexto ativo (sistema/empresa/estabelecimento)
    - Dados de expiração da sessão
    - Indicador de personificação
    
    **Útil para:**
    - Interface mostrar contexto atual
    - Validar se ainda está personificando
    - Verificar expiração de sessão
    - Mostrar dados do usuário efetivo
    """,
    responses={
        200: {
            "description": "Contexto atual da sessão",
            "content": {
                "application/json": {
                    "example": {
                        "session_valid": True,
                        "user_id": 5,
                        "user_email": "admin@proteamcare.com",
                        "effective_user_id": 123,
                        "effective_user_email": "usuario@empresa.com",
                        "is_impersonating": True,
                        "active_role": {
                            "id": 3,
                            "name": "admin_empresa",
                            "display_name": "Admin Empresa"
                        },
                        "active_context": {
                            "type": "company",
                            "id": 1,
                            "name": "Empresa ABC"
                        },
                        "session_expires_at": "2025-09-06T17:30:00Z"
                    }
                }
            }
        },
        401: {"description": "Sessão inválida ou expirada"}
    }
)
async def get_current_context(
    request: Request,
    current_user: User = Depends(get_current_user_skip_options),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Obter contexto atual da sessão"""
    
    # Handle OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return {}
    
    # current_user pode ser None para requests OPTIONS
    if current_user is None:
        return {}
    
    # Obter token da sessão
    session_token = request.headers.get('session-token')
    if not session_token:
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sessão não encontrado"
            )
    
    session_manager = SecureSessionManager(db)
    
    try:
        session_data = await session_manager.validate_session(session_token)
        
        if not session_data:
            # Retornar resposta indicando que não há sessão ativa, 
            # ao invés de 401 que causa logout
            return {
                "session_valid": False,
                "message": "Nenhuma sessão segura ativa - usando contexto padrão",
                "user_info": {
                    "id": current_user.id if current_user else None,
                    "email": getattr(current_user, 'email_address', None) if current_user else None
                }
            }
        
        return {
            "session_valid": True,
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
            "user_email": session_data['user_email'],
            "effective_user_id": session_data.get('impersonated_user_id') or session_data['user_id'],
            "effective_user_email": session_data.get('impersonated_email') or session_data['user_email'],
            "is_impersonating": bool(session_data.get('impersonated_user_id')),
            "is_root": session_data.get('is_system_admin', False),
            "active_role": {
                "id": session_data.get('active_role_id'),
                "name": session_data.get('role_name'),
                "display_name": session_data.get('role_display_name')
            },
            "active_context": {
                "type": session_data.get('active_context_type'),
                "id": session_data.get('active_context_id')
            },
            "session_expires_at": session_data.get('expires_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter contexto: {str(e)}"
        )


@router.post(
    "/terminate",
    summary="Terminar sessão atual",
    description="""
    Termina a sessão segura atual, incluindo qualquer personificação ativa.
    
    **Efeitos:**
    - Sessão marcada como inativa
    - Personificação encerrada
    - Registro de auditoria criado
    - Token invalidado
    """,
)
async def terminate_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Terminar sessão segura"""
    
    session_token = request.headers.get('session-token')
    if not session_token:
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            session_token = auth_header[7:]
        else:
            return {"success": True, "message": "Nenhuma sessão para terminar"}
    
    session_manager = SecureSessionManager(db)
    
    try:
        terminated = await session_manager.terminate_session(session_token, "User logout")
        
        return {
            "success": terminated,
            "message": "Sessão terminada com sucesso" if terminated else "Sessão não encontrada"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao terminar sessão: {str(e)}"
        )


@router.get(
    "/active-sessions",
    summary="Listar sessões ativas (ROOT apenas)",
    description="""
    Lista todas as sessões ativas no sistema.
    **Acesso restrito a usuários ROOT.**
    
    **Informações incluídas:**
    - Usuário da sessão
    - Usuário personificado (se aplicável)
    - Contexto ativo
    - Última atividade
    - IP e User-Agent
    """,
)
async def list_active_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Listar sessões ativas (ROOT apenas)"""
    
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem ver sessões ativas"
        )
    
    try:
        query = """
        SELECT * FROM master.vw_active_sessions
        ORDER BY last_activity_at DESC
        LIMIT 50
        """
        
        result = await db.execute(query)
        sessions = []
        
        for row in result.fetchall():
            sessions.append(dict(row._mapping))
        
        return {
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar sessões: {str(e)}"
        )