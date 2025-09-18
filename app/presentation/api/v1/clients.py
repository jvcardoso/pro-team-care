from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user, get_current_user_skip_options
from app.infrastructure.database import get_db
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.establishment_repository import (
    EstablishmentRepository,
)
from app.infrastructure.services.tenant_context_service import get_tenant_context
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.client import (
    ClientCreate,
    ClientDetailed,
    ClientExistingCheckResponse,
    ClientListParams,
    ClientListResponse,
    ClientStatus,
    ClientUpdateComplete,
    ClientValidationResponse,
    PersonType,
)

logger = structlog.get_logger()

router = APIRouter()


async def validate_establishment_access(
    establishment_id: int, current_user: Optional[User], db
) -> None:
    """Validar se o estabelecimento pertence à empresa do usuário"""
    if not current_user or current_user.is_system_admin:
        return  # Admin ou requisições sem auth podem acessar tudo

    establishment_repo = EstablishmentRepository(db)
    establishment = await establishment_repo.get_by_id(establishment_id)

    if not establishment:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")

    if establishment.company_id != current_user.company_id:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: estabelecimento não pertence à sua empresa",
        )


# Endpoint de teste simples
@router.post("/simple-test")
async def simple_test():
    return {"message": "POST funcionando"}


# Endpoint de teste sem autenticação
@router.post(
    "/test",
    summary="Teste de criação",
    description="Endpoint de teste para verificar se POST funciona",
    tags=["Clients"],
)
async def test_create():
    logger.info("=== POST /clients/test CHAMADO ===")
    return {"message": "Teste funcionando"}
    """
    Criar novo cliente:

    - **establishment_id**: ID do estabelecimento (obrigatório)
    - **client_code**: Código único dentro do estabelecimento (opcional)
    - **status**: Status do cliente (padrão: active)
    - **person**: Dados da pessoa física/jurídica do cliente
    - **existing_person_id**: ID de pessoa existente para reutilizar

    **Validações automáticas:**
    - CPF/CNPJ deve ser válido e único (se criar nova pessoa)
    - Cliente não pode ser duplicado no mesmo estabelecimento
    - Client_code deve ser único no estabelecimento (se fornecido)
    """
    try:
        logger.info("=== INÍCIO CRIAÇÃO CLIENT ===")
        logger.info("Endpoint POST /clients chamado!")
        logger.info("Dados recebidos", client_data=client_data.model_dump())

        repository = ClientRepository(db)
        logger.info("Repository criado com sucesso")

        client = await repository.create(client_data)
        logger.info("Client criado com sucesso")

        logger.info(
            "Client created",
            client_id=client.id,
            establishment_id=client.establishment_id,
            person_id=client.person_id,
            client_code=client.client_code,
        )

        return client

    except ValueError as e:
        logger.error("ValueError em create_client", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating client", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get(
    "/",
    response_model=ClientListResponse,
    summary="Listar clientes",
    description="Listar clientes com filtros e paginação",
    tags=["Clients"],
)
@require_permission("clients_view", context_type="establishment")
async def list_clients(
    establishment_id: int = Query(
        None, description="Filtrar por estabelecimento (apenas para admins do sistema)"
    ),
    status: str = Query(None, description="Filtrar por status"),
    person_type: str = Query(None, description="Filtrar por tipo de pessoa (PF/PJ)"),
    search: str = Query(
        None, min_length=1, max_length=100, description="Buscar por nome ou CPF/CNPJ"
    ),
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(10, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Listar clientes com filtros:

    - **establishment_id**: Filtrar por estabelecimento específico (apenas para admins do sistema)
    - **status**: Filtrar por status (active, inactive, on_hold, archived)
    - **person_type**: Filtrar por tipo de pessoa (PF, PJ)
    - **search**: Buscar por nome ou CPF/CNPJ
    - **page**: Página (padrão: 1)
    - **size**: Itens por página (padrão: 10, máximo: 100)

    **Segurança Multi-Tenant:**
    - Usuários não-admin só veem clientes dos estabelecimentos da sua empresa
    - Admins do sistema podem filtrar por qualquer estabelecimento via establishment_id
    """
    try:
        # Set tenant context for multi-tenant isolation
        tenant_service = get_tenant_context()
        await tenant_service.set_database_context(db, current_user.company_id)

        # 🔒 APLICAR FILTRO DE EMPRESA BASEADO NO CONTEXTO DO USUÁRIO
        effective_establishment_id = None

        if current_user.is_system_admin:
            # Admin do sistema pode ver qualquer estabelecimento ou usar filtro específico
            effective_establishment_id = (
                establishment_id  # Pode ser None para ver todos
            )

            if establishment_id:
                await validate_establishment_access(establishment_id, current_user, db)

            logger.info(
                "Admin listando clientes",
                admin_user_id=current_user.id,
                requested_establishment_id=establishment_id,
                admin_company_id=current_user.company_id,
            )
        else:
            # Usuário comum precisa filtrar por estabelecimentos da sua empresa
            if establishment_id:
                # Validar que o estabelecimento pertence à sua empresa
                await validate_establishment_access(establishment_id, current_user, db)
                effective_establishment_id = establishment_id
            else:
                # Se não especificou estabelecimento, buscar de todos os estabelecimentos da empresa
                # effective_establishment_id = None significará filtrar por company_id no repositório
                effective_establishment_id = None

            logger.info(
                "Usuário listando clientes da própria empresa",
                user_id=current_user.id,
                company_id=current_user.company_id,
                establishment_id=effective_establishment_id,
            )

        # Convert string values to enum values
        status_enum = None
        if status:
            try:
                status_enum = ClientStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Status inválido: {status}"
                )

        person_type_enum = None
        if person_type:
            try:
                person_type_enum = PersonType(person_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Tipo de pessoa inválido: {person_type}"
                )

        params = ClientListParams(
            establishment_id=effective_establishment_id,
            status=status_enum,
            person_type=person_type_enum,
            search=search,
            page=page,
            size=size,
        )

        repository = ClientRepository(db)

        # Para usuários não-admin sem establishment_id específico, filtrar por company_id
        if not current_user.is_system_admin and effective_establishment_id is None:
            clients = await repository.list_clients_by_company(
                params, current_user.company_id
            )
            total = await repository.count_clients_by_company(
                params, current_user.company_id
            )
        else:
            clients = await repository.list_clients(params)
            total = await repository.count_clients(params)

        pages = (total + size - 1) // size  # Ceiling division

        return ClientListResponse(
            clients=clients,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    except Exception as e:
        logger.error("Error listing clients", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/{client_id}",
    response_model=ClientDetailed,
    summary="Obter cliente",
    description="Obter cliente por ID com todos os detalhes",
    tags=["Clients"],
)
@require_permission("clients_view", context_type="establishment")
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Obter cliente específico por ID:

    - **client_id**: ID do cliente
    - Retorna todos os detalhes incluindo pessoa, estabelecimento, empresa e contatos
    """
    try:
        repository = ClientRepository(db)
        client = await repository.get_by_id(client_id)

        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        return client

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching client", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put(
    "/{client_id}",
    response_model=ClientDetailed,
    summary="Atualizar cliente",
    description="Atualizar cliente e dados da pessoa relacionada",
    tags=["Clients"],
)
@require_permission("clients_update", context_type="establishment")
async def update_client(
    client_id: int,
    client_data: ClientUpdateComplete,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Atualizar cliente:

    - **client_id**: ID do cliente
    - Pode atualizar dados do cliente e da pessoa relacionada
    - Validações automáticas para client_code único

    **Campos atualizáveis:**
    - client_code: Código do cliente
    - status: Status do cliente
    - person: Dados da pessoa (nome, telefones, emails, endereços, etc.)
    """
    try:
        repository = ClientRepository(db)
        client = await repository.update(client_id, client_data)

        logger.info(
            "Client updated",
            client_id=client_id,
            user_id=current_user.id,
        )

        return client

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error updating client", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.patch(
    "/{client_id}/status",
    response_model=ClientDetailed,
    summary="Alterar status do cliente",
    description="Alterar status do cliente",
    tags=["Clients"],
)
@require_permission("clients_update", context_type="establishment")
async def toggle_client_status(
    client_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Alterar status do cliente:

    - **client_id**: ID do cliente
    - **status**: Novo status (active, inactive, on_hold, archived)
    """
    try:
        repository = ClientRepository(db)

        # Convert string to enum
        status_enum = None
        if status:
            try:
                status_enum = ClientStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Status inválido: {status}"
                )

        update_data = ClientUpdateComplete(
            client_code=None, status=status_enum, person=None
        )
        client = await repository.update(client_id, update_data)

        logger.info(
            "Client status changed",
            client_id=client_id,
            new_status=status,
            user_id=current_user.id,
        )

        return client

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error toggling client status", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir cliente",
    description="Soft delete de cliente (apenas se não houver dependências)",
    tags=["Clients"],
)
@require_permission("clients_delete", context_type="establishment")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Excluir cliente:

    - **client_id**: ID do cliente
    - Soft delete (deleted_at preenchido)
    - Valida se não possui agendamentos ou outras dependências
    """
    try:
        repository = ClientRepository(db)
        success = await repository.delete(client_id)

        if not success:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        logger.info("Client deleted", client_id=client_id, user_id=current_user.id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error deleting client", client_id=client_id, error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post(
    "/validate",
    response_model=ClientValidationResponse,
    summary="Validar criação de cliente",
    description="Validar se é possível criar cliente com os dados fornecidos",
    tags=["Clients"],
)
async def validate_client_creation(
    establishment_id: int = Query(..., description="ID do estabelecimento"),
    tax_id: str = Query(..., description="CPF ou CNPJ do cliente"),
    client_code: str = Query(None, description="Código do cliente (opcional)"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Validar acesso ao estabelecimento
    await validate_establishment_access(establishment_id, current_user, db)
    """
    Validar criação de cliente:

    - **establishment_id**: ID do estabelecimento
    - **tax_id**: CPF ou CNPJ do cliente
    - **client_code**: Código do cliente (opcional)

    Retorna:
    - is_valid: se é válido criar
    - error_message: mensagem de erro se inválido
    - warnings: avisos importantes
    """
    try:
        repository = ClientRepository(db)
        validation = await repository.validate_creation(
            establishment_id, client_code, tax_id, allow_existing_tax_id=False
        )

        return ClientValidationResponse(
            is_valid=validation["is_valid"],
            error_message=validation["error_message"],
            warnings=[],
        )

    except Exception as e:
        logger.error("Error validating client creation", error=str(e))
        return ClientValidationResponse(
            is_valid=False,
            error_message="Erro na validação",
            warnings=["Erro interno durante validação"],
        )


@router.get(
    "/establishment/{establishment_id}",
    response_model=List[ClientDetailed],
    summary="Listar clientes do estabelecimento",
    description="Listar todos os clientes de um estabelecimento específico",
    tags=["Clients"],
)
async def list_clients_by_establishment(
    establishment_id: int,
    status: str = Query(None, description="Filtrar por status"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Validar acesso ao estabelecimento
    if current_user:
        await validate_establishment_access(establishment_id, current_user, db)
    """
    Listar clientes de um estabelecimento:

    - **establishment_id**: ID do estabelecimento
    - **status**: Filtrar por status (opcional)
    - Ordenado por nome do cliente
    """
    try:
        # Convert string values to enum values
        status_enum = None
        if status:
            try:
                status_enum = ClientStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Status inválido: {status}"
                )

        params = ClientListParams(
            establishment_id=establishment_id,
            status=status_enum,
            person_type=None,
            search=None,
            page=1,
            size=100,  # Limite máximo permitido pelo schema
        )

        repository = ClientRepository(db)
        clients = await repository.list_clients(params)

        return clients

    except Exception as e:
        logger.error(
            "Error listing clients by establishment",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/check-existing-in-establishment",
    response_model=ClientExistingCheckResponse,
    summary="Verificar se cliente existe no estabelecimento",
    description="Verificar se já existe cliente com este CPF/CNPJ no estabelecimento específico",
    tags=["Clients"],
)
async def check_existing_client_in_establishment(
    establishment_id: int = Query(..., description="ID do estabelecimento"),
    tax_id: str = Query(..., description="CPF ou CNPJ para verificação"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Validar acesso ao estabelecimento
    await validate_establishment_access(establishment_id, current_user, db)
    """
    Verificar se cliente já existe no estabelecimento:

    - **establishment_id**: ID do estabelecimento
    - **tax_id**: CPF ou CNPJ para verificação

    Retorna:
    - exists_in_establishment: se existe cliente no mesmo estabelecimento
    - existing_client: dados do cliente existente (se houver)
    - person_exists_globally: se a pessoa existe em outros estabelecimentos
    - existing_person: dados da pessoa (se existir globalmente)
    - person_type: tipo detectado (PF/PJ)
    """
    try:
        import re

        clean_tax_id = re.sub(r"\D", "", tax_id)

        # Determinar tipo de pessoa
        person_type = "PF" if len(clean_tax_id) == 11 else "PJ"

        repository = ClientRepository(db)

        # 1. Buscar todos os clientes com este CPF/CNPJ
        all_clients_params = ClientListParams(
            establishment_id=None,
            status=None,
            person_type=None,
            search=clean_tax_id,
            page=1,
            size=100,
        )
        all_clients = await repository.list_clients(all_clients_params)

        # 2. Verificar se existe no estabelecimento específico
        existing_client_in_establishment = None
        for client in all_clients:
            if client.establishment_id == establishment_id:
                existing_client_in_establishment = client
                break

        # 3. Obter dados da pessoa se existir
        existing_person_dict = None
        if all_clients:
            person = all_clients[0].person  # Todos compartilham a mesma pessoa
            if person:
                existing_person_dict = {
                    "id": person.id,
                    "name": person.name,
                    "tax_id": person.tax_id,
                    "person_type": person.person_type,
                }

        try:
            response_data = ClientExistingCheckResponse(
                exists_in_establishment=existing_client_in_establishment is not None,
                existing_client=existing_client_in_establishment,
                person_exists_globally=len(all_clients) > 0,
                existing_person=existing_person_dict,
                person_type=person_type,
                other_establishments=[
                    {
                        "establishment_id": client.establishment_id,
                        "establishment_name": (
                            client.establishment_name
                            if hasattr(client, "establishment_name")
                            else f"Estabelecimento {client.establishment_id}"
                        ),
                        "client_code": client.client_code,
                        "status": client.status,
                    }
                    for client in all_clients
                    if client.establishment_id != establishment_id
                ],
            )

            logger.info(
                "Duplication check completed successfully",
                establishment_id=establishment_id,
                tax_id=clean_tax_id,
                exists_in_establishment=response_data.exists_in_establishment,
                person_exists_globally=response_data.person_exists_globally,
                person_type=response_data.person_type,
                other_establishments_count=len(response_data.other_establishments),
            )

            return response_data

        except Exception as validation_error:
            logger.error(
                "Error validating duplication check response",
                establishment_id=establishment_id,
                tax_id=clean_tax_id,
                validation_error=str(validation_error),
                existing_client_data=(
                    existing_client_in_establishment.model_dump()
                    if existing_client_in_establishment
                    else None
                ),
            )

            # Return a simpler response that avoids validation issues
            return {
                "exists_in_establishment": existing_client_in_establishment is not None,
                "existing_client": (
                    None
                    if not existing_client_in_establishment
                    else {
                        "id": existing_client_in_establishment.id,
                        "name": existing_client_in_establishment.name,
                        "tax_id": existing_client_in_establishment.tax_id,
                        "client_code": existing_client_in_establishment.client_code,
                        "status": existing_client_in_establishment.status,
                    }
                ),
                "person_exists_globally": len(all_clients) > 0,
                "existing_person": existing_person_dict,
                "person_type": person_type,
                "other_establishments": [
                    {
                        "establishment_id": client.establishment_id,
                        "establishment_name": getattr(
                            client,
                            "establishment_name",
                            f"Estabelecimento {client.establishment_id}",
                        ),
                        "client_code": client.client_code or "",
                        "status": client.status,
                    }
                    for client in all_clients
                    if client.establishment_id != establishment_id
                ],
            }

    except Exception as e:
        logger.error(
            "Error checking existing client in establishment",
            establishment_id=establishment_id,
            tax_id=tax_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/search/by-tax-id",
    response_model=List[ClientDetailed],
    summary="Buscar cliente por CPF/CNPJ",
    description="Buscar clientes pelo CPF ou CNPJ em todos os estabelecimentos",
    tags=["Clients"],
)
async def search_clients_by_tax_id(
    tax_id: str = Query(..., description="CPF ou CNPJ para busca"),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Buscar clientes por CPF/CNPJ:

    - **tax_id**: CPF ou CNPJ para busca
    - Retorna todos os registros de cliente desta pessoa em diferentes estabelecimentos
    """
    try:
        # Remove caracteres não numéricos do tax_id
        import re

        clean_tax_id = re.sub(r"\D", "", tax_id)

        params = ClientListParams(
            establishment_id=None,
            status=None,
            person_type=None,
            search=clean_tax_id,
            page=1,
            size=100,  # Limite para evitar sobrecarga
        )

        repository = ClientRepository(db)
        clients = await repository.list_clients(params)

        return clients

    except Exception as e:
        logger.error(
            "Error searching clients by tax_id",
            tax_id=tax_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/stats/by-establishment/{establishment_id}",
    summary="Estatísticas de clientes por estabelecimento",
    description="Obter estatísticas de clientes de um estabelecimento",
    tags=["Clients"],
)
async def get_client_stats_by_establishment(
    establishment_id: int,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Validar acesso ao estabelecimento
    await validate_establishment_access(establishment_id, current_user, db)
    """
    Estatísticas de clientes:

    - **establishment_id**: ID do estabelecimento
    - Retorna contadores por status, tipo de pessoa, etc.
    """
    try:
        repository = ClientRepository(db)

        # Contar por status
        stats = {}
        for status_value in ["active", "inactive", "on_hold", "archived"]:
            params = ClientListParams(
                establishment_id=establishment_id,
                status=ClientStatus(status_value),
                person_type=None,
                search=None,
                page=1,
                size=1,
            )
            count = await repository.count_clients(params)
            stats[f"status_{status_value}"] = count

        # Contar por tipo de pessoa
        for person_type in ["PF", "PJ"]:
            params = ClientListParams(
                establishment_id=establishment_id,
                status=None,
                person_type=PersonType(person_type),
                search=None,
                page=1,
                size=1,
            )
            count = await repository.count_clients(params)
            stats[f"person_type_{person_type}"] = count

        # Total geral
        params = ClientListParams(
            establishment_id=establishment_id,
            status=None,
            person_type=None,
            search=None,
            page=1,
            size=1,
        )
        stats["total"] = await repository.count_clients(params)

        return stats

    except Exception as e:
        logger.error(
            "Error getting client stats",
            establishment_id=establishment_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# SOLUÇÃO TEMPORÁRIA: Usar rota /create até resolver problema da rota /
@router.post(
    "/create",
    response_model=ClientDetailed,
    status_code=status.HTTP_201_CREATED,
    summary="Criar cliente",
    description="Criar novo cliente vinculado a um estabelecimento",
    tags=["Clients"],
)
@require_permission("clients_create", context_type="establishment")
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Validar acesso ao estabelecimento
    await validate_establishment_access(client_data.establishment_id, current_user, db)
    """
    Criar novo cliente:

    - **establishment_id**: ID do estabelecimento (obrigatório)
    - **client_code**: Código único dentro do estabelecimento (opcional)
    - **status**: Status do cliente (padrão: active)
    - **person**: Dados da pessoa física/jurídica do cliente
    - **existing_person_id**: ID de pessoa existente para reutilizar (alternativa a 'person')

    **Validações automáticas:**
    - CPF/CNPJ deve ser válido e único (se criar nova pessoa)
    - Cliente não pode ser duplicado no mesmo estabelecimento
    - Client_code deve ser único no estabelecimento (se fornecido)
    """
    try:
        logger.info("=== INÍCIO CRIAÇÃO CLIENT ===")
        logger.info("Dados recebidos", client_data=client_data.model_dump())

        repository = ClientRepository(db)
        logger.info("Repository criado com sucesso")

        client = await repository.create(client_data)
        logger.info("Client criado com sucesso")

        logger.info(
            "Client created",
            client_id=client.id,
            establishment_id=client.establishment_id,
            person_id=client.person_id,
            client_code=client.client_code,
        )

        return client

    except ValueError as e:
        logger.error("ValueError em create_client", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating client", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Erro interno do servidor: {str(e)}"
        )
