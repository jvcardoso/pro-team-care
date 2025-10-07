"""
API endpoints para sistema de controle de limites automático
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.repositories.limits_repository import LimitsRepository
from app.presentation.decorators.role_permissions import (
    require_role_level_or_permission,
)
from app.presentation.schemas.limits import (  # Limits Configuration; Service Usage Tracking; Limits Violations; Alerts; Business Logic; Enums
    AlertsConfiguration,
    AlertsConfigurationCreate,
    AlertsConfigurationUpdate,
    AlertSeverity,
    AlertsLog,
    AlertsLogCreate,
    AlertsLogListParams,
    AlertsLogListResponse,
    AlertType,
    CheckLimitsRequest,
    CheckLimitsResponse,
    EntityType,
    ExpiringAuthorizationAlert,
    LimitsConfiguration,
    LimitsConfigurationCreate,
    LimitsConfigurationListParams,
    LimitsConfigurationListResponse,
    LimitsConfigurationUpdate,
    LimitsDashboard,
    LimitsViolation,
    LimitsViolationCreate,
    LimitsViolationListParams,
    LimitsViolationListResponse,
    LimitType,
    ServiceUsageTracking,
    ServiceUsageTrackingCreate,
    ServiceUsageTrackingListParams,
    ServiceUsageTrackingListResponse,
    UsageStatistics,
    ViolationType,
)

router = APIRouter(prefix="/limits-control", tags=["Limits Control"])
logger = logging.getLogger(__name__)


# === UTILITY FUNCTIONS ===


def get_limits_repository(db: AsyncSession = Depends(get_db)) -> LimitsRepository:
    """Factory para repository de limites"""
    return LimitsRepository(db)


def calculate_pages(total: int, size: int) -> int:
    """Calcular número total de páginas"""
    return (total + size - 1) // size


# === LIMITS CONFIGURATION ENDPOINTS ===


@router.post("/configurations/", response_model=LimitsConfiguration)
@require_role_level_or_permission(80, "limits_config.create")
async def create_limits_configuration(
    data: LimitsConfigurationCreate,
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Criar nova configuração de limite"""
    try:
        config = await repo.create_limits_config(**data.dict())
        logger.info(f"Configuração de limite criada: {config.id}")
        return config
    except Exception as e:
        logger.error(f"Erro ao criar configuração de limite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar configuração de limite",
        )


@router.get("/configurations/", response_model=LimitsConfigurationListResponse)
@require_role_level_or_permission(50, "limits_config.view")
async def list_limits_configurations(
    limit_type: Optional[LimitType] = Query(None),
    entity_type: Optional[EntityType] = Query(None),
    entity_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Listar configurações de limite"""
    try:
        configs, total = await repo.list_limits_configs(
            limit_type=limit_type,
            entity_type=entity_type,
            entity_id=entity_id,
            is_active=is_active,
            page=page,
            size=size,
        )

        return LimitsConfigurationListResponse(
            configurations=configs,
            total=total,
            page=page,
            size=size,
            pages=calculate_pages(total, size),
        )
    except Exception as e:
        logger.error(f"Erro ao listar configurações de limite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar configurações",
        )


@router.get("/configurations/{config_id}", response_model=LimitsConfiguration)
@require_role_level_or_permission(50, "limits_config.view")
async def get_limits_configuration(
    config_id: int, repo: LimitsRepository = Depends(get_limits_repository)
):
    """Buscar configuração de limite por ID"""
    config = await repo.get_limits_config(config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de limite não encontrada",
        )
    return config


@router.put("/configurations/{config_id}", response_model=LimitsConfiguration)
@require_role_level_or_permission(80, "limits_config.update")
async def update_limits_configuration(
    config_id: int,
    data: LimitsConfigurationUpdate,
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Atualizar configuração de limite"""
    try:
        config = await repo.update_limits_config(
            config_id, **data.dict(exclude_unset=True)
        )
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de limite não encontrada",
            )

        logger.info(f"Configuração de limite atualizada: {config_id}")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração de limite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar configuração",
        )


# === SERVICE USAGE TRACKING ENDPOINTS ===


@router.post("/usage/track", response_model=ServiceUsageTracking)
@require_role_level_or_permission(30, "service_usage.create")
async def track_service_usage(
    data: ServiceUsageTrackingCreate,
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Registrar uso de serviço"""
    try:
        usage = await repo.track_service_usage(**data.dict())
        logger.info(f"Uso de serviço registrado: {usage.id}")
        return usage
    except Exception as e:
        logger.error(f"Erro ao registrar uso de serviço: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar uso",
        )


@router.get("/usage/statistics", response_model=UsageStatistics)
@require_role_level_or_permission(50, "service_usage.view")
async def get_usage_statistics(
    authorization_id: Optional[int] = Query(None),
    contract_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Obter estatísticas de uso"""
    try:
        stats = await repo.get_usage_statistics(
            authorization_id=authorization_id,
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date,
        )

        return UsageStatistics(
            total_executions=stats["total_executions"],
            total_sessions=stats["total_sessions"],
            avg_sessions_per_execution=stats["avg_sessions_per_execution"],
            period_start=start_date,
            period_end=end_date,
        )
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de uso: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter estatísticas",
        )


