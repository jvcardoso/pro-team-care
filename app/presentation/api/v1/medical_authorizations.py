"""API endpoints para autorizações médicas"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.logging import logger
from app.infrastructure.repositories.medical_authorization_repository import (
    MedicalAuthorizationRepository,
)
from app.presentation.decorators.role_permissions import (
    require_role_level_or_permission,
)
from app.presentation.schemas.medical_authorization import (
    AuthorizationHistoryResponse,
    AuthorizationRenewalResponse,
    AuthorizationRenewRequest,
    AuthorizationStatistics,
    AuthorizationStatusEnum,
    AuthorizationSuspendRequest,
    MedicalAuthorizationCancel,
    MedicalAuthorizationCreate,
    MedicalAuthorizationListParams,
    MedicalAuthorizationListResponse,
    MedicalAuthorizationResponse,
    MedicalAuthorizationUpdate,
    SessionUpdateRequest,
    UrgencyLevelEnum,
)
from app.presentation.schemas.user import UserDetailed as UserResponse

router = APIRouter(prefix="/medical-authorizations", tags=["medical-authorizations"])


@router.post("/", response_model=MedicalAuthorizationResponse)
@require_role_level_or_permission(3, "authorizations.create")
async def create_authorization(
    authorization_data: MedicalAuthorizationCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Criar nova autorização médica"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.create_authorization(
            authorization_data, created_by=current_user.id, company_id=company_id
        )

        logger.info(
            f"Autorização médica criada",
            extra={
                "authorization_id": authorization.id,
                "authorization_code": authorization.authorization_code,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return authorization

    except Exception as e:
        logger.error(f"Erro ao criar autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.get("/", response_model=MedicalAuthorizationListResponse)
@require_role_level_or_permission(3, "authorizations.view")
async def list_authorizations(
    contract_life_id: Optional[int] = Query(None),
    service_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[AuthorizationStatusEnum] = Query(None),
    urgency_level: Optional[UrgencyLevelEnum] = Query(None),
    valid_from: Optional[date] = Query(None),
    valid_until: Optional[date] = Query(None),
    requires_supervision: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Listar autorizações médicas com filtros"""
    try:
        params = MedicalAuthorizationListParams(
            contract_life_id=contract_life_id,
            service_id=service_id,
            doctor_id=doctor_id,
            status=status,
            urgency_level=urgency_level,
            valid_from=valid_from,
            valid_until=valid_until,
            requires_supervision=requires_supervision,
            page=page,
            size=size,
        )

        repo = MedicalAuthorizationRepository(db)
        authorizations, total = await repo.list_authorizations(params, company_id)

        # Convert to response format
        authorization_responses = []
        for auth in authorizations:
            auth_dict = {
                "id": auth.id,
                "contract_life_id": auth.contract_life_id,
                "service_id": auth.service_id,
                "doctor_id": auth.doctor_id,
                "authorization_code": auth.authorization_code,
                "authorization_date": auth.authorization_date,
                "valid_from": auth.valid_from,
                "valid_until": auth.valid_until,
                "sessions_authorized": auth.sessions_authorized,
                "sessions_remaining": auth.sessions_remaining,
                "monthly_limit": auth.monthly_limit,
                "weekly_limit": auth.weekly_limit,
                "daily_limit": auth.daily_limit,
                "medical_indication": auth.medical_indication,
                "contraindications": auth.contraindications,
                "special_instructions": auth.special_instructions,
                "urgency_level": auth.urgency_level,
                "requires_supervision": auth.requires_supervision,
                "supervision_notes": auth.supervision_notes,
                "diagnosis_cid": auth.diagnosis_cid,
                "diagnosis_description": auth.diagnosis_description,
                "treatment_goals": auth.treatment_goals,
                "expected_duration_days": auth.expected_duration_days,
                "renewal_allowed": auth.renewal_allowed,
                "renewal_conditions": auth.renewal_conditions,
                "status": auth.status,
                "cancellation_reason": auth.cancellation_reason,
                "cancelled_at": auth.cancelled_at,
                "cancelled_by": auth.cancelled_by,
                "created_at": auth.created_at,
                "updated_at": auth.updated_at,
                "created_by": auth.created_by,
                "updated_by": auth.updated_by,
                # Related data
                "service_name": auth.service.service_name if auth.service else None,
                "service_category": (
                    auth.service.service_category if auth.service else None
                ),
                "service_type": auth.service.service_type if auth.service else None,
                "doctor_name": (
                    auth.doctor.person.name
                    if auth.doctor and auth.doctor.person
                    else auth.doctor.email_address if auth.doctor else None
                ),
                "doctor_email": auth.doctor.email_address if auth.doctor else None,
                "patient_name": (
                    auth.contract_life.person.name
                    if auth.contract_life and auth.contract_life.person
                    else None
                ),
                "contract_number": (
                    auth.contract_life.contract.contract_number
                    if auth.contract_life and auth.contract_life.contract
                    else None
                ),
            }
            authorization_responses.append(MedicalAuthorizationResponse(**auth_dict))

        return MedicalAuthorizationListResponse(
            authorizations=authorization_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    except Exception as e:
        logger.error(f"Erro ao listar autorizações médicas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.get("/{authorization_id}", response_model=MedicalAuthorizationResponse)
@require_role_level_or_permission(3, "authorizations.view")
async def get_authorization(
    authorization_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Buscar autorização médica por ID"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.get_authorization(authorization_id, company_id)

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        # Convert to response format
        auth_dict = {
            "id": authorization.id,
            "contract_life_id": authorization.contract_life_id,
            "service_id": authorization.service_id,
            "doctor_id": authorization.doctor_id,
            "authorization_code": authorization.authorization_code,
            "authorization_date": authorization.authorization_date,
            "valid_from": authorization.valid_from,
            "valid_until": authorization.valid_until,
            "sessions_authorized": authorization.sessions_authorized,
            "sessions_remaining": authorization.sessions_remaining,
            "monthly_limit": authorization.monthly_limit,
            "weekly_limit": authorization.weekly_limit,
            "daily_limit": authorization.daily_limit,
            "medical_indication": authorization.medical_indication,
            "contraindications": authorization.contraindications,
            "special_instructions": authorization.special_instructions,
            "urgency_level": authorization.urgency_level,
            "requires_supervision": authorization.requires_supervision,
            "supervision_notes": authorization.supervision_notes,
            "diagnosis_cid": authorization.diagnosis_cid,
            "diagnosis_description": authorization.diagnosis_description,
            "treatment_goals": authorization.treatment_goals,
            "expected_duration_days": authorization.expected_duration_days,
            "renewal_allowed": authorization.renewal_allowed,
            "renewal_conditions": authorization.renewal_conditions,
            "status": authorization.status,
            "cancellation_reason": authorization.cancellation_reason,
            "cancelled_at": authorization.cancelled_at,
            "cancelled_by": authorization.cancelled_by,
            "created_at": authorization.created_at,
            "updated_at": authorization.updated_at,
            "created_by": authorization.created_by,
            "updated_by": authorization.updated_by,
            # Related data
            "service_name": (
                authorization.service.service_name if authorization.service else None
            ),
            "service_category": (
                authorization.service.service_category
                if authorization.service
                else None
            ),
            "service_type": (
                authorization.service.service_type if authorization.service else None
            ),
            "doctor_name": (
                authorization.doctor.person.name
                if authorization.doctor and authorization.doctor.person
                else (
                    authorization.doctor.email_address if authorization.doctor else None
                )
            ),
            "doctor_email": (
                authorization.doctor.email_address if authorization.doctor else None
            ),
            "patient_name": (
                authorization.contract_life.person.name
                if authorization.contract_life and authorization.contract_life.person
                else None
            ),
            "contract_number": (
                authorization.contract_life.contract.contract_number
                if authorization.contract_life and authorization.contract_life.contract
                else None
            ),
        }

        return MedicalAuthorizationResponse(**auth_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.put("/{authorization_id}", response_model=MedicalAuthorizationResponse)
@require_role_level_or_permission(3, "authorizations.edit")
async def update_authorization(
    authorization_id: int,
    update_data: MedicalAuthorizationUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Atualizar autorização médica"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.update_authorization(
            authorization_id,
            update_data,
            updated_by=current_user.id,
            company_id=company_id,
        )

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        logger.info(
            f"Autorização médica atualizada",
            extra={
                "authorization_id": authorization_id,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return authorization

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.post("/{authorization_id}/cancel", response_model=MedicalAuthorizationResponse)
@require_role_level_or_permission(3, "authorizations.cancel")
async def cancel_authorization(
    authorization_id: int,
    cancel_data: MedicalAuthorizationCancel,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Cancelar autorização médica"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.cancel_authorization(
            authorization_id,
            cancel_data.cancellation_reason,
            cancelled_by=current_user.id,
            company_id=company_id,
        )

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        logger.info(
            f"Autorização médica cancelada",
            extra={
                "authorization_id": authorization_id,
                "reason": cancel_data.cancellation_reason,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return authorization

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.post("/{authorization_id}/suspend", response_model=MedicalAuthorizationResponse)
@require_role_level_or_permission(3, "authorizations.suspend")
async def suspend_authorization(
    authorization_id: int,
    suspend_data: AuthorizationSuspendRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Suspender autorização médica"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.suspend_authorization(
            authorization_id,
            suspend_data,
            suspended_by=current_user.id,
            company_id=company_id,
        )

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        logger.info(
            f"Autorização médica suspensa",
            extra={
                "authorization_id": authorization_id,
                "reason": suspend_data.reason,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return authorization

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao suspender autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.post(
    "/{authorization_id}/update-sessions", response_model=MedicalAuthorizationResponse
)
@require_role_level_or_permission(3, "authorizations.use_sessions")
async def update_sessions(
    authorization_id: int,
    session_update: SessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Atualizar sessões utilizadas"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorization = await repo.update_sessions(
            authorization_id,
            session_update,
            updated_by=current_user.id,
            company_id=company_id,
        )

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        logger.info(
            f"Sessões atualizadas na autorização",
            extra={
                "authorization_id": authorization_id,
                "sessions_used": session_update.sessions_used,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return authorization

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar sessões: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.post("/{authorization_id}/renew", response_model=dict)
@require_role_level_or_permission(3, "authorizations.renew")
async def renew_authorization(
    authorization_id: int,
    renew_data: AuthorizationRenewRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Renovar autorização médica"""
    try:
        repo = MedicalAuthorizationRepository(db)
        result = await repo.renew_authorization(
            authorization_id,
            renew_data,
            approved_by=current_user.id,
            company_id=company_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Autorização não encontrada",
            )

        new_authorization, renewal = result

        logger.info(
            f"Autorização médica renovada",
            extra={
                "original_authorization_id": authorization_id,
                "new_authorization_id": new_authorization.id,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )

        return {
            "message": "Autorização renovada com sucesso",
            "new_authorization_id": new_authorization.id,
            "new_authorization_code": new_authorization.authorization_code,
            "renewal_id": renewal.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao renovar autorização médica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.get(
    "/{authorization_id}/history", response_model=List[AuthorizationHistoryResponse]
)
@require_role_level_or_permission(3, "authorizations.view_history")
async def get_authorization_history(
    authorization_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Buscar histórico de uma autorização"""
    try:
        repo = MedicalAuthorizationRepository(db)
        history = await repo.get_authorization_history(authorization_id, company_id)

        return [
            AuthorizationHistoryResponse(
                id=h.id,
                authorization_id=h.authorization_id,
                action=h.action,
                field_changed=h.field_changed,
                old_value=h.old_value,
                new_value=h.new_value,
                reason=h.reason,
                performed_by=h.performed_by,
                performed_at=h.performed_at,
                ip_address=h.ip_address,
                user_agent=h.user_agent,
                performed_by_name=(
                    h.performed_by_user.person.name
                    if h.performed_by_user and h.performed_by_user.person
                    else (
                        h.performed_by_user.email_address
                        if h.performed_by_user
                        else None
                    )
                ),
            )
            for h in history
        ]

    except Exception as e:
        logger.error(f"Erro ao buscar histórico da autorização: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.get("/statistics/overview", response_model=AuthorizationStatistics)
@require_role_level_or_permission(3, "authorizations.view_statistics")
async def get_authorization_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Obter estatísticas de autorizações"""
    try:
        repo = MedicalAuthorizationRepository(db)
        stats = await repo.get_authorization_statistics(
            company_id=company_id, start_date=start_date, end_date=end_date
        )

        return AuthorizationStatistics(**stats)

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de autorizações: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )


@router.get("/expiring/soon", response_model=List[MedicalAuthorizationResponse])
@require_role_level_or_permission(3, "authorizations.view")
async def get_expiring_authorizations(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
    company_id: Optional[int] = None,
):
    """Buscar autorizações que vencem em breve"""
    try:
        repo = MedicalAuthorizationRepository(db)
        authorizations = await repo.get_authorizations_expiring_soon(days, company_id)

        return [
            MedicalAuthorizationResponse(
                id=auth.id,
                contract_life_id=auth.contract_life_id,
                service_id=auth.service_id,
                doctor_id=auth.doctor_id,
                authorization_code=auth.authorization_code,
                authorization_date=auth.authorization_date,
                valid_from=auth.valid_from,
                valid_until=auth.valid_until,
                sessions_authorized=auth.sessions_authorized,
                sessions_remaining=auth.sessions_remaining,
                monthly_limit=auth.monthly_limit,
                weekly_limit=auth.weekly_limit,
                daily_limit=auth.daily_limit,
                medical_indication=auth.medical_indication,
                contraindications=auth.contraindications,
                special_instructions=auth.special_instructions,
                urgency_level=auth.urgency_level,
                requires_supervision=auth.requires_supervision,
                supervision_notes=auth.supervision_notes,
                diagnosis_cid=auth.diagnosis_cid,
                diagnosis_description=auth.diagnosis_description,
                treatment_goals=auth.treatment_goals,
                expected_duration_days=auth.expected_duration_days,
                renewal_allowed=auth.renewal_allowed,
                renewal_conditions=auth.renewal_conditions,
                status=auth.status,
                cancellation_reason=auth.cancellation_reason,
                cancelled_at=auth.cancelled_at,
                cancelled_by=auth.cancelled_by,
                created_at=auth.created_at,
                updated_at=auth.updated_at,
                created_by=auth.created_by,
                updated_by=auth.updated_by,
                service_name=auth.service.service_name if auth.service else None,
                service_category=(
                    auth.service.service_category if auth.service else None
                ),
                service_type=auth.service.service_type if auth.service else None,
                doctor_name=(
                    auth.doctor.person.name
                    if auth.doctor and auth.doctor.person
                    else auth.doctor.email_address if auth.doctor else None
                ),
                doctor_email=auth.doctor.email_address if auth.doctor else None,
                patient_name=(
                    auth.contract_life.person.name
                    if auth.contract_life and auth.contract_life.person
                    else None
                ),
                contract_number=(
                    auth.contract_life.contract.contract_number
                    if auth.contract_life and auth.contract_life.contract
                    else None
                ),
            )
            for auth in authorizations
        ]

    except Exception as e:
        logger.error(f"Erro ao buscar autorizações expirando: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )
