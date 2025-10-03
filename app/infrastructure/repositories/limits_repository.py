"""
Repository para gestão de controle de limites automático
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.orm.models import (
    LimitsConfiguration,
    ServiceUsageTracking,
    LimitsViolation,
    AlertsConfiguration,
    AlertsLog,
    MedicalAuthorization,
    Contract,
    ServicesCatalog,
    User,
    People
)


class LimitsRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    # === LIMITS CONFIGURATION ===

    async def create_limits_config(self, **kwargs) -> LimitsConfiguration:
        """Criar nova configuração de limite"""
        config = LimitsConfiguration(**kwargs)
        self.db_session.add(config)
        await self.db_session.commit()
        await self.db_session.refresh(config)
        return config

    async def get_limits_config(self, config_id: int) -> Optional[LimitsConfiguration]:
        """Buscar configuração de limite por ID"""
        query = select(LimitsConfiguration).where(LimitsConfiguration.id == config_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def list_limits_configs(
        self,
        limit_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[LimitsConfiguration], int]:
        """Listar configurações de limite com filtros"""
        query = select(LimitsConfiguration)
        count_query = select(func.count(LimitsConfiguration.id))

        # Filtros
        conditions = []
        if limit_type:
            conditions.append(LimitsConfiguration.limit_type == limit_type)
        if entity_type:
            conditions.append(LimitsConfiguration.entity_type == entity_type)
        if entity_id:
            conditions.append(LimitsConfiguration.entity_id == entity_id)
        if is_active is not None:
            conditions.append(LimitsConfiguration.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Paginação
        query = query.offset((page - 1) * size).limit(size)
        query = query.order_by(LimitsConfiguration.created_at.desc())

        result = await self.db_session.execute(query)
        count_result = await self.db_session.execute(count_query)

        configs = result.scalars().all()
        total = count_result.scalar()

        return configs, total

    async def update_limits_config(self, config_id: int, **kwargs) -> Optional[LimitsConfiguration]:
        """Atualizar configuração de limite"""
        config = await self.get_limits_config(config_id)
        if not config:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        await self.db_session.commit()
        await self.db_session.refresh(config)
        return config

    # === SERVICE USAGE TRACKING ===

    async def track_service_usage(
        self,
        authorization_id: int,
        sessions_used: int,
        execution_date: date,
        executed_by: int,
        notes: Optional[str] = None
    ) -> ServiceUsageTracking:
        """Registrar uso de serviço"""
        usage = ServiceUsageTracking(
            authorization_id=authorization_id,
            sessions_used=sessions_used,
            execution_date=execution_date,
            executed_by=executed_by,
            notes=notes,
            created_at=datetime.utcnow()
        )
        self.db_session.add(usage)
        await self.db_session.commit()
        await self.db_session.refresh(usage)
        return usage

    async def get_usage_statistics(
        self,
        authorization_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obter estatísticas de uso"""
        # Base query
        query = select(
            func.count(ServiceUsageTracking.id).label('total_executions'),
            func.sum(ServiceUsageTracking.sessions_used).label('total_sessions'),
            func.avg(ServiceUsageTracking.sessions_used).label('avg_sessions_per_execution')
        )

        conditions = []
        if authorization_id:
            conditions.append(ServiceUsageTracking.authorization_id == authorization_id)

        if contract_id:
            # Join with authorization to filter by contract
            query = query.join(MedicalAuthorization, ServiceUsageTracking.authorization_id == MedicalAuthorization.id)
            query = query.join(Contract, MedicalAuthorization.contract_life_id == Contract.id)
            conditions.append(Contract.id == contract_id)

        if start_date:
            conditions.append(ServiceUsageTracking.execution_date >= start_date)
        if end_date:
            conditions.append(ServiceUsageTracking.execution_date <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.db_session.execute(query)
        stats = result.first()

        return {
            'total_executions': stats.total_executions or 0,
            'total_sessions': stats.total_sessions or 0,
            'avg_sessions_per_execution': float(stats.avg_sessions_per_execution or 0)
        }

    # === LIMITS VIOLATIONS ===

    async def create_violation(
        self,
        authorization_id: int,
        violation_type: str,
        attempted_value: float,
        limit_value: float,
        description: str,
        detected_by: int
    ) -> LimitsViolation:
        """Registrar violação de limite"""
        violation = LimitsViolation(
            authorization_id=authorization_id,
            violation_type=violation_type,
            attempted_value=attempted_value,
            limit_value=limit_value,
            description=description,
            detected_by=detected_by,
            detected_at=datetime.utcnow()
        )
        self.db_session.add(violation)
        await self.db_session.commit()
        await self.db_session.refresh(violation)
        return violation

    async def list_violations(
        self,
        authorization_id: Optional[int] = None,
        violation_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[LimitsViolation], int]:
        """Listar violações de limite"""
        query = select(LimitsViolation).options(
            joinedload(LimitsViolation.authorization),
            joinedload(LimitsViolation.detected_by_user)
        )
        count_query = select(func.count(LimitsViolation.id))

        conditions = []
        if authorization_id:
            conditions.append(LimitsViolation.authorization_id == authorization_id)
        if violation_type:
            conditions.append(LimitsViolation.violation_type == violation_type)
        if start_date:
            conditions.append(LimitsViolation.detected_at >= start_date)
        if end_date:
            conditions.append(LimitsViolation.detected_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.offset((page - 1) * size).limit(size)
        query = query.order_by(LimitsViolation.detected_at.desc())

        result = await self.db_session.execute(query)
        count_result = await self.db_session.execute(count_query)

        violations = result.scalars().all()
        total = count_result.scalar()

        return violations, total

    # === ALERTS CONFIGURATION ===

    async def create_alert_config(self, **kwargs) -> AlertsConfiguration:
        """Criar configuração de alerta"""
        config = AlertsConfiguration(**kwargs)
        self.db_session.add(config)
        await self.db_session.commit()
        await self.db_session.refresh(config)
        return config

    async def get_active_alert_configs(
        self,
        alert_type: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> List[AlertsConfiguration]:
        """Buscar configurações de alerta ativas"""
        query = select(AlertsConfiguration).where(AlertsConfiguration.is_active == True)

        if alert_type:
            query = query.where(AlertsConfiguration.alert_type == alert_type)
        if entity_type:
            query = query.where(AlertsConfiguration.entity_type == entity_type)

        result = await self.db_session.execute(query)
        return result.scalars().all()

    # === ALERTS LOG ===

    async def create_alert_log(
        self,
        alert_config_id: int,
        entity_id: int,
        message: str,
        severity: str = 'medium',
        data: Optional[Dict] = None
    ) -> AlertsLog:
        """Registrar log de alerta"""
        alert_log = AlertsLog(
            alert_config_id=alert_config_id,
            entity_id=entity_id,
            message=message,
            severity=severity,
            data=data,
            created_at=datetime.utcnow()
        )
        self.db_session.add(alert_log)
        await self.db_session.commit()
        await self.db_session.refresh(alert_log)
        return alert_log

    async def list_alert_logs(
        self,
        entity_id: Optional[int] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        size: int = 50
    ) -> tuple[List[AlertsLog], int]:
        """Listar logs de alerta"""
        query = select(AlertsLog).options(
            joinedload(AlertsLog.alert_config)
        )
        count_query = select(func.count(AlertsLog.id))

        conditions = []
        if entity_id:
            conditions.append(AlertsLog.entity_id == entity_id)
        if severity:
            conditions.append(AlertsLog.severity == severity)
        if start_date:
            conditions.append(AlertsLog.created_at >= start_date)
        if end_date:
            conditions.append(AlertsLog.created_at <= end_date)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.offset((page - 1) * size).limit(size)
        query = query.order_by(AlertsLog.created_at.desc())

        result = await self.db_session.execute(query)
        count_result = await self.db_session.execute(count_query)

        logs = result.scalars().all()
        total = count_result.scalar()

        return logs, total

    # === BUSINESS LOGIC METHODS ===

    async def check_authorization_limits(
        self,
        authorization_id: int,
        sessions_to_use: int = 1,
        execution_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Verificar limites de autorização usando função PostgreSQL"""
        if execution_date is None:
            execution_date = date.today()

        # Usar função PostgreSQL para verificação completa
        query = text("""
            SELECT master.check_authorization_limits(:auth_id, :sessions, :exec_date)
        """)

        result = await self.db_session.execute(
            query,
            {
                "auth_id": authorization_id,
                "sessions": sessions_to_use,
                "exec_date": execution_date
            }
        )

        return result.scalar()

    async def check_contract_limits(
        self,
        contract_id: int,
        current_month: Optional[date] = None
    ) -> Dict[str, Any]:
        """Verificar limites de contrato usando função PostgreSQL"""
        if current_month is None:
            current_month = date.today().replace(day=1)

        query = text("""
            SELECT master.check_contract_limits(:contract_id, :month)
        """)

        result = await self.db_session.execute(
            query,
            {
                "contract_id": contract_id,
                "month": current_month
            }
        )

        return result.scalar()

    async def get_expiring_authorizations(
        self,
        days_ahead: int = 7,
        company_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Buscar autorizações que vencem em breve"""
        query = text("""
            SELECT
                ma.id,
                ma.authorization_code,
                ma.valid_until,
                ma.sessions_remaining,
                sc.service_name,
                COALESCE(up.name, u.email_address) as patient_name,
                c.contract_number,
                (ma.valid_until - CURRENT_DATE) as days_until_expiry
            FROM master.medical_authorizations ma
            JOIN master.services_catalog sc ON ma.service_id = sc.id
            JOIN master.contract_lives cl ON ma.contract_life_id = cl.id
            JOIN master.contracts c ON cl.contract_id = c.id
            LEFT JOIN master.users u ON cl.life_id = u.id
            LEFT JOIN master.people up ON u.person_id = up.id
            WHERE ma.status = 'active'
            AND ma.valid_until BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s days'
            %s
            ORDER BY ma.valid_until ASC
        """ % (
            days_ahead,
            f"AND c.company_id = {company_id}" if company_id else ""
        ))

        result = await self.db_session.execute(query)
        rows = result.fetchall()

        return [
            {
                'authorization_id': row.id,
                'authorization_code': row.authorization_code,
                'valid_until': row.valid_until,
                'sessions_remaining': row.sessions_remaining,
                'service_name': row.service_name,
                'patient_name': row.patient_name,
                'contract_number': row.contract_number,
                'days_until_expiry': row.days_until_expiry
            }
            for row in rows
        ]

    async def get_limits_dashboard(
        self,
        company_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obter dados para dashboard de limites"""
        if start_date is None:
            start_date = date.today().replace(day=1)  # Primeiro dia do mês
        if end_date is None:
            end_date = date.today()

        # Estatísticas básicas
        violations_query = select(func.count(LimitsViolation.id)).where(
            and_(
                LimitsViolation.detected_at >= start_date,
                LimitsViolation.detected_at <= end_date
            )
        )

        usage_query = select(
            func.count(ServiceUsageTracking.id),
            func.sum(ServiceUsageTracking.sessions_used)
        ).where(
            and_(
                ServiceUsageTracking.execution_date >= start_date,
                ServiceUsageTracking.execution_date <= end_date
            )
        )

        alerts_query = select(func.count(AlertsLog.id)).where(
            and_(
                AlertsLog.created_at >= start_date,
                AlertsLog.created_at <= end_date
            )
        )

        violations_result = await self.db_session.execute(violations_query)
        usage_result = await self.db_session.execute(usage_query)
        alerts_result = await self.db_session.execute(alerts_query)

        violations_count = violations_result.scalar()
        usage_stats = usage_result.first()
        alerts_count = alerts_result.scalar()

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'violations': {
                'total': violations_count or 0
            },
            'usage': {
                'total_executions': usage_stats[0] or 0,
                'total_sessions': usage_stats[1] or 0
            },
            'alerts': {
                'total': alerts_count or 0
            }
        }