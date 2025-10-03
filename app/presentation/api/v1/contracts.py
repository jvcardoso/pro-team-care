from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.contract_repository import (
    ContractRepository,
    ServicesRepository,
)
from app.infrastructure.services.tenant_context_service import get_tenant_context
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.contract import (
    ContractCreate,
    ContractDetailed,
    ContractListParams,
    ContractListResponse,
    ContractResponse,
    ContractStatus,
    ContractType,
    ContractUpdate,
    ServicesCatalogResponse,
    ServicesListParams,
    ServicesListResponse,
)
from app.presentation.schemas.contract_lives import (
    ContractLifeCreate,
    ContractLifeHistoryResponse,
    ContractLifeResponse,
    ContractLifeUpdate,
)

logger = structlog.get_logger()

router = APIRouter()


@router.post(
    "/", response_model=ContractResponse, status_code=http_status.HTTP_201_CREATED
)
@require_permission("contracts.create")
async def create_contract(
    contract_data: ContractCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new contract"""
    try:
        contract_repo = ContractRepository(db)

        # Add created_by from current user
        contract_dict = contract_data.model_dump()
        contract_dict["created_by"] = current_user.id

        contract = await contract_repo.create_contract(contract_dict)
        await db.commit()

        logger.info(
            "Contract created successfully",
            contract_id=contract.id,
            contract_number=contract.contract_number,
            client_id=contract.client_id,
            created_by=current_user.id,
        )

        return ContractResponse.model_validate(contract)

    except Exception as e:
        await db.rollback()
        logger.error(
            "Error creating contract",
            error=str(e),
            contract_data=contract_data.model_dump(),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao criar contrato",
        )


@router.get("/test", response_model=dict)
async def test_contracts_endpoint(db=Depends(get_db)):
    """Test endpoint to check if contracts table is accessible"""
    try:
        from sqlalchemy import text

        result = await db.execute(
            text("SELECT COUNT(*) as count FROM master.contracts")
        )
        count = result.scalar()
        return {"contracts_table_exists": True, "contracts_count": count}
    except Exception as e:
        return {"contracts_table_exists": False, "error": str(e)}


@router.get("/", response_model=ContractListResponse)
@require_permission("contracts.view")
async def list_contracts(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    contract_status: Optional[ContractStatus] = Query(
        None, description="Filter by contract status"
    ),
    contract_type: Optional[ContractType] = Query(
        None, description="Filter by contract type"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List contracts with filtering and pagination"""
    try:
        logger.info(
            "Starting contracts list request",
            client_id=client_id,
            status=contract_status,
            contract_type=contract_type,
        )
        contract_repo = ContractRepository(db)

        result = await contract_repo.list_contracts(
            client_id=client_id,
            status=contract_status,
            contract_type=contract_type,
            page=page,
            size=size,
        )

        # Convert contracts to response models
        try:
            logger.info(
                "Converting contracts to response models",
                contracts_count=len(result["contracts"]),
            )
            if result["contracts"]:
                logger.info(
                    "First contract data",
                    contract_data=(
                        result["contracts"][0].__dict__
                        if hasattr(result["contracts"][0], "__dict__")
                        else str(result["contracts"][0])
                    ),
                )
            contracts_response = [
                ContractResponse.model_validate(contract)
                for contract in result["contracts"]
            ]
            logger.info("Conversion completed successfully")
        except Exception as e:
            logger.error(
                "Error converting contracts to response models",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

        logger.info(
            "Contracts listed successfully",
            total=result["total"],
            page=page,
            size=size,
            filters={
                "client_id": client_id,
                "status": contract_status,
                "contract_type": contract_type,
            },
            user_id=current_user.id,
        )

        return ContractListResponse(
            contracts=contracts_response,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"],
        )

    except Exception as e:
        logger.error("Error listing contracts", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar contratos",
        )


@router.get("/{contract_id}", response_model=ContractDetailed)
@require_permission("contracts.view")
async def get_contract(
    contract_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get contract by ID with detailed information"""
    try:
        contract_repo = ContractRepository(db)
        contract = await contract_repo.get_contract_by_id(contract_id)

        if not contract:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado",
            )

        logger.info(
            "Contract retrieved successfully",
            contract_id=contract_id,
            contract_number=contract.contract_number,
            user_id=current_user.id,
        )

        return ContractDetailed.model_validate(contract)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving contract", error=str(e), contract_id=contract_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar contrato",
        )


@router.put("/{contract_id}", response_model=ContractResponse)
@require_permission("contracts.update")
async def update_contract(
    contract_id: int,
    update_data: ContractUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update contract"""
    try:
        contract_repo = ContractRepository(db)

        # Only include fields that are not None
        update_dict = {
            k: v for k, v in update_data.model_dump().items() if v is not None
        }

        if not update_dict:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar foi fornecido",
            )

        contract = await contract_repo.update_contract(contract_id, update_dict)

        if not contract:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado",
            )

        await db.commit()

        logger.info(
            "Contract updated successfully",
            contract_id=contract_id,
            updated_fields=list(update_dict.keys()),
            user_id=current_user.id,
        )

        return ContractResponse.model_validate(contract)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error updating contract", error=str(e), contract_id=contract_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar contrato",
        )


