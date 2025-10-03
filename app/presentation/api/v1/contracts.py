from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.contract_repository import ContractRepository, ServicesRepository
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
    ServicesListParams,
    ServicesListResponse,
    ServicesCatalogResponse,
)

logger = structlog.get_logger()

router = APIRouter()


@router.post("/", response_model=ContractResponse, status_code=http_status.HTTP_201_CREATED)
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
        logger.error("Error creating contract", error=str(e), contract_data=contract_data.model_dump())
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao criar contrato"
        )


@router.get("/test", response_model=dict)
async def test_contracts_endpoint(db=Depends(get_db)):
    """Test endpoint to check if contracts table is accessible"""
    try:
        from sqlalchemy import text

        result = await db.execute(text("SELECT COUNT(*) as count FROM master.contracts"))
        count = result.scalar()
        return {"contracts_table_exists": True, "contracts_count": count}
    except Exception as e:
        return {"contracts_table_exists": False, "error": str(e)}

@router.get("/", response_model=ContractListResponse)
@require_permission("contracts.view")
async def list_contracts(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    contract_status: Optional[ContractStatus] = Query(None, description="Filter by contract status"),
    contract_type: Optional[ContractType] = Query(None, description="Filter by contract type"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List contracts with filtering and pagination"""
    try:
        logger.info("Starting contracts list request", client_id=client_id, status=contract_status, contract_type=contract_type)
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
            logger.info("Converting contracts to response models", contracts_count=len(result["contracts"]))
            if result["contracts"]:
                logger.info("First contract data", contract_data=result["contracts"][0].__dict__ if hasattr(result["contracts"][0], '__dict__') else str(result["contracts"][0]))
            contracts_response = [
                ContractResponse.model_validate(contract) for contract in result["contracts"]
            ]
            logger.info("Conversion completed successfully")
        except Exception as e:
            logger.error("Error converting contracts to response models", error=str(e), error_type=type(e).__name__)
            raise

        logger.info(
            "Contracts listed successfully",
            total=result["total"],
            page=page,
            size=size,
            filters={"client_id": client_id, "status": contract_status, "contract_type": contract_type},
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
            detail="Erro interno do servidor ao listar contratos"
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
                detail="Contrato não encontrado"
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
            detail="Erro interno do servidor ao buscar contrato"
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
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        if not update_dict:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar foi fornecido"
            )

        contract = await contract_repo.update_contract(contract_id, update_dict)

        if not contract:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
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
            detail="Erro interno do servidor ao atualizar contrato"
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
                detail="Contrato não encontrado"
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
            detail="Erro interno do servidor ao deletar contrato"
        )


@router.get("/count/", response_model=dict)
@require_permission("contracts.view")
async def count_contracts(
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    status: Optional[ContractStatus] = Query(None, description="Filter by contract status"),
    contract_type: Optional[ContractType] = Query(None, description="Filter by contract type"),
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
            filters={"client_id": client_id, "status": status, "contract_type": contract_type},
            user_id=current_user.id,
        )

        return {"count": result["total"]}

    except Exception as e:
        logger.error("Error counting contracts", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao contar contratos"
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
            ServicesCatalogResponse.model_validate(service) for service in result["services"]
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
            detail="Erro interno do servidor ao listar catálogo de serviços"
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
                detail="Serviço não encontrado"
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
            detail="Erro interno do servidor ao buscar serviço"
        )


# ==========================================
# CONTRACT LIVES ENDPOINTS
# ==========================================

@router.get("/{contract_id}/lives", response_model=list)
@require_permission("contracts.view")
async def list_contract_lives(
    contract_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List lives for a specific contract"""
    try:
        from sqlalchemy import select
        from app.infrastructure.orm.models import ContractLive, People

        query = (
            select(ContractLive, People.name.label("person_name"), People.tax_id.label("person_cpf"))
            .join(People, ContractLive.person_id == People.id)
            .where(ContractLive.contract_id == contract_id)
            .order_by(ContractLive.start_date.desc())
        )

        result = await db.execute(query)
        lives_data = result.all()

        lives = []
        for live, person_name, person_cpf in lives_data:
            lives.append({
                "id": live.id,
                "contract_id": live.contract_id,
                "person_id": live.person_id,
                "person_name": person_name,
                "person_cpf": person_cpf,
                "start_date": live.start_date.isoformat() if live.start_date else None,
                "end_date": live.end_date.isoformat() if live.end_date else None,
                "status": live.status,
                "relationship_type": live.relationship_type,
                "substitution_allowed": True,  # Default for now
                "notes": live.substitution_reason,
                "created_at": live.created_at.isoformat() if live.created_at else None,
                "updated_at": live.updated_at.isoformat() if live.updated_at else None,
            })

        logger.info(
            "Contract lives listed successfully",
            contract_id=contract_id,
            lives_count=len(lives),
            user_id=current_user.id,
        )

        return lives

    except Exception as e:
        logger.error("Error listing contract lives", error=str(e), contract_id=contract_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao listar vidas do contrato"
        )


@router.post("/{contract_id}/lives", response_model=dict)
@require_permission("contracts.lives.manage")
async def add_contract_life(
    contract_id: int,
    life_data: dict,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new life to a contract"""
    try:
        from sqlalchemy import select
        from app.infrastructure.orm.models import ContractLive, People, Contract
        from datetime import datetime

        # Validate contract exists
        contract_query = select(Contract).where(Contract.id == contract_id)
        contract_result = await db.execute(contract_query)
        contract = contract_result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado"
            )

        # Check if person exists or create one
        person_name = life_data.get("person_name")
        if not person_name:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Nome da pessoa é obrigatório"
            )

        # For now, create a simple person record (in real app, this would be more sophisticated)
        person_query = select(People).where(People.name == person_name)
        person_result = await db.execute(person_query)
        person = person_result.scalar_one_or_none()

        if not person:
            # Create new person - simplified for now
            person = People(
                name=person_name,
                person_type="PF",
                status="active",
                company_id=1,  # Default company - in real app, this would come from context
                tax_id=f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",  # Temporary tax_id
            )
            db.add(person)
            await db.flush()
            await db.refresh(person)

        # Create contract life
        contract_life = ContractLive(
            contract_id=contract_id,
            person_id=person.id,
            start_date=datetime.fromisoformat(life_data.get("start_date")).date(),
            end_date=datetime.fromisoformat(life_data.get("end_date")).date() if life_data.get("end_date") else None,
            relationship_type=life_data.get("relationship_type", "FUNCIONARIO"),
            status="active",
            substitution_reason=life_data.get("notes"),
            created_by=current_user.id,
        )

        db.add(contract_life)
        await db.commit()
        await db.refresh(contract_life)

        logger.info(
            "Contract life added successfully",
            contract_id=contract_id,
            life_id=contract_life.id,
            person_name=person_name,
            user_id=current_user.id,
        )

        return {
            "id": contract_life.id,
            "message": f"{person_name} adicionado ao contrato com sucesso"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error adding contract life", error=str(e), contract_id=contract_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao adicionar vida ao contrato"
        )


@router.put("/{contract_id}/lives/{life_id}", response_model=dict)
@require_permission("contracts.lives.manage")
async def update_contract_life(
    contract_id: int,
    life_id: int,
    life_data: dict,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update or substitute a contract life"""
    try:
        from sqlalchemy import select, update
        from app.infrastructure.orm.models import ContractLive
        from datetime import datetime

        # Find the life to update
        query = select(ContractLive).where(
            ContractLive.id == life_id,
            ContractLive.contract_id == contract_id
        )
        result = await db.execute(query)
        contract_life = result.scalar_one_or_none()

        if not contract_life:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Vida do contrato não encontrada"
            )

        # Update the life
        update_data = {}
        if "end_date" in life_data:
            update_data["end_date"] = datetime.fromisoformat(life_data["end_date"]).date() if life_data["end_date"] else None
        if "status" in life_data:
            update_data["status"] = life_data["status"]
        if "relationship_type" in life_data:
            update_data["relationship_type"] = life_data["relationship_type"]
        if "substitution_reason" in life_data:
            update_data["substitution_reason"] = life_data["substitution_reason"]
        if "primary_service_address" in life_data:
            update_data["primary_service_address"] = life_data["primary_service_address"]

        update_data["updated_at"] = datetime.utcnow()
        # Note: updated_by field doesn't exist in contract_lives table based on database structure

        stmt = (
            update(ContractLive)
            .where(ContractLive.id == life_id)
            .values(**update_data)
        )

        await db.execute(stmt)
        await db.commit()

        logger.info(
            "Contract life updated successfully",
            contract_id=contract_id,
            life_id=life_id,
            user_id=current_user.id,
        )

        return {"message": "Vida do contrato atualizada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error updating contract life", error=str(e), contract_id=contract_id, life_id=life_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao atualizar vida do contrato"
        )


@router.delete("/{contract_id}/lives/{life_id}", status_code=http_status.HTTP_204_NO_CONTENT)
@require_permission("contracts.lives.manage")
async def remove_contract_life(
    contract_id: int,
    life_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove (terminate) a life from contract"""
    try:
        from sqlalchemy import select, update
        from app.infrastructure.orm.models import ContractLive
        from datetime import datetime

        # Find the life to remove
        query = select(ContractLive).where(
            ContractLive.id == life_id,
            ContractLive.contract_id == contract_id
        )
        result = await db.execute(query)
        contract_life = result.scalar_one_or_none()

        if not contract_life:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Vida do contrato não encontrada"
            )

        # Terminate the life (soft delete)
        stmt = (
            update(ContractLive)
            .where(ContractLive.id == life_id)
            .values(
                status="cancelled",
                end_date=datetime.utcnow().date(),
                updated_at=datetime.utcnow()
                # Note: updated_by field doesn't exist in contract_lives table
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
        logger.error("Error removing contract life", error=str(e), contract_id=contract_id, life_id=life_id)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao remover vida do contrato"
        )