from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from structlog import get_logger

from app.infrastructure.auth import get_current_user
from app.infrastructure.cache.decorators import cache_invalidate, cached
from app.infrastructure.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.orm.models import People, Role, User, UserRole
from app.infrastructure.orm.views import UserCompleteView, UserHierarchicalView
from app.infrastructure.services.security_service import get_security_service
from app.infrastructure.services.tenant_context_service import get_tenant_context
from app.infrastructure.services.validation_service import get_validation_service
from app.presentation.decorators.simple_permissions import (
    require_permission,
    require_system_admin,
    require_users_view,
)
from app.presentation.schemas.role import (
    RoleAssignmentCreate,
    RoleAssignmentResponse,
    RoleResponse,
)
from app.presentation.schemas.user_schemas import (
    UserCompleteResponse,
    UserCreate,
    UserHierarchicalResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()
logger = get_logger()


async def get_current_user_schema(
    token: str = Depends(oauth2_scheme), db=Depends(get_db)
):
    """Get current user with complete data"""
    # Decode JWT token to get user_id
    from jose import JWTError, jwt

    from config.settings import settings

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        result = await db.execute(
            select(UserCompleteView).where(UserCompleteView.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PaginationParams(BaseModel):
    """Parâmetros de paginação padronizados"""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@require_permission("users.create", context_type="company")
async def create_user(
    user_data: UserCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
    validation_service=Depends(get_validation_service),
):
    """Criar novo usuário (apenas system admin)"""
    try:
        # Usar transaction para garantir consistência
        async with db.begin():
            # Validate person exists
            result = await db.execute(
                select(People).where(People.id == user_data.person_id)
            )
            person = result.scalar_one_or_none()
            if not person:
                raise HTTPException(status_code=404, detail="Person not found")

            # Validate email is unique
            result = await db.execute(select(User).where(User.email == user_data.email))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already registered")

            # Generate password hash using security service
            password_hash = await security_service.hash_password(user_data.password)

            # Create user
            user = User(
                email=user_data.email,
                password_hash=password_hash,
                person_id=user_data.person_id,
                is_admin=user_data.is_admin,
                is_active=user_data.is_active,
            )

            db.add(user)
            await db.flush()  # Get user.id without committing

            await logger.ainfo(
                "user_created",
                user_id=user.id,
                email=user.email,
                created_by=current_user.id,
            )

            # Converter para response schema
            from datetime import datetime

            return UserResponse(
                id=user.id,
                email=user.email,
                person_id=user.person_id,
                is_admin=user.is_admin or False,
                is_active=user.is_active or True,
                created_at=user.created_at or datetime.utcnow(),
                updated_at=user.updated_at,
            )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror("user_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/count")
@require_users_view()
# @cached(ttl=60, key_prefix="users_count")  # Cache DESABILITADO para dados dinâmicos
async def get_users_count(
    _cache_bust: Optional[str] = Query(
        None, description="Parâmetro para quebrar cache"
    ),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Obter estatísticas de usuários com filtros multi-tenant"""
    try:
        # Set tenant context for system admin vs regular users
        tenant_service = get_tenant_context()
        company_id_for_context = (
            None if current_user.is_system_admin else current_user.company_id
        )
        await tenant_service.set_database_context(db, company_id_for_context)

        # 🔧 CORREÇÃO: Query unificada com filtro multi-tenant aplicado diretamente
        # Usar a mesma abordagem do endpoint de listagem
        query_conditions = [
            User.deleted_at.is_(None),
            User.person_id.isnot(None),  # Apenas usuários com person válido
        ]

        # 🔐 FILTRO MULTI-TENANT: ROOT vê tudo, usuário normal vê só da sua empresa
        if not current_user.is_system_admin:
            query_conditions.append(User.company_id == current_user.company_id)
            await logger.ainfo(
                "🔒 Contagem filtrada por empresa",
                user_email=current_user.email_address,
                company_id=current_user.company_id,
            )
        else:
            await logger.ainfo(
                "🔓 Contagem global (ROOT)", user_email=current_user.email_address
            )

        # Query de estatísticas com filtros aplicados diretamente
        stats_query = (
            select(
                func.count().label("total"),
                func.count().filter(User.is_active == True).label("ativos"),
                func.count().filter(User.is_active == False).label("inativos"),
                func.count().filter(User.is_system_admin == True).label("admins"),
            )
            .select_from(
                User.__table__.join(People.__table__, User.person_id == People.id)
            )
            .where(and_(*query_conditions))
        )

        result = await db.execute(stats_query)
        stats = result.fetchone()

        # 🔧 DEBUG: Log para verificar qual empresa está sendo filtrada
        await logger.ainfo(
            "🔢 Estatísticas calculadas",
            user_email=current_user.email_address,
            is_system_admin=current_user.is_system_admin,
            company_id=(
                current_user.company_id if not current_user.is_system_admin else "ALL"
            ),
            total=stats.total,
            ativos=stats.ativos,
        )

        return {
            "total": stats.total,
            "ativos": stats.ativos,
            "inativos": stats.inativos,
            "admins": stats.admins,
        }
    except Exception as e:
        await logger.aerror("users_count_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/", response_model=UserListResponse)
@require_users_view()
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),  # Renomeado de per_page para size
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Listar usuários com filtros e paginação usando views otimizadas"""
    try:
        # Set tenant context for system admin vs regular users
        tenant_service = get_tenant_context()
        company_id_for_context = (
            None if current_user.is_system_admin else current_user.company_id
        )
        await tenant_service.set_database_context(db, company_id_for_context)
        # 🔧 USAR QUERY DIRETA EM VEZ DA VIEW (que pode ter problemas)
        # Construir query base com joins diretos para evitar problemas com a view
        query = (
            select(User)
            .options(selectinload(User.person))
            .join(People, User.person_id == People.id)
            .where(User.deleted_at.is_(None))
        )

        # 🔐 FILTRO MULTI-TENANT: ROOT vê tudo, usuário normal vê só da sua empresa
        if not current_user.is_system_admin:
            # Usuário normal: forçar filtro pela empresa dele
            query = query.where(User.company_id == current_user.company_id)
            logger.info(
                f"🔒 Usuário {current_user.email_address} - filtrando por empresa {current_user.company_id}"
            )
        else:
            # ROOT: ver todos os usuários do sistema
            logger.info(
                f"🔓 ROOT {current_user.email_address} - sem filtro obrigatório"
            )

        # Aplicar filtros
        conditions = []
        if search:
            search_term = f"%{search.lower()}%"
            conditions.append(
                or_(
                    func.lower(People.name).contains(search_term),
                    func.lower(User.email_address).contains(search_term),
                )
            )

        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if is_admin is not None:
            conditions.append(User.is_system_admin == is_admin)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total before pagination
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # Apply pagination and ordering
        offset = (page - 1) * size
        query = (
            query.offset(offset)
            .limit(size)
            .order_by(People.name, User.created_at.desc())
        )

        # Execute query
        result = await db.execute(query)
        users_entities = result.scalars().all()

        # Convert to response schema usando entities diretas
        users = []
        for user_entity in users_entities:
            users.append(
                UserCompleteResponse(
                    user_id=user_entity.id,
                    user_email=user_entity.email_address,
                    user_is_system_admin=user_entity.is_system_admin,
                    user_is_active=user_entity.is_active,
                    user_company_id=user_entity.company_id,
                    user_created_at=user_entity.created_at,
                    user_updated_at=user_entity.updated_at,
                    person_id=user_entity.person.id if user_entity.person else None,
                    person_name=user_entity.person.name if user_entity.person else None,
                    person_tax_id=(
                        user_entity.person.tax_id if user_entity.person else None
                    ),
                    person_is_active=(
                        user_entity.person.is_active if user_entity.person else None
                    ),
                    person_created_at=(
                        user_entity.person.created_at if user_entity.person else None
                    ),
                    person_updated_at=(
                        user_entity.person.updated_at if user_entity.person else None
                    ),
                )
            )

        return UserListResponse(
            items=users,
            total=total,
            page=page,
            per_page=size,  # Manter per_page na response para compatibilidade
            pages=((total - 1) // size + 1) if total > 0 else 0,
            has_prev=page > 1,
            has_next=page < ((total - 1) // size + 1) if total > 0 else False,
        )

    except Exception as e:
        await logger.aerror("user_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/hierarchical", response_model=List[UserHierarchicalResponse])
@require_users_view()
async def list_users_hierarchical(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Listar usuários em estrutura hierárquica para admins"""
    try:
        # Set tenant context for system admin vs regular users
        tenant_service = get_tenant_context()
        company_id_for_context = (
            None if current_user.is_system_admin else current_user.company_id
        )
        await tenant_service.set_database_context(db, company_id_for_context)
        # Query para buscar dados hierárquicos otimizados com filtro multi-tenant
        query = select(UserHierarchicalView)

        # 🔐 FILTRO MULTI-TENANT: ROOT vê tudo, usuário normal vê só da sua empresa
        if not current_user.is_system_admin:
            # Usuário normal: forçar filtro pela empresa dele
            query = query.where(
                UserHierarchicalView.company_id == current_user.company_id
            )
            logger.info(
                f"🔒 Usuário {current_user.email_address} - filtrando usuários hierárquicos por empresa {current_user.company_id}"
            )
        else:
            # ROOT: ver todos os usuários do sistema
            logger.info(
                f"🔓 ROOT {current_user.email_address} - visualizando todos os usuários hierárquicos"
            )

        result = await db.execute(query)
        users_data = result.scalars().all()

        # Convert to response schema
        users = []
        for user_data in users_data:
            users.append(
                UserHierarchicalResponse(
                    user_id=user_data.user_id,
                    user_email=user_data.user_email,
                    user_is_system_admin=user_data.user_is_system_admin,
                    user_is_active=user_data.user_is_active,
                    person_name=user_data.person_name,
                    person_tax_id=user_data.person_tax_id,
                    establishment_name=user_data.establishment_name,
                    establishment_type=user_data.establishment_type,
                    role_name=user_data.role_name,
                    permissions_count=user_data.permissions_count,
                )
            )

        return users

    except Exception as e:
        await logger.aerror("users_hierarchical_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/{user_id}", response_model=UserCompleteResponse)
@require_users_view()
async def get_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Obter detalhes completos de um usuário específico"""
    try:
        # Set tenant context for system admin vs regular users
        tenant_service = get_tenant_context()
        company_id_for_context = (
            None if current_user.is_system_admin else current_user.company_id
        )
        await tenant_service.set_database_context(db, company_id_for_context)
        # Buscar usuário usando view otimizada - pegando apenas a primeira linha para evitar erro de múltiplas linhas
        result = await db.execute(
            select(UserCompleteView).where(UserCompleteView.user_id == user_id)
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Acessar dados da primeira (e única) linha do resultado
        user_data = user_row[0]

        return UserCompleteResponse(
            user_id=user_data.user_id,
            user_email=user_data.user_email,
            user_is_system_admin=user_data.user_is_system_admin,
            user_is_active=user_data.user_is_active,
            user_created_at=user_data.user_created_at,
            user_updated_at=user_data.user_updated_at,
            person_id=user_data.person_id,
            person_name=user_data.person_name,
            person_tax_id=user_data.person_tax_id,
            person_is_active=user_data.person_is_active,
            person_created_at=user_data.person_created_at,
            person_updated_at=user_data.person_updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("get_user_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/{user_id}/roles", response_model=List[int])
async def get_user_roles(
    user_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Obter roles/perfis atribuídos a um usuário específico"""
    try:
        # Verificar se o usuário existe
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Buscar roles do usuário
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.status == "active"
            )
        )
        user_roles = result.scalars().all()

        # Retornar apenas os role_ids para simplificar
        roles_response = [user_role.role_id for user_role in user_roles]

        return roles_response

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("get_user_roles_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put("/{user_id}/roles")
async def update_user_roles(
    user_id: int,
    role_data: dict,  # Aceitar { role_ids: [...] }
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Atualizar roles/perfis de um usuário"""
    try:
        # Extrair role_ids do body
        role_ids = role_data.get("role_ids", [])

        await logger.ainfo(
            "update_user_roles_called",
            user_id=user_id,
            role_ids=role_ids,
            current_user_id=current_user.id,
        )

        # Verificar se o usuário existe
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se os roles existem (simplificado)
        if role_ids:
            for role_id in role_ids:
                result = await db.execute(select(Role).where(Role.id == role_id))
                role = result.scalar_one_or_none()
                if not role:
                    raise HTTPException(
                        status_code=400, detail=f"Role {role_id} não existe"
                    )

        # Remover todos os roles atuais do usuário
        await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))

        # Adicionar os novos roles
        if role_ids:
            for role_id in role_ids:
                # Usar company como contexto padrão
                context_type = "company"
                context_id = user.company_id

                # Validar que company_id existe
                if not context_id:
                    await logger.aerror(
                        "user_missing_company_id",
                        user_id=user_id,
                        role_id=role_id,
                    )
                    raise HTTPException(
                        status_code=400, detail="Usuário não possui empresa associada"
                    )

                user_role = UserRole(
                    user_id=user_id,  # type: ignore
                    role_id=role_id,  # type: ignore
                    context_type=context_type,  # type: ignore
                    context_id=context_id,  # type: ignore
                    status="active",  # type: ignore
                    assigned_by_user_id=current_user.id,  # type: ignore
                )
                db.add(user_role)

        # Commit the changes
        await db.commit()

        await logger.ainfo(
            "user_roles_updated",
            user_id=user_id,
            role_ids=role_ids,
            updated_by=current_user.id,
        )

        return {
            "message": "Roles do usuário atualizados com sucesso",
            "role_ids": role_ids,
        }

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("update_user_roles_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/{user_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_user_role(
    user_id: int,
    role_assignment: RoleAssignmentCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Atribuir um role específico a um usuário"""
    try:
        # Verificar se o usuário existe
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se o role existe
        result = await db.execute(
            select(Role).where(Role.id == role_assignment.role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role não encontrado")

        # Verificar se o role já está atribuído
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_assignment.role_id,
                UserRole.context_type == role_assignment.context_type,
                UserRole.context_id == role_assignment.context_id,
            )
        )
        existing_assignment = result.scalar_one_or_none()
        if existing_assignment:
            raise HTTPException(status_code=400, detail="Role já atribuído ao usuário")

        # Criar nova atribuição
        user_role = UserRole(
            user_id=user_id,  # type: ignore
            role_id=role_assignment.role_id,  # type: ignore
            context_type=role_assignment.context_type,  # type: ignore
            context_id=role_assignment.context_id,  # type: ignore
            status="active",  # type: ignore
            assigned_by_user_id=current_user.id,  # type: ignore
            expires_at=role_assignment.expires_at,  # type: ignore
        )

        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)

        await logger.ainfo(
            "user_role_assigned",
            user_id=user_id,
            role_id=role_assignment.role_id,
            assigned_by=current_user.id,
        )

        return {
            "message": "Role atribuído com sucesso",
            "assignment": {
                "id": user_role.id,
                "user_id": user_role.user_id,
                "role_id": user_role.role_id,
                "context_type": user_role.context_type,
                "context_id": user_role.context_id,
                "status": user_role.status,
                "assigned_at": user_role.assigned_at,
            },
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror("assign_user_role_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete("/{user_id}/roles/{role_id}")
async def remove_user_role(
    user_id: int,
    role_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Remover um role específico de um usuário"""
    try:
        # Verificar se o usuário existe
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Verificar se o role existe
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role não encontrado")

        # Encontrar e remover a atribuição
        result = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
            )
        )
        user_role = result.scalar_one_or_none()
        if not user_role:
            raise HTTPException(status_code=404, detail="Role não atribuído ao usuário")

        await db.delete(user_role)
        await db.commit()

        await logger.ainfo(
            "user_role_removed",
            user_id=user_id,
            role_id=role_id,
            removed_by=current_user.id,
        )

        return {"message": "Role removido com sucesso"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror(
            "remove_user_role_failed", user_id=user_id, role_id=role_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put("/{user_id}", response_model=UserResponse)
@require_permission("users.edit", context_type="company")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
    validation_service=Depends(get_validation_service),
):
    """Atualizar usuário existente"""
    try:
        # Find existing user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Validate email uniqueness if changed
        if user_data.email and user_data.email != user.email_address:
            result = await db.execute(
                select(User).where(
                    and_(User.email_address == user_data.email, User.id != user_id)
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email já está em uso")
            user.email_address = user_data.email

        # Update other fields
        if user_data.is_admin is not None:
            user.is_system_admin = user_data.is_admin
        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        # Update password if provided
        if user_data.password:
            user.password = await security_service.hash_password(user_data.password)

        await logger.ainfo(
            "user_updated",
            user_id=user.id,
            email=user.email_address,
            updated_by=current_user.id,
        )

        return UserResponse(
            id=user.id,
            email=user.email_address,
            person_id=user.person_id,
            is_admin=user.is_system_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("user_update_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete("/{user_id}")
@require_permission("users.delete", context_type="company")
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Deletar usuário (soft delete) - apenas system admin"""
    try:
        async with db.begin():
            # Find user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            # Prevent self-deletion
            if user.id == current_user.id:
                raise HTTPException(
                    status_code=400, detail="Não é possível deletar a própria conta"
                )

            # Soft delete - just deactivate
            user.is_active = False
            await db.flush()

            await logger.ainfo(
                "user_deleted",
                user_id=user.id,
                email=user.email,
                deleted_by=current_user.id,
            )

            return {"message": "Usuário desativado com sucesso"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror("user_delete_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.patch("/{user_id}/status")
@require_permission("users.edit", context_type="company")
async def toggle_user_status(
    user_id: int,
    status_data: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Ativar/Inativar usuário - apenas system admin"""
    try:
        async with db.begin():
            # Find user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            # Prevent self-deactivation
            if user.id == current_user.id and not status_data.get("is_active", True):
                raise HTTPException(
                    status_code=400, detail="Não é possível inativar a própria conta"
                )

            # Update status
            is_active = status_data.get("is_active", True)
            user.is_active = is_active
            await db.flush()

            action = "ativado" if is_active else "inativado"
            await logger.ainfo(
                "user_status_changed",
                user_id=user.id,
                email=user.email,
                is_active=is_active,
                changed_by=current_user.id,
            )

            return {"message": f"Usuário {action} com sucesso", "is_active": is_active}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror("user_status_toggle_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.patch("/{user_id}/password")
@require_permission("users.edit", context_type="company")
async def change_user_password(
    user_id: int,
    password_data: dict,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Alterar senha de usuário - apenas system admin"""
    try:
        async with db.begin():
            # Find user
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            # Validate password
            new_password = password_data.get("new_password")
            if not new_password or len(new_password) < 8:
                raise HTTPException(
                    status_code=400,
                    detail="Nova senha deve ter pelo menos 8 caracteres",
                )

            # Hash and update password
            user.password_hash = await security_service.hash_password(new_password)
            await db.flush()

            await logger.ainfo(
                "user_password_changed",
                user_id=user.id,
                email=user.email,
                changed_by=current_user.id,
            )

            return {"message": "Senha alterada com sucesso"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror(
            "user_password_change_failed", user_id=user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ========== PROFILE ENDPOINTS ==========


@router.get("/me/profile", response_model=UserCompleteResponse)
async def get_my_profile(
    db=Depends(get_db), current_user=Depends(get_current_user_schema)
):
    """Obter perfil do usuário logado"""
    return current_user


@router.get("/me/permissions")
async def get_my_permissions(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Obter permissões do usuário logado"""
    try:
        permissions = await security_service.get_user_permissions(db, current_user.id)
        return {"permissions": permissions}

    except Exception as e:
        await logger.aerror(
            "get_permissions_failed", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put("/me/profile")
async def update_my_profile(
    profile_data: UserUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    security_service=Depends(get_security_service),
):
    """Atualizar perfil do usuário logado"""
    user = current_user
    try:
        async with db.begin():
            # Only allow email and password updates for self

            # Update email if provided and different
            if profile_data.email and profile_data.email != user.email:
                # Check uniqueness
                result = await db.execute(
                    select(User).where(
                        and_(User.email == profile_data.email, User.id != user.id)
                    )
                )
                if result.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Email já está em uso")
                user.email = profile_data.email

            # Update password if provided
            if profile_data.password:
                user.password_hash = await security_service.hash_password(
                    profile_data.password
                )

            await db.flush()

            await logger.ainfo("profile_updated", user_id=user.id, email=user.email)

            return {"message": "Perfil atualizado com sucesso"}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror(
            "profile_update_failed", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