@router.delete("/{contract_id}", status_code=http_status.HTTP_204_NO_CONTENT)
@require_permission("contracts.delete")
async def delete_contract(
    contract_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete contract"""
    try:
        contract_repo = ContractRepository(db)

        deleted = await contract_repo.delete_contract(contract_id)

        if not deleted:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado",
            )

        await db.commit()

        logger.info(
            "Contract deleted successfully",
            contract_id=contract_id,
            user_id=current_user.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error deleting contract", error=str(e), contract_id=contract_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao deletar contrato",
        )


@router.get("/count/", response_model=dict)
@require_permission("contracts.view")
async def count_contracts(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    status: Optional[ContractStatus] = Query(
        None, description="Filter by contract status"
    ),
    contract_type: Optional[ContractType] = Query(
        None, description="Filter by contract type"
    ),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Count contracts with filtering"""
    try:
        contract_repo = ContractRepository(db)

        # Get count by fetching first page with minimal data
        result = await contract_repo.list_contracts(
            client_id=client_id,
            status=status,
            contract_type=contract_type,
            page=1,
            size=1,
        )

        logger.info(
            "Contracts counted successfully",
            count=result["total"],
            filters={
                "client_id": client_id,
                "status": status,
                "contract_type": contract_type,
            },
            user_id=current_user.id,
        )

        return {"count": result["total"]}

    except Exception as e:
        logger.error("Error counting contracts", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao contar contratos",
        )


# ==========================================
# SERVICES CATALOG ENDPOINTS
# ==========================================

services_router = APIRouter()


@services_router.get("/", response_model=ServicesListResponse)
@require_permission("services.view")
async def list_services_catalog(
    category: Optional[str] = Query(None, description="Filter by service category"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(100, ge=1, le=500, description="Page size"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List services catalog with filtering and pagination"""
    try:
        services_repo = ServicesRepository(db)

        result = await services_repo.list_services_catalog(
            category=category,
            service_type=service_type,
            page=page,
            size=size,
        )

        # Convert services to response models
        services_response = [
            ServicesCatalogResponse.model_validate(service)
            for service in result["services"]
        ]

        logger.info(
            "Services catalog listed successfully",
            total=result["total"],
            page=page,
            size=size,
            filters={"category": category, "service_type": service_type},
            user_id=current_user.id,
        )

        return ServicesListResponse(
            services=services_response,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"],
        )

    except Exception as e:
        logger.error("Error listing services catalog", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar catálogo de serviços",
        )


@services_router.get("/{service_id}", response_model=ServicesCatalogResponse)
@require_permission("services.view")
async def get_service(
    service_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get service by ID"""
    try:
        services_repo = ServicesRepository(db)
        service = await services_repo.get_service_by_id(service_id)

        if not service:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Serviço não encontrado",
            )

        logger.info(
            "Service retrieved successfully",
            service_id=service_id,
            service_code=service.service_code,
            user_id=current_user.id,
        )

        return ServicesCatalogResponse.model_validate(service)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving service", error=str(e), service_id=service_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao buscar serviço",
        )


# ==========================================
# CONTRACT LIVES ENDPOINTS
# ==========================================


@router.get("/{contract_id}/lives", response_model=List[ContractLifeResponse])
@require_permission("contracts.view")
async def list_contract_lives(
    contract_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todas as vidas vinculadas a um contrato

    **Retorna:**
    - Lista de vidas com informações de pessoa (JOIN com people)
    - Ordenado por data de início (mais recente primeiro)

    **Permissão necessária:** `contracts.view`
    """
    try:
        from sqlalchemy import select

        from app.application.validators.contract_lives_validator import (
            ContractLivesValidator,
        )
        from app.infrastructure.orm.models import ContractLive, People
        from app.presentation.schemas.contract_lives import ContractLifeResponse

        # Validar que contrato existe
        validator = ContractLivesValidator(db)
        await validator.validate_contract_exists(contract_id)

        # Buscar vidas com JOIN em people
        query = (
            select(
                ContractLive,
                People.name.label("person_name"),
                People.tax_id.label("person_cpf"),
            )
            .join(People, ContractLive.person_id == People.id)
            .where(ContractLive.contract_id == contract_id)
            .order_by(ContractLive.start_date.desc())
        )

        result = await db.execute(query)
        lives_data = result.all()

        # Converter para schema Pydantic
        lives = []
        for live, person_name, person_cpf in lives_data:
            life_dict = {
                "id": live.id,
                "contract_id": live.contract_id,
                "person_id": live.person_id,
                "person_name": person_name,
                "person_cpf": person_cpf,
                "start_date": live.start_date,
                "end_date": live.end_date,
                "status": live.status or "active",
                "relationship_type": live.relationship_type,
                "substitution_reason": live.substitution_reason,
                "allows_substitution": True,  # Default (campo não existe na tabela)
                "primary_service_address": live.primary_service_address,
                "created_at": live.created_at,
                "updated_at": live.updated_at,
                "created_by": live.created_by,
            }
            lives.append(ContractLifeResponse(**life_dict))

        logger.info(
            "Contract lives listed successfully",
            contract_id=contract_id,
            lives_count=len(lives),
            user_id=current_user.id,
        )

        return lives

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error listing contract lives", error=str(e), contract_id=contract_id
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar vidas do contrato",
        )


@router.post("/{contract_id}/lives", response_model=dict, status_code=http_status.HTTP_201_CREATED)
@require_permission("contracts.lives.manage")
async def add_contract_life(
    contract_id: int,
    life_data: ContractLifeCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adiciona uma nova vida ao contrato

    **Validações aplicadas:**
    - Contrato existe e está ativo
    - Não há sobreposição de períodos para a mesma pessoa
    - Período da vida está dentro do período do contrato
    - Limites de vidas (mínimo, máximo, contratado) não foram excedidos
    - Validação de datas (end_date >= start_date)

    **Permissão necessária:** `contracts.lives.manage`
    """
    try:
        from datetime import datetime

        from sqlalchemy import select

        from app.application.validators.contract_lives_validator import (
            ContractLivesValidator,
        )
        from app.infrastructure.orm.models import ContractLive, People
        from app.infrastructure.services.tenant_context_service import TenantContext

        # Inicializar validador
        validator = ContractLivesValidator(db)

        # Validação 1: Contrato existe e está ativo
        contract = await validator.validate_contract_exists(contract_id)

        # Validação 2: Limites de vidas (adicionar)
        await validator.validate_lives_limits(contract_id, action="add")

        # Validação 3: Período dentro do contrato
        await validator.validate_date_within_contract_period(
            contract_id, life_data.start_date, life_data.end_date
        )

        # Buscar ou criar pessoa
        person_query = select(People).where(People.name == life_data.person_name)
        person_result = await db.execute(person_query)
        person = person_result.scalar_one_or_none()

        if not person:
            # Criar nova pessoa (PF)
            # Obter company_id do contexto de tenant
            tenant_context = TenantContext.get_context()
            company_id = tenant_context.get("company_id", 1)  # Fallback para company_id=1

            person = People(
                name=life_data.person_name,
                person_type="PF",
                status="active",
                company_id=company_id,
                tax_id=f"TEMP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",  # CPF temporário
            )
            db.add(person)
            await db.flush()
            await db.refresh(person)

        # Validação 4: Não há sobreposição de períodos
        await validator.validate_no_period_overlap(
            contract_id, person.id, life_data.start_date, life_data.end_date
        )

        # Criar vida no contrato
        contract_life = ContractLive(
            contract_id=contract_id,
            person_id=person.id,
            start_date=life_data.start_date,
            end_date=life_data.end_date,
            relationship_type=life_data.relationship_type,
            status="active",
            substitution_reason=life_data.notes,
            created_by=current_user.id,
        )

        db.add(contract_life)
        await db.commit()
        await db.refresh(contract_life)

        logger.info(
            "Contract life added successfully",
            contract_id=contract_id,
            life_id=contract_life.id,
            person_id=person.id,
            person_name=life_data.person_name,
            user_id=current_user.id,
        )

        return {
            "id": contract_life.id,
            "person_id": person.id,
            "message": f"{life_data.person_name} adicionado ao contrato com sucesso",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error adding contract life",
            error=str(e),
            contract_id=contract_id,
            life_data=life_data.model_dump(),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao adicionar vida ao contrato: {str(e)}",
        )


@router.put("/{contract_id}/lives/{life_id}", response_model=dict)
@require_permission("contracts.lives.manage")
async def update_contract_life(
    contract_id: int,
    life_id: int,
    life_data: ContractLifeUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza uma vida do contrato (usualmente para encerrar ou substituir)

    **Casos de uso comuns:**
    - Encerrar vida: definir `end_date` e `status = 'cancelled'`
    - Substituir vida: definir `status = 'substituted'` e `substitution_reason`
    - Atualizar observações: definir `notes`

    **Validações aplicadas:**
    - Vida existe e pertence ao contrato
    - end_date >= start_date (se fornecido)

    **Permissão necessária:** `contracts.lives.manage`
    """
    try:
        from datetime import datetime

        from sqlalchemy import select, update

        from app.infrastructure.orm.models import ContractLive

        # Buscar vida para atualizar
        query = select(ContractLive).where(
            ContractLive.id == life_id, ContractLive.contract_id == contract_id
        )
        result = await db.execute(query)
        contract_life = result.scalar_one_or_none()

        if not contract_life:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Vida {life_id} não encontrada no contrato {contract_id}",
            )

        # Validar end_date >= start_date (se fornecido)
        if life_data.end_date and life_data.end_date < contract_life.start_date:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"end_date ({life_data.end_date}) deve ser posterior ou igual a "
                    f"start_date ({contract_life.start_date})"
                ),
            )

        # Montar dados para atualização (apenas campos fornecidos)
        update_data = {}
        if life_data.end_date is not None:
            update_data["end_date"] = life_data.end_date
        if life_data.status is not None:
            update_data["status"] = life_data.status
        if life_data.notes is not None:
            # Nota: campo 'notes' não existe, mas 'substitution_reason' sim
            update_data["substitution_reason"] = life_data.notes
        if life_data.substitution_reason is not None:
            update_data["substitution_reason"] = life_data.substitution_reason

        # Sempre atualizar timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Executar update
        stmt = (
            update(ContractLive).where(ContractLive.id == life_id).values(**update_data)
        )
        await db.execute(stmt)
        await db.commit()

        logger.info(
            "Contract life updated successfully",
            contract_id=contract_id,
            life_id=life_id,
            updated_fields=list(update_data.keys()),
            user_id=current_user.id,
        )

        return {
            "message": "Vida do contrato atualizada com sucesso",
            "life_id": life_id,
            "updated_fields": list(update_data.keys()),
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error updating contract life",
            error=str(e),
            contract_id=contract_id,
            life_id=life_id,
            life_data=life_data.model_dump(exclude_unset=True),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao atualizar vida do contrato: {str(e)}",
        )


@router.delete(
    "/{contract_id}/lives/{life_id}", status_code=http_status.HTTP_204_NO_CONTENT
)
@require_permission("contracts.lives.manage")
async def remove_contract_life(
    contract_id: int,
    life_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove (encerra) uma vida do contrato

    **Comportamento:** Soft delete
    - Define `status = 'cancelled'`
    - Define `end_date = hoje`
    - **NÃO deleta** fisicamente o registro (preserva auditoria)

    **Validações aplicadas:**
    - Vida existe e pertence ao contrato
    - Limite mínimo de vidas não é violado

    **Permissão necessária:** `contracts.lives.manage`
    """
    try:
        from datetime import datetime

        from sqlalchemy import select, update

        from app.application.validators.contract_lives_validator import (
            ContractLivesValidator,
        )
        from app.infrastructure.orm.models import ContractLive

        # Inicializar validador
        validator = ContractLivesValidator(db)

        # Buscar vida para remover
        query = select(ContractLive).where(
            ContractLive.id == life_id, ContractLive.contract_id == contract_id
        )
        result = await db.execute(query)
        contract_life = result.scalar_one_or_none()

        if not contract_life:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Vida {life_id} não encontrada no contrato {contract_id}",
            )

        # Validar limite mínimo de vidas (antes de remover)
        await validator.validate_lives_limits(contract_id, action="remove")

        # Encerrar vida (soft delete)
        stmt = (
            update(ContractLive)
            .where(ContractLive.id == life_id)
            .values(
                status="cancelled",
                end_date=datetime.utcnow().date(),
                updated_at=datetime.utcnow(),
            )
        )

        await db.execute(stmt)
        await db.commit()

        logger.info(
            "Contract life removed successfully",
            contract_id=contract_id,
            life_id=life_id,
            user_id=current_user.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            "Error removing contract life",
            error=str(e),
            contract_id=contract_id,
            life_id=life_id,
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao remover vida do contrato",
        )


@router.get("/{contract_id}/lives/{life_id}/history", response_model=ContractLifeHistoryResponse)
@require_permission("contracts.view")
async def get_contract_life_history(
    contract_id: int,
    life_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Busca histórico completo de auditoria de uma vida

    **Retorna:**
    - Todos os eventos de mudança (created, updated, substituted, cancelled)
    - Campos alterados em cada evento
    - Valores antigos e novos
    - Informações do usuário que fez a mudança

    **Permissão necessária:** `contracts.view`
    """
    try:
        from sqlalchemy import select, text

        from app.infrastructure.orm.models import ContractLive, People
        from app.presentation.schemas.contract_lives import (
            ContractLifeHistoryEvent,
            ContractLifeHistoryResponse,
        )

        # Validar que vida existe e pertence ao contrato
        query = select(ContractLive, People.name.label("person_name")).join(
            People, ContractLive.person_id == People.id
        ).where(
            ContractLive.id == life_id,
            ContractLive.contract_id == contract_id
        )
        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Vida {life_id} não encontrada no contrato {contract_id}",
            )

        contract_life, person_name = row

        # Buscar histórico de auditoria
        history_query = text("""
            SELECT
                h.id,
                h.contract_life_id,
                h.action,
                h.changed_fields,
                h.old_values,
                h.new_values,
                h.changed_by,
                h.changed_at,
                u.full_name as changed_by_name
            FROM master.contract_lives_history h
            LEFT JOIN master.users u ON h.changed_by = u.id
            WHERE h.contract_life_id = :life_id
            ORDER BY h.changed_at DESC
        """)

        history_result = await db.execute(history_query, {"life_id": life_id})
        history_rows = history_result.fetchall()

        # Converter para lista de eventos
        events = []
        for row in history_rows:
            event = ContractLifeHistoryEvent(
                id=row.id,
                contract_life_id=row.contract_life_id,
                action=row.action,
                changed_fields=row.changed_fields,
                old_values=row.old_values,
                new_values=row.new_values,
                changed_by=row.changed_by,
                changed_by_name=row.changed_by_name,
                changed_at=row.changed_at,
            )
            events.append(event)

        logger.info(
            "Contract life history retrieved successfully",
            contract_id=contract_id,
            life_id=life_id,
            events_count=len(events),
            user_id=current_user.id,
        )

        return ContractLifeHistoryResponse(
            contract_life_id=life_id,
            person_name=person_name,
            events=events,
            total_events=len(events),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting contract life history",
            error=str(e),
            contract_id=contract_id,
            life_id=life_id,
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor ao buscar histórico: {str(e)}",
        )