# === LIMITS VIOLATIONS ENDPOINTS ===


@router.post("/violations/", response_model=LimitsViolation)
@require_role_level_or_permission(30, "limits_violations.create")
async def create_violation(
    data: LimitsViolationCreate, repo: LimitsRepository = Depends(get_limits_repository)
):
    """Registrar violação de limite"""
    try:
        violation = await repo.create_violation(**data.dict())
        logger.warning(
            f"Violação de limite registrada: {violation.id} - {violation.violation_type}"
        )
        return violation
    except Exception as e:
        logger.error(f"Erro ao registrar violação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao registrar violação",
        )


@router.get("/violations/", response_model=LimitsViolationListResponse)
@require_role_level_or_permission(50, "limits_violations.view")
async def list_violations(
    authorization_id: Optional[int] = Query(None),
    violation_type: Optional[ViolationType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Listar violações de limite"""
    try:
        violations, total = await repo.list_violations(
            authorization_id=authorization_id,
            violation_type=violation_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
        )

        return LimitsViolationListResponse(
            violations=violations,
            total=total,
            page=page,
            size=size,
            pages=calculate_pages(total, size),
        )
    except Exception as e:
        logger.error(f"Erro ao listar violações: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar violações",
        )


# === ALERTS ENDPOINTS ===


@router.post("/alerts/configurations/", response_model=AlertsConfiguration)
@require_role_level_or_permission(80, "alerts_config.create")
async def create_alert_configuration(
    data: AlertsConfigurationCreate,
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Criar configuração de alerta"""
    try:
        config = await repo.create_alert_config(**data.dict())
        logger.info(f"Configuração de alerta criada: {config.id}")
        return config
    except Exception as e:
        logger.error(f"Erro ao criar configuração de alerta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar configuração de alerta",
        )


@router.get("/alerts/logs/", response_model=AlertsLogListResponse)
@require_role_level_or_permission(50, "alerts_log.view")
async def list_alert_logs(
    entity_id: Optional[int] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Listar logs de alerta"""
    try:
        logs, total = await repo.list_alert_logs(
            entity_id=entity_id,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
        )

        return AlertsLogListResponse(
            logs=logs,
            total=total,
            page=page,
            size=size,
            pages=calculate_pages(total, size),
        )
    except Exception as e:
        logger.error(f"Erro ao listar logs de alerta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar logs",
        )


# === BUSINESS LOGIC ENDPOINTS ===


@router.post("/check-authorization-limits/", response_model=CheckLimitsResponse)
@require_role_level_or_permission(30, "limits_check.execute")
async def check_authorization_limits(
    data: CheckLimitsRequest, repo: LimitsRepository = Depends(get_limits_repository)
):
    """Verificar limites de autorização"""
    try:
        result = await repo.check_authorization_limits(
            authorization_id=data.authorization_id,
            sessions_to_use=data.sessions_to_use,
            execution_date=data.execution_date,
        )

        logger.info(
            f"Verificação de limites executada para autorização {data.authorization_id}"
        )
        return CheckLimitsResponse(**result)
    except Exception as e:
        logger.error(f"Erro ao verificar limites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao verificar limites",
        )


@router.get("/check-contract-limits/{contract_id}")
@require_role_level_or_permission(30, "limits_check.execute")
async def check_contract_limits(
    contract_id: int,
    current_month: Optional[date] = Query(None),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Verificar limites de contrato"""
    try:
        result = await repo.check_contract_limits(
            contract_id=contract_id, current_month=current_month
        )

        logger.info(f"Verificação de limites de contrato executada: {contract_id}")
        return result
    except Exception as e:
        logger.error(f"Erro ao verificar limites de contrato: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao verificar limites de contrato",
        )


@router.get("/expiring-authorizations/")
@require_role_level_or_permission(50, "authorization_alerts.view")
async def get_expiring_authorizations(
    days_ahead: int = Query(7, ge=1, le=30),
    company_id: Optional[int] = Query(None),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Buscar autorizações que vencem em breve"""
    try:
        authorizations = await repo.get_expiring_authorizations(
            days_ahead=days_ahead, company_id=company_id
        )

        return authorizations
    except Exception as e:
        logger.error(f"Erro ao buscar autorizações expirando: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar autorizações expirando",
        )


@router.get("/dashboard/", response_model=LimitsDashboard)
@require_role_level_or_permission(50, "limits_dashboard.view")
async def get_limits_dashboard(
    company_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    repo: LimitsRepository = Depends(get_limits_repository),
):
    """Obter dados para dashboard de limites"""
    try:
        dashboard_data = await repo.get_limits_dashboard(
            company_id=company_id, start_date=start_date, end_date=end_date
        )

        # Buscar autorizações expirando
        expiring = await repo.get_expiring_authorizations(
            days_ahead=7, company_id=company_id
        )

        # Buscar violações recentes
        recent_violations, _ = await repo.list_violations(
            start_date=datetime.now().replace(hour=0, minute=0, second=0),
            page=1,
            size=10,
        )

        dashboard_data["expiring_authorizations"] = expiring
        dashboard_data["recent_violations"] = recent_violations

        return LimitsDashboard(**dashboard_data)
    except Exception as e:
        logger.error(f"Erro ao obter dashboard de limites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter dashboard",
        )
