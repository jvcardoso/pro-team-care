"""
API endpoints para dashboard executivo de contratos home care
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.services.contract_dashboard_service import ContractDashboardService
from app.presentation.decorators.role_permissions import require_role_level_or_permission

router = APIRouter(prefix="/contract-dashboard", tags=["Contract Dashboard"])
logger = logging.getLogger(__name__)


# === UTILITY FUNCTIONS ===

def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> ContractDashboardService:
    """Factory para dashboard service"""
    return ContractDashboardService(db)


# === DASHBOARD ENDPOINTS ===

@router.get("/executive/{contract_id}")
@require_role_level_or_permission(50, "contract_dashboard.view")
async def get_executive_dashboard(
    contract_id: int,
    start_date: Optional[date] = Query(None, description="Data início período (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data fim período (YYYY-MM-DD)"),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Dashboard executivo completo para um contrato específico"""
    try:
        dashboard_data = await service.get_executive_dashboard(
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date
        )

        if not dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contrato {contract_id} não encontrado"
            )

        logger.info(f"Dashboard executivo obtido para contrato {contract_id}")
        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter dashboard executivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter dashboard executivo"
        )


@router.get("/financial/{contract_id}")
@require_role_level_or_permission(60, "contract_financial.view")
async def get_financial_metrics(
    contract_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Métricas financeiras detalhadas do contrato"""
    try:
        financial_data = await service.get_financial_metrics(
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Métricas financeiras obtidas para contrato {contract_id}")
        return financial_data

    except Exception as e:
        logger.error(f"Erro ao obter métricas financeiras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter métricas financeiras"
        )


@router.get("/services/{contract_id}")
@require_role_level_or_permission(50, "contract_services.view")
async def get_service_metrics(
    contract_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Métricas de execução de serviços do contrato"""
    try:
        service_data = await service.get_service_execution_metrics(
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Métricas de serviço obtidas para contrato {contract_id}")
        return service_data

    except Exception as e:
        logger.error(f"Erro ao obter métricas de serviço: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter métricas de serviço"
        )


@router.get("/quality/{contract_id}")
@require_role_level_or_permission(50, "contract_quality.view")
async def get_quality_metrics(
    contract_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Métricas de qualidade e satisfação do contrato"""
    try:
        quality_data = await service.get_quality_satisfaction_metrics(
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Métricas de qualidade obtidas para contrato {contract_id}")
        return quality_data

    except Exception as e:
        logger.error(f"Erro ao obter métricas de qualidade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter métricas de qualidade"
        )


@router.get("/limits-status/{contract_id}")
@require_role_level_or_permission(50, "contract_limits.view")
async def get_limits_status(
    contract_id: int,
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Status atual dos limites do contrato"""
    try:
        limits_data = await service.get_limits_status(contract_id=contract_id)

        logger.info(f"Status de limites obtido para contrato {contract_id}")
        return limits_data

    except Exception as e:
        logger.error(f"Erro ao obter status de limites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter status de limites"
        )


@router.get("/alerts/{contract_id}")
@require_role_level_or_permission(50, "contract_alerts.view")
async def get_contract_alerts(
    contract_id: int,
    days_ahead: int = Query(7, ge=1, le=30, description="Dias para alertas futuros"),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Alertas e notificações do contrato"""
    try:
        alerts_data = await service.get_contract_alerts(
            contract_id=contract_id,
            days_ahead=days_ahead
        )

        logger.info(f"Alertas obtidos para contrato {contract_id}")
        return alerts_data

    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter alertas"
        )


@router.get("/usage-trends/{contract_id}")
@require_role_level_or_permission(50, "contract_usage.view")
async def get_usage_trends(
    contract_id: int,
    months_back: int = Query(6, ge=1, le=24, description="Meses históricos para análise"),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Tendências de uso histórico do contrato"""
    try:
        trends_data = await service.get_usage_trends(
            contract_id=contract_id,
            months_back=months_back
        )

        logger.info(f"Tendências de uso obtidas para contrato {contract_id}")
        return trends_data

    except Exception as e:
        logger.error(f"Erro ao obter tendências de uso: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao obter tendências"
        )


# === COMPARATIVE ENDPOINTS ===

@router.get("/compare/contracts")
@require_role_level_or_permission(70, "contracts_compare.view")
async def compare_contracts(
    contract_ids: str = Query(..., description="IDs dos contratos separados por vírgula (ex: 1,2,3)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Comparação entre múltiplos contratos"""
    try:
        # Validar e converter IDs
        try:
            contract_ids_list = [int(id.strip()) for id in contract_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IDs de contratos devem ser números inteiros separados por vírgula"
            )

        if len(contract_ids_list) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo 10 contratos por comparação"
            )

        comparison_data = {}
        for contract_id in contract_ids_list:
            try:
                dashboard_data = await service.get_executive_dashboard(
                    contract_id=contract_id,
                    start_date=start_date,
                    end_date=end_date
                )
                if dashboard_data:
                    comparison_data[f"contract_{contract_id}"] = dashboard_data
            except Exception as e:
                logger.warning(f"Erro ao obter dados do contrato {contract_id}: {e}")
                comparison_data[f"contract_{contract_id}"] = {"error": str(e)}

        logger.info(f"Comparação obtida para contratos: {contract_ids}")
        return {
            "contracts_compared": contract_ids_list,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "data": comparison_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao comparar contratos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao comparar contratos"
        )


# === EXPORT ENDPOINTS ===

@router.get("/export/{contract_id}")
@require_role_level_or_permission(60, "contract_export.view")
async def export_dashboard(
    contract_id: int,
    format: str = Query("json", regex="^(json|csv)$", description="Formato de exportação"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    service: ContractDashboardService = Depends(get_dashboard_service)
):
    """Exportar dados do dashboard"""
    try:
        dashboard_data = await service.get_executive_dashboard(
            contract_id=contract_id,
            start_date=start_date,
            end_date=end_date
        )

        if not dashboard_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contrato {contract_id} não encontrado"
            )

        # TODO: Implementar exportação CSV
        if format == "csv":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Exportação CSV será implementada em versão futura"
            )

        logger.info(f"Dados exportados para contrato {contract_id} em formato {format}")
        return {
            "export_info": {
                "contract_id": contract_id,
                "format": format,
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            },
            "data": dashboard_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao exportar dados"
        )