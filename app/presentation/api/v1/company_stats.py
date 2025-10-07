from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import Client, Establishments, Professional
from app.presentation.decorators.simple_permissions import require_permission

router = APIRouter()


@router.get("/{company_id}/stats")
@require_permission("companies_view", context_type="company")
async def get_company_stats(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obter estatísticas agregadas da empresa

    Retorna contadores de:
    - Estabelecimentos
    - Clientes (todos os estabelecimentos)
    - Profissionais (todos os estabelecimentos)
    """
    try:
        # Validar acesso à empresa
        if not current_user.is_system_admin and current_user.company_id != company_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # 1. Contar estabelecimentos
        establishments_query = select(func.count(Establishments.id)).where(
            and_(
                Establishments.company_id == company_id,
                Establishments.deleted_at.is_(None),
            )
        )
        establishments_result = await db.execute(establishments_query)
        establishments_count = establishments_result.scalar() or 0

        # 2. Contar clientes (via subquery de establishments)
        establishments_ids_query = select(Establishments.id).where(
            and_(
                Establishments.company_id == company_id,
                Establishments.deleted_at.is_(None),
            )
        )

        clients_query = select(func.count(Client.id)).where(
            and_(
                Client.establishment_id.in_(establishments_ids_query),
                Client.deleted_at.is_(None),
                Client.status == "active",  # Apenas ativos
            )
        )
        clients_result = await db.execute(clients_query)
        clients_count = clients_result.scalar() or 0

        # 3. Contar profissionais (via subquery de establishments)
        professionals_query = select(func.count(Professional.id)).where(
            and_(
                Professional.establishment_id.in_(establishments_ids_query),
                Professional.deleted_at.is_(None),
                Professional.status == "active",  # Apenas ativos
            )
        )
        professionals_result = await db.execute(professionals_query)
        professionals_count = professionals_result.scalar() or 0

        return {
            "company_id": company_id,
            "establishments_count": establishments_count,
            "clients_count": clients_count,
            "professionals_count": professionals_count,
            # "patients_count": 0,  # Implementar futuramente
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao carregar estatísticas")
