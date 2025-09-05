from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.auth import get_current_user
from app.presentation.schemas.user_legacy import User as CurrentUserSchema
from app.presentation.schemas.user import (
    UserCreate, UserUpdate, UserDetailed, UserList, 
    UserCreateResponse, UserListResponse, UserCountResponse,
    UserPasswordChange, UserProfile
)

router = APIRouter()
logger = get_logger()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency to get user repository"""
    return UserRepository(db)


@router.post(
    "/", 
    response_model=UserCreateResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Criar Usuário",
    description="""
    Cria um novo usuário com todos os dados relacionados (pessoa física, contatos, etc.).
    
    **Validações automáticas:**
    - Email deve ser único no sistema
    - CPF deve ser válido e único
    - Senha deve ser forte (8+ caracteres, maiúscula, minúscula, número)
    - Telefone deve seguir padrão brasileiro (DDD + número)
    - CEP será enriquecido automaticamente com dados da ViaCEP
    
    **Campos obrigatórios:**
    - person.name: Nome completo do usuário
    - person.tax_id: CPF do usuário (apenas números)
    - email_address: Email único no sistema
    - password: Senha forte
    
    **Recursos inclusos:**
    - Hash automático da senha com bcrypt
    - Pessoa física criada automaticamente
    - Contatos opcionais (telefones, emails, endereços)
    - Preferências e configurações de notificação
    """,
    tags=["Users"],
    responses={
        201: {
            "description": "Usuário criado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "person_id": 1,
                            "email_address": "joao.silva@email.com",
                            "is_active": True,
                            "is_system_admin": False,
                            "person": {
                                "name": "João Silva",
                                "tax_id": "12345678901",
                                "person_type": "PF"
                            }
                        },
                        "message": "Usuário criado com sucesso"
                    }
                }
            }
        },
        400: {
            "description": "Dados inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Email já está em uso"}
                }
            }
        },
        422: {"description": "Erro de validação"}
    }
)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Criar novo usuário (apenas admins)"""
    try:
        # Verificar se o usuário atual é admin
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem criar usuários"
            )
        
        created_user = await user_repo.create(user_data)
        
        logger.info(
            "User created via API", 
            user_id=created_user.id, 
            email=created_user.email_address,
            created_by=current_user.id
        )
        
        return UserCreateResponse(
            user=created_user,
            message="Usuário criado com sucesso"
        )
        
    except ValueError as e:
        logger.warning("User creation failed - validation", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("User creation failed - internal error", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Listar Usuários",
    description="""
    Lista usuários com paginação e filtros avançados.
    
    **Filtros disponíveis:**
    - **search**: Busca por nome ou email (parcial, case-insensitive)
    - **is_active**: true/false para usuários ativos/inativos
    - **is_admin**: true/false para administradores/usuários normais
    
    **Paginação:**
    - **page**: Página atual (começando em 1)
    - **size**: Itens por página (máximo 100)
    
    **Resposta otimizada:**
    - Dados essenciais para listagem
    - Contadores de telefones e roles
    - Ordenação por data de criação (mais recentes primeiro)
    - Performance otimizada com JOINs
    """,
    tags=["Users"]
)
async def list_users(
    page: int = Query(1, ge=1, description="Página (começando em 1)"),
    size: int = Query(20, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    is_admin: Optional[bool] = Query(None, description="Filtrar por admin"),
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Listar usuários com filtros e paginação"""
    try:
        # Verificar permissões
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem listar usuários"
            )
        
        # Calcular offset
        skip = (page - 1) * size
        
        # Buscar usuários
        users, total = await user_repo.list(
            skip=skip,
            limit=size,
            search=search,
            is_active=is_active,
            is_admin=is_admin
        )
        
        # Calcular páginas
        pages = (total + size - 1) // size
        
        logger.info(
            "Users listed via API",
            total=total,
            page=page,
            size=size,
            requested_by=current_user.id
        )
        
        return UserListResponse(
            users=users,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing users", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get(
    "/count",
    response_model=UserCountResponse,
    summary="Contar Usuários",
    description="""
    Retorna contagem de usuários por status.
    
    **Contadores:**
    - **total**: Total de usuários ativos no sistema
    - **active**: Usuários com status ativo
    - **inactive**: Usuários com status inativo
    
    Útil para dashboards e estatísticas gerais.
    """,
    tags=["Users"]
)
async def count_users(
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Contar usuários por status"""
    try:
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem ver estatísticas"
            )
        
        counts = await user_repo.count()
        
        return UserCountResponse(**counts)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error counting users", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get(
    "/{user_id}",
    response_model=UserDetailed,
    summary="Buscar Usuário",
    description="""
    Busca um usuário específico por ID com todos os detalhes.
    
    **Dados inclusos:**
    - Informações básicas do usuário
    - Dados da pessoa física associada
    - Telefones, emails e endereços
    - Roles e permissões
    - Preferências e configurações
    
    **Segurança:**
    - Campos sensíveis (senha, tokens) não são retornados
    - Apenas administradores podem ver todos os usuários
    - Usuários normais só podem ver o próprio perfil
    """,
    tags=["Users"]
)
async def get_user(
    user_id: int,
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Buscar usuário por ID"""
    try:
        # Verificar permissões: admin pode ver todos, usuário normal só o próprio
        if not current_user.is_system_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode visualizar seu próprio perfil"
            )
        
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        logger.info(
            "User retrieved via API",
            user_id=user_id,
            requested_by=current_user.id
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.put(
    "/{user_id}",
    response_model=UserDetailed,
    summary="Atualizar Usuário",
    description="""
    Atualiza dados de um usuário existente.
    
    **Campos atualizáveis:**
    - Dados pessoais (nome, CPF, data nascimento)
    - Email (deve continuar único)
    - Status ativo/inativo
    - Contatos (telefones, emails, endereços)
    - Preferências e configurações
    
    **Validações:**
    - Email único se alterado
    - CPF válido se alterado
    - Apenas dados fornecidos são atualizados (PATCH behavior)
    
    **Permissões:**
    - Admins podem atualizar qualquer usuário
    - Usuários normais só podem atualizar o próprio perfil
    """,
    tags=["Users"]
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Atualizar usuário"""
    try:
        # Verificar permissões
        if not current_user.is_system_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode atualizar seu próprio perfil"
            )
        
        updated_user = await user_repo.update(user_id, user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        logger.info(
            "User updated via API",
            user_id=user_id,
            updated_by=current_user.id
        )
        
        return updated_user
        
    except ValueError as e:
        logger.warning("User update failed - validation", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Usuário",
    description="""
    Exclui um usuário do sistema (soft delete).
    
    **Comportamento:**
    - Exclusão lógica (soft delete) - dados preservados
    - Usuário fica inativo e não consegue fazer login
    - Dados históricos mantidos para auditoria
    
    **Segurança:**
    - Apenas administradores podem excluir usuários
    - Usuários não podem excluir a si mesmos
    - Operação irreversível via API (requer acesso direto ao banco)
    """,
    tags=["Users"]
)
async def delete_user(
    user_id: int,
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Excluir usuário (soft delete)"""
    try:
        # Apenas admins podem excluir
        if not current_user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem excluir usuários"
            )
        
        # Usuário não pode excluir a si mesmo
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode excluir sua própria conta"
            )
        
        deleted = await user_repo.delete(user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        logger.info(
            "User deleted via API",
            user_id=user_id,
            deleted_by=current_user.id
        )
        
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting user", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.post(
    "/{user_id}/password",
    status_code=status.HTTP_200_OK,
    summary="Alterar Senha",
    description="""
    Altera a senha de um usuário.
    
    **Validações:**
    - Nova senha deve ser forte (8+ caracteres, maiúscula, minúscula, número)
    - Confirmação deve conferir com nova senha
    - Senha atual obrigatória (exceto para admins alterando outros usuários)
    
    **Comportamento:**
    - Senha hasheada automaticamente com bcrypt
    - Timestamp de alteração de senha atualizado
    - Tokens existentes invalidados (por segurança)
    
    **Permissões:**
    - Usuários podem alterar a própria senha (com senha atual)
    - Admins podem alterar senha de qualquer usuário (sem senha atual)
    """,
    tags=["Users"]
)
async def change_password(
    user_id: int,
    password_data: UserPasswordChange,
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Alterar senha do usuário"""
    try:
        # Verificar permissões
        is_self = current_user.id == user_id
        is_admin = current_user.is_system_admin
        
        if not is_self and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode alterar sua própria senha"
            )
        
        # Se usuário alterando própria senha, senha atual é obrigatória
        if is_self and not is_admin:
            if not password_data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Senha atual é obrigatória"
                )
            
            # Verificar senha atual
            user_detail = await user_repo.get_by_id(user_id)
            if not user_detail:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
            
            # Buscar hash da senha atual
            from app.infrastructure.entities.user import UserEntity
            from sqlalchemy import select
            
            db = user_repo.db
            result = await db.execute(select(UserEntity.password).where(UserEntity.id == user_id))
            current_hash = result.scalar_one_or_none()
            
            if not current_hash or not user_repo.verify_password(password_data.current_password, current_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Senha atual incorreta"
                )
        
        # Alterar senha
        success = await user_repo.change_password(user_id, password_data.new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        logger.info(
            "Password changed via API",
            user_id=user_id,
            changed_by=current_user.id,
            is_self=is_self
        )
        
        return {"message": "Senha alterada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error changing password", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")


@router.get(
    "/me/profile",
    response_model=UserProfile,
    summary="Meu Perfil",
    description="""
    Retorna o perfil do usuário logado.
    
    **Dados públicos:**
    - Informações básicas (nome, email)
    - Status de atividade
    - Dados não sensíveis da pessoa
    
    **Uso:** Interface de usuário, dropdown de perfil, etc.
    """,
    tags=["Users"]
)
async def get_my_profile(
    current_user: CurrentUserSchema = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Buscar perfil do usuário atual"""
    try:
        user_detail = await user_repo.get_by_id(current_user.id)
        
        if not user_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        # Converter para UserProfile (dados públicos)
        profile = UserProfile(
            id=user_detail.id,
            name=user_detail.person.name,
            email_address=user_detail.email_address,
            is_active=user_detail.is_active,
            last_login_at=user_detail.last_login_at,
            gender=user_detail.person.gender
        )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")