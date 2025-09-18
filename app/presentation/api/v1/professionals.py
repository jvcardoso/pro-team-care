from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.orm.models import Establishments, People, Professional
from app.infrastructure.services.security_service import get_security_service
from app.presentation.decorators.simple_permissions import (
    require_permission,
    require_professionals_view,
)
from app.presentation.schemas.user_schemas import (
    ProfessionalCreate,
    ProfessionalResponse,
    UserCompleteResponse,
)

router = APIRouter()
logger = get_logger()


async def get_current_user_schema(db=Depends(get_db)):
    """Get current user with complete data"""
    from app.infrastructure.auth import get_current_user as get_current_basic
    from app.infrastructure.orm.views import UserCompleteView

    user = await get_current_basic(db)

    query = select(UserCompleteView).where(UserCompleteView.user_id == user.id)
    result = await db.execute(query)
    user_complete = result.scalars().first()

    if not user_complete:
        raise HTTPException(status_code=404, detail="User data not found")

    return UserCompleteResponse.from_attributes(user_complete)


@router.post(
    "/", response_model=ProfessionalResponse, status_code=status.HTTP_201_CREATED
)
@require_permission("professionals.create", context_type="establishment")
async def create_professional(
    professional_data: ProfessionalCreate,
    db=Depends(get_db),
    security_service=Depends(get_security_service),
    current_user=Depends(get_current_user_schema),
):
    """Criar novo profissional"""
    try:
        # Verificar se pessoa física existe
        pf_person = await db.execute(
            select(People).where(People.id == professional_data.pf_person_id)
        )
        pf_person = pf_person.scalars().first()

        if not pf_person:
            raise HTTPException(status_code=404, detail="Pessoa física não encontrada")

        # Verificar se pessoa jurídica existe (se fornecida)
        if professional_data.pj_person_id:
            pj_person = await db.execute(
                select(People).where(People.id == professional_data.pj_person_id)
            )
            if not pj_person.scalars().first():
                raise HTTPException(
                    status_code=404, detail="Pessoa jurídica não encontrada"
                )

        # Verificar se estabelecimento existe
        establishment = await db.execute(
            select(Establishments).where(
                Establishments.id == professional_data.establishment_id
            )
        )
        if not establishment.scalars().first():
            raise HTTPException(
                status_code=404, detail="Estabelecimento não encontrado"
            )

        # Verificar se professional já existe para esta PF + estabelecimento
        existing = await db.execute(
            select(Professional).where(
                and_(
                    Professional.pf_person_id == professional_data.pf_person_id,
                    Professional.establishment_id == professional_data.establishment_id,
                    Professional.deleted_at.is_(None),
                )
            )
        )
        if existing.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Profissional já cadastrado neste estabelecimento",
            )

        # Criar professional
        professional = Professional(
            pf_person_id=professional_data.pf_person_id,
            pj_person_id=professional_data.pj_person_id,
            establishment_id=professional_data.establishment_id,
            professional_code=professional_data.professional_code,
            specialties=professional_data.specialties,
            admission_date=professional_data.admission_date,
            status="ACTIVE",
        )

        db.add(professional)
        await db.commit()
        await db.refresh(professional)

        # Buscar dados completos para retorno
        professional_query = (
            select(Professional)
            .options(
                selectinload(Professional.pf_person),
                selectinload(Professional.pj_person),
                selectinload(Professional.establishment),
            )
            .where(Professional.id == professional.id)
        )

        result = await db.execute(professional_query)
        created_professional = result.scalars().first()

        await logger.ainfo(
            "professional_created",
            professional_id=created_professional.id,
            pf_person_id=professional_data.pf_person_id,
            establishment_id=professional_data.establishment_id,
            created_by=current_user.user_id,
        )

        return ProfessionalResponse.from_attributes(created_professional)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror("professional_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/", response_model=List[ProfessionalResponse])
