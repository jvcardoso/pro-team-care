from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user, get_current_user_skip_options
from app.infrastructure.database import get_db
from app.infrastructure.repositories.establishment_repository import (
    EstablishmentRepository,
)
from app.presentation.decorators.simple_permissions import (
    require_establishments_create,
    require_establishments_view,
    require_permission,
)
from app.presentation.schemas.establishment import (
    EstablishmentCreate,
    EstablishmentDetailed,
    EstablishmentListParams,
    EstablishmentListResponse,
    EstablishmentReorderRequest,
    EstablishmentUpdateComplete,
    EstablishmentValidationResponse,
)

logger = structlog.get_logger()

router = APIRouter()


@router.post(
    "/",
    response_model=EstablishmentDetailed,
    status_code=status.HTTP_201_CREATED,
    summary="Criar estabelecimento",
    description="Criar novo estabelecimento vinculado a uma empresa",
    tags=["Establishments"],
)
@require_establishments_create()
async def create_establishment(
    establishment_data: EstablishmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Criar novo estabelecimento:

    - **company_id**: ID da empresa pai (obrigatório)
    - **code**: Código único dentro da empresa
    - **type**: Tipo (matriz, filial, unidade, posto)
    - **category**: Categoria (clínica, hospital, laboratório, etc.)
    - **person**: Dados da pessoa jurídica do estabelecimento
    - **is_principal**: Se é o estabelecimento principal da empresa
    - **settings**: Configurações específicas (opcional)
    - **operating_hours**: Horários de funcionamento (opcional)
    - **service_areas**: Áreas de serviço (opcional)
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        establishment = await repository.create(establishment_data)

        logger.info(
            "Establishment created",
            establishment_id=establishment.id,
            company_id=establishment.company_id,
            code=establishment.code,
            user_id=current_user.id,
        )

        return establishment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Error creating establishment", error=str(e), user_id=current_user.id
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/",
    response_model=EstablishmentListResponse,
    summary="Listar estabelecimentos",
    description="Listar estabelecimentos com filtros e paginação",
    tags=["Establishments"],
)
@require_establishments_view()
async def list_establishments(
    company_id: int = Query(
        None, description="Filtrar por empresa (apenas para admins do sistema)"
    ),
    is_active: bool = Query(None, description="Filtrar por status ativo"),
    is_principal: bool = Query(None, description="Filtrar estabelecimentos principais"),
    type: str = Query(None, description="Filtrar por tipo"),
    category: str = Query(None, description="Filtrar por categoria"),
    search: str = Query(
        None, min_length=1, max_length=100, description="Buscar por nome ou código"
    ),
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar estabelecimentos com filtros:

    - **company_id**: Filtrar por empresa específica (apenas para admins do sistema)
    - **is_active**: Filtrar por status ativo/inativo
    - **is_principal**: Filtrar estabelecimentos principais
    - **type**: Filtrar por tipo (matriz, filial, etc.)
    - **category**: Filtrar por categoria (clínica, hospital, etc.)
    - **search**: Buscar por nome ou código
    - **page**: Página (padrão: 1)
    - **size**: Itens por página (padrão: 10, máximo: 100)

    **Segurança Multi-Tenant:**
    - Usuários não-admin só veem estabelecimentos da sua empresa
    - Admins do sistema podem filtrar por qualquer empresa via company_id
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # 🔒 APLICAR FILTRO DE EMPRESA BASEADO NO CONTEXTO DO USUÁRIO
        effective_company_id = None

        if current_user.is_system_admin:
            # Admin do sistema pode ver qualquer empresa ou usar filtro específico
            effective_company_id = company_id  # Pode ser None para ver todas

            logger.info(
                "Admin listando estabelecimentos",
                admin_user_id=current_user.id,
                requested_company_id=company_id,
                admin_company_id=current_user.company_id,
            )
        else:
            # Usuário comum só pode ver estabelecimentos da sua própria empresa
            effective_company_id = current_user.company_id

            if company_id is not None and company_id != current_user.company_id:
                logger.warning(
                    "Tentativa de acesso cross-company negada",
                    user_id=current_user.id,
                    user_company_id=current_user.company_id,
                    requested_company_id=company_id,
                )
                raise HTTPException(
                    status_code=403,
                    detail="Acesso negado: você só pode visualizar estabelecimentos da sua empresa",
                )

            logger.info(
                "Usuário listando estabelecimentos da própria empresa",
                user_id=current_user.id,
                company_id=effective_company_id,
            )

        params = EstablishmentListParams(
            company_id=effective_company_id,
            is_active=is_active,
            is_principal=is_principal,
            type=type,
            category=category,
            search=search,
            page=page,
            size=size,
        )

        repository = EstablishmentRepository(db)

        establishments = await repository.list_establishments(params)
        total = await repository.count_establishments(params)

        pages = (total + size - 1) // size  # Ceiling division

        return EstablishmentListResponse(
            establishments=establishments,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    except Exception as e:
        logger.error(
            "Error listing establishments", error=str(e), user_id=current_user.id
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/{establishment_id}",
    response_model=EstablishmentDetailed,
    summary="Obter estabelecimento",
    description="Obter estabelecimento por ID com todos os detalhes",
    tags=["Establishments"],
)
@require_establishments_view()
async def get_establishment(
    establishment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obter estabelecimento específico por ID:

    - **establishment_id**: ID do estabelecimento
    - Retorna todos os detalhes incluindo pessoa, empresa relacionada e contadores

    **Segurança Multi-Tenant:**
    - Usuários não-admin só podem acessar estabelecimentos da sua empresa
    - Admins do sistema podem acessar qualquer estabelecimento
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        establishment = await repository.get_by_id(establishment_id)

        if not establishment:
            raise HTTPException(
                status_code=404, detail="Estabelecimento não encontrado"
            )

        # 🔒 VALIDAR ACESSO CROSS-COMPANY
        if not current_user.is_system_admin:
            if establishment.company_id != current_user.company_id:
                logger.warning(
                    "Tentativa de acesso cross-company negada no get_establishment",
                    user_id=current_user.id,
                    user_company_id=current_user.company_id,
                    establishment_company_id=establishment.company_id,
                    establishment_id=establishment_id,
                )
                raise HTTPException(
                    status_code=403,
                    detail="Acesso negado: você só pode visualizar estabelecimentos da sua empresa",
                )

        logger.info(
            "Estabelecimento acessado",
            user_id=current_user.id,
            establishment_id=establishment_id,
            establishment_company_id=establishment.company_id,
            is_system_admin=current_user.is_system_admin,
        )

        return establishment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error fetching establishment",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put(
    "/{establishment_id}",
    response_model=EstablishmentDetailed,
    summary="Atualizar estabelecimento",
    description="Atualizar estabelecimento e dados da pessoa relacionada",
    tags=["Establishments"],
)
async def update_establishment(
    establishment_id: int,
    establishment_data: EstablishmentUpdateComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Atualizar estabelecimento:

    - **establishment_id**: ID do estabelecimento
    - Pode atualizar dados do establishment e da pessoa relacionada
    - Validações automáticas para code único e estabelecimento principal
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        establishment = await repository.update(establishment_id, establishment_data)

        logger.info(
            "Establishment updated",
            establishment_id=establishment_id,
            user_id=current_user.id,
        )

        return establishment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Error updating establishment",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.patch(
    "/{establishment_id}/status",
    response_model=EstablishmentDetailed,
    summary="Alterar status do estabelecimento",
    description="Ativar ou desativar estabelecimento",
    tags=["Establishments"],
)
async def toggle_establishment_status(
    establishment_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Alterar status do estabelecimento:

    - **establishment_id**: ID do estabelecimento
    - **is_active**: true para ativar, false para desativar
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)

        update_data = EstablishmentUpdateComplete(is_active=is_active)
        establishment = await repository.update(establishment_id, update_data)

        logger.info(
            "Establishment status changed",
            establishment_id=establishment_id,
            new_status=is_active,
            user_id=current_user.id,
        )

        return establishment

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Error toggling establishment status",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete(
    "/{establishment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir estabelecimento",
    description="Soft delete de estabelecimento (apenas se não houver dependências)",
    tags=["Establishments"],
)
async def delete_establishment(
    establishment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Excluir estabelecimento:

    - **establishment_id**: ID do estabelecimento
    - Soft delete (deleted_at preenchido)
    - Valida se não possui usuários, profissionais ou clientes vinculados
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        success = await repository.delete(establishment_id)

        if not success:
            raise HTTPException(
                status_code=404, detail="Estabelecimento não encontrado"
            )

        logger.info(
            "Establishment deleted",
            establishment_id=establishment_id,
            user_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Error deleting establishment",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post(
    "/reorder",
    response_model=dict,
    summary="Reordenar estabelecimentos",
    description="Alterar ordem de display dos estabelecimentos dentro da empresa",
    tags=["Establishments"],
)
async def reorder_establishments(
    reorder_data: EstablishmentReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reordenar estabelecimentos:

    - **company_id**: ID da empresa
    - **establishment_orders**: Lista de objetos {id, order} com nova ordenação

    Exemplo:
    ```json
    {
      "company_id": 1,
      "establishment_orders": [
        {"id": 10, "order": 1},
        {"id": 15, "order": 2},
        {"id": 12, "order": 3}
      ]
    }
    ```
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        success = await repository.reorder(reorder_data)

        if not success:
            raise HTTPException(
                status_code=400, detail="Erro ao reordenar estabelecimentos"
            )

        logger.info(
            "Establishments reordered",
            company_id=reorder_data.company_id,
            count=len(reorder_data.establishment_orders),
            user_id=current_user.id,
        )

        return {"message": "Estabelecimentos reordenados com sucesso"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error reordering establishments", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post(
    "/validate",
    response_model=EstablishmentValidationResponse,
    summary="Validar criação de estabelecimento",
    description="Validar se é possível criar estabelecimento com os dados fornecidos",
    tags=["Establishments"],
)
async def validate_establishment_creation(
    company_id: int = Query(..., description="ID da empresa"),
    code: str = Query(..., description="Código do estabelecimento"),
    is_principal: bool = Query(False, description="Se será estabelecimento principal"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validar criação de estabelecimento:

    - **company_id**: ID da empresa pai
    - **code**: Código único do estabelecimento
    - **is_principal**: Se será estabelecimento principal

    Retorna:
    - is_valid: se é válido criar
    - error_message: mensagem de erro se inválido
    - suggested_display_order: próximo display_order sugerido
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        repository = EstablishmentRepository(db)
        validation = await repository.validate_creation(company_id, code, is_principal)

        return EstablishmentValidationResponse(
            is_valid=validation["is_valid"],
            error_message=validation["error_message"],
            suggested_display_order=validation["suggested_display_order"],
        )

    except Exception as e:
        logger.error("Error validating establishment creation", error=str(e))
        return EstablishmentValidationResponse(
            is_valid=False, error_message="Erro na validação", suggested_display_order=1
        )


@router.get(
    "/company/{company_id}",
    response_model=List[EstablishmentDetailed],
    summary="Listar estabelecimentos da empresa",
    description="Listar todos os estabelecimentos de uma empresa específica",
    tags=["Establishments"],
)
async def list_establishments_by_company(
    company_id: int,
    is_active: bool = Query(None, description="Filtrar por status ativo"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Listar estabelecimentos de uma empresa:

    - **company_id**: ID da empresa
    - **is_active**: Filtrar por status ativo (opcional)
    - Ordenado por display_order
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        params = EstablishmentListParams(
            company_id=company_id,
            is_active=is_active,
            page=1,
            size=100,  # Limite alto para pegar todos da empresa
        )

        repository = EstablishmentRepository(db)
        establishments = await repository.list_establishments(params)

        return establishments

    except Exception as e:
        logger.error(
            "Error listing establishments by company",
            company_id=company_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