@require_professionals_view()
async def list_professionals(
    establishment_id: Optional[int] = Query(
        None, description="Filtrar por estabelecimento"
    ),
    status_filter: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Buscar por nome"),
    db=Depends(get_db),
    current_user=Depends(get_current_user_schema),
):
    """Listar profissionais com filtros"""
    try:
        query = select(Professional).options(
            selectinload(Professional.pf_person),
            selectinload(Professional.pj_person),
            selectinload(Professional.establishment),
        )

        # Aplicar filtros
        conditions = [Professional.deleted_at.is_(None)]

        if establishment_id:
            conditions.append(Professional.establishment_id == establishment_id)

        if status_filter:
            conditions.append(Professional.status == status_filter)

        if search:
            search_term = f"%{search.lower()}%"
            conditions.append(
                func.lower(Professional.pf_person.name).contains(search_term)
            )

        query = query.where(and_(*conditions))
        query = query.order_by(Professional.created_at.desc())

        result = await db.execute(query)
        professionals = result.scalars().all()

        await logger.ainfo(
            "professionals_listed",
            count=len(professionals),
            establishment_id=establishment_id,
            requested_by=current_user.user_id,
        )

        return [ProfessionalResponse.from_attributes(prof) for prof in professionals]

    except Exception as e:
        await logger.aerror("professionals_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/{professional_id}", response_model=ProfessionalResponse)
@require_professionals_view()
async def get_professional(
    professional_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user_schema),
):
    """Buscar profissional por ID"""
    try:
        query = (
            select(Professional)
            .options(
                selectinload(Professional.pf_person),
                selectinload(Professional.pj_person),
                selectinload(Professional.establishment),
            )
            .where(
                and_(
                    Professional.id == professional_id,
                    Professional.deleted_at.is_(None),
                )
            )
        )

        result = await db.execute(query)
        professional = result.scalars().first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        await logger.ainfo(
            "professional_retrieved",
            professional_id=professional_id,
            requested_by=current_user.user_id,
        )

        return ProfessionalResponse.from_attributes(professional)

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror(
            "professional_get_failed", professional_id=professional_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put("/{professional_id}", response_model=ProfessionalResponse)
@require_permission("professionals.edit", context_type="establishment")
async def update_professional(
    professional_id: int,
    professional_data: ProfessionalCreate,  # Reusing create schema for simplicity
    db=Depends(get_db),
    current_user=Depends(get_current_user_schema),
):
    """Atualizar profissional"""
    try:
        professional = await db.execute(
            select(Professional).where(
                and_(
                    Professional.id == professional_id,
                    Professional.deleted_at.is_(None),
                )
            )
        )
        professional = professional.scalars().first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Atualizar campos
        if professional_data.professional_code:
            professional.professional_code = professional_data.professional_code

        if professional_data.specialties:
            professional.specialties = professional_data.specialties

        if professional_data.admission_date:
            professional.admission_date = professional_data.admission_date

        await db.commit()
        await db.refresh(professional)

        await logger.ainfo(
            "professional_updated",
            professional_id=professional_id,
            updated_by=current_user.user_id,
        )

        return ProfessionalResponse.from_attributes(professional)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror(
            "professional_update_failed", professional_id=professional_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete("/{professional_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("professionals.delete", context_type="establishment")
async def delete_professional(
    professional_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user_schema),
):
    """Excluir profissional (soft delete)"""
    try:
        professional = await db.execute(
            select(Professional).where(Professional.id == professional_id)
        )
        professional = professional.scalars().first()

        if not professional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")

        # Soft delete
        from datetime import datetime

        professional.deleted_at = datetime.utcnow()
        professional.status = "INACTIVE"

        await db.commit()

        await logger.ainfo(
            "professional_deleted",
            professional_id=professional_id,
            deleted_by=current_user.user_id,
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        await logger.aerror(
            "professional_delete_failed", professional_id=professional_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
