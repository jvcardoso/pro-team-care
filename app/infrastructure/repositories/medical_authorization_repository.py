"""Repository para autorizações médicas"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import and_, or_, func, desc, asc, case, extract
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import text

from app.infrastructure.orm.models import (
    MedicalAuthorization,
    AuthorizationRenewal,
    AuthorizationHistory,
    ServicesCatalog,
    ContractLive,
    User,
    People
)
from app.presentation.schemas.medical_authorization import (
    MedicalAuthorizationCreate,
    MedicalAuthorizationUpdate,
    MedicalAuthorizationListParams,
    AuthorizationRenewalCreate,
    AuthorizationHistoryCreate,
    SessionUpdateRequest,
    AuthorizationSuspendRequest,
    AuthorizationRenewRequest,
    AuthorizationStatusEnum,
    UrgencyLevelEnum,
    AuthorizationActionEnum
)


class MedicalAuthorizationRepository:
    """Repository para gestão de autorizações médicas"""

    def __init__(self, db: Session):
        self.db = db

    async def create_authorization(
        self,
        authorization_data: MedicalAuthorizationCreate,
        created_by: int,
        company_id: Optional[int] = None
    ) -> MedicalAuthorization:
        """Criar nova autorização médica"""

        authorization = MedicalAuthorization(
            **authorization_data.dict(),
            created_by=created_by,
            updated_by=created_by
        )

        self.db.add(authorization)
        self.db.flush()  # Get the ID

        # Create history entry
        await self._create_history_entry(
            authorization.id,
            AuthorizationActionEnum.CREATED,
            performed_by=created_by,
            reason="Autorização médica criada"
        )

        self.db.commit()
        return authorization

    async def get_authorization(
        self,
        authorization_id: int,
        company_id: Optional[int] = None
    ) -> Optional[MedicalAuthorization]:
        """Buscar autorização por ID"""

        query = self.db.query(MedicalAuthorization).options(
            joinedload(MedicalAuthorization.service),
            joinedload(MedicalAuthorization.contract_life).joinedload(ContractLive.person),
            joinedload(MedicalAuthorization.doctor).joinedload(User.person)
        )

        if company_id:
            # Filter by company through contract_life -> contract -> client
            query = query.join(ContractLive).join(
                "contract"
            ).join("client").filter_by(company_id=company_id)

        return query.filter(MedicalAuthorization.id == authorization_id).first()

    async def list_authorizations(
        self,
        params: MedicalAuthorizationListParams,
        company_id: Optional[int] = None
    ) -> Tuple[List[MedicalAuthorization], int]:
        """Listar autorizações com filtros e paginação"""

        query = self.db.query(MedicalAuthorization).options(
            joinedload(MedicalAuthorization.service),
            joinedload(MedicalAuthorization.contract_life).joinedload(ContractLive.person),
            joinedload(MedicalAuthorization.doctor).joinedload(User.person)
        )

        # Multi-tenant filter
        if company_id:
            query = query.join(ContractLive).join(
                "contract"
            ).join("client").filter_by(company_id=company_id)

        # Apply filters
        if params.contract_life_id:
            query = query.filter(MedicalAuthorization.contract_life_id == params.contract_life_id)

        if params.service_id:
            query = query.filter(MedicalAuthorization.service_id == params.service_id)

        if params.doctor_id:
            query = query.filter(MedicalAuthorization.doctor_id == params.doctor_id)

        if params.status:
            query = query.filter(MedicalAuthorization.status == params.status.value)

        if params.urgency_level:
            query = query.filter(MedicalAuthorization.urgency_level == params.urgency_level.value)

        if params.valid_from:
            query = query.filter(MedicalAuthorization.valid_from >= params.valid_from)

        if params.valid_until:
            query = query.filter(MedicalAuthorization.valid_until <= params.valid_until)

        if params.requires_supervision is not None:
            query = query.filter(MedicalAuthorization.requires_supervision == params.requires_supervision)

        # Count total
        total = query.count()

        # Apply pagination and ordering
        authorizations = query.order_by(
            desc(MedicalAuthorization.created_at)
        ).offset(
            (params.page - 1) * params.size
        ).limit(params.size).all()

        return authorizations, total

    async def update_authorization(
        self,
        authorization_id: int,
        update_data: MedicalAuthorizationUpdate,
        updated_by: int,
        company_id: Optional[int] = None
    ) -> Optional[MedicalAuthorization]:
        """Atualizar autorização médica"""

        authorization = await self.get_authorization(authorization_id, company_id)
        if not authorization:
            return None

        # Track changes for history
        changes = []
        update_dict = update_data.dict(exclude_unset=True)

        for field, new_value in update_dict.items():
            old_value = getattr(authorization, field)
            if old_value != new_value:
                changes.append({
                    'field': field,
                    'old_value': str(old_value) if old_value is not None else None,
                    'new_value': str(new_value) if new_value is not None else None
                })
                setattr(authorization, field, new_value)

        authorization.updated_by = updated_by
        authorization.updated_at = datetime.utcnow()

        # Create history entries for changes
        for change in changes:
            await self._create_history_entry(
                authorization_id,
                AuthorizationActionEnum.UPDATED,
                performed_by=updated_by,
                field_changed=change['field'],
                old_value=change['old_value'],
                new_value=change['new_value'],
                reason="Autorização atualizada"
            )

        self.db.commit()
        return authorization

    async def cancel_authorization(
        self,
        authorization_id: int,
        cancellation_reason: str,
        cancelled_by: int,
        company_id: Optional[int] = None
    ) -> Optional[MedicalAuthorization]:
        """Cancelar autorização médica"""

        authorization = await self.get_authorization(authorization_id, company_id)
        if not authorization:
            return None

        authorization.status = AuthorizationStatusEnum.CANCELLED.value
        authorization.cancellation_reason = cancellation_reason
        authorization.cancelled_at = datetime.utcnow()
        authorization.cancelled_by = cancelled_by
        authorization.updated_by = cancelled_by
        authorization.updated_at = datetime.utcnow()

        await self._create_history_entry(
            authorization_id,
            AuthorizationActionEnum.CANCELLED,
            performed_by=cancelled_by,
            reason=cancellation_reason
        )

        self.db.commit()
        return authorization

    async def suspend_authorization(
        self,
        authorization_id: int,
        suspend_data: AuthorizationSuspendRequest,
        suspended_by: int,
        company_id: Optional[int] = None
    ) -> Optional[MedicalAuthorization]:
        """Suspender autorização médica"""

        authorization = await self.get_authorization(authorization_id, company_id)
        if not authorization:
            return None

        authorization.status = AuthorizationStatusEnum.SUSPENDED.value
        authorization.updated_by = suspended_by
        authorization.updated_at = datetime.utcnow()

        await self._create_history_entry(
            authorization_id,
            AuthorizationActionEnum.SUSPENDED,
            performed_by=suspended_by,
            reason=suspend_data.reason
        )

        self.db.commit()
        return authorization

    async def update_sessions(
        self,
        authorization_id: int,
        session_update: SessionUpdateRequest,
        updated_by: int,
        company_id: Optional[int] = None
    ) -> Optional[MedicalAuthorization]:
        """Atualizar sessões utilizadas"""

        authorization = await self.get_authorization(authorization_id, company_id)
        if not authorization:
            return None

        if authorization.sessions_remaining is not None:
            if authorization.sessions_remaining < session_update.sessions_used:
                raise ValueError("Sessões insuficientes")

            old_remaining = authorization.sessions_remaining
            authorization.sessions_remaining -= session_update.sessions_used

            await self._create_history_entry(
                authorization_id,
                AuthorizationActionEnum.SESSIONS_UPDATED,
                performed_by=updated_by,
                field_changed="sessions_remaining",
                old_value=str(old_remaining),
                new_value=str(authorization.sessions_remaining),
                reason=session_update.notes or f"Utilizadas {session_update.sessions_used} sessões"
            )

        authorization.updated_by = updated_by
        authorization.updated_at = datetime.utcnow()

        self.db.commit()
        return authorization

    async def renew_authorization(
        self,
        authorization_id: int,
        renew_data: AuthorizationRenewRequest,
        approved_by: int,
        company_id: Optional[int] = None
    ) -> Optional[Tuple[MedicalAuthorization, AuthorizationRenewal]]:
        """Renovar autorização médica"""

        original = await self.get_authorization(authorization_id, company_id)
        if not original:
            return None

        # Create new authorization based on original
        new_auth_data = MedicalAuthorizationCreate(
            contract_life_id=original.contract_life_id,
            service_id=original.service_id,
            doctor_id=original.doctor_id,
            authorization_date=date.today(),
            valid_from=original.valid_until,  # Continue from where original ends
            valid_until=renew_data.new_valid_until,
            sessions_authorized=renew_data.additional_sessions or original.sessions_authorized,
            sessions_remaining=renew_data.additional_sessions or original.sessions_authorized,
            monthly_limit=original.monthly_limit,
            weekly_limit=original.weekly_limit,
            daily_limit=original.daily_limit,
            medical_indication=original.medical_indication,
            contraindications=original.contraindications,
            special_instructions=original.special_instructions,
            urgency_level=original.urgency_level,
            requires_supervision=original.requires_supervision,
            supervision_notes=original.supervision_notes,
            diagnosis_cid=original.diagnosis_cid,
            diagnosis_description=original.diagnosis_description,
            treatment_goals=original.treatment_goals,
            expected_duration_days=original.expected_duration_days,
            renewal_allowed=original.renewal_allowed,
            renewal_conditions=original.renewal_conditions
        )

        new_authorization = await self.create_authorization(
            new_auth_data,
            approved_by,
            company_id
        )

        # Create renewal record
        renewal = AuthorizationRenewal(
            original_authorization_id=authorization_id,
            new_authorization_id=new_authorization.id,
            renewal_date=date.today(),
            renewal_reason=renew_data.renewal_reason,
            changes_made=renew_data.changes_summary,
            approved_by=approved_by
        )

        self.db.add(renewal)

        # Create history entries
        await self._create_history_entry(
            authorization_id,
            AuthorizationActionEnum.RENEWED,
            performed_by=approved_by,
            reason=renew_data.renewal_reason
        )

        self.db.commit()
        return new_authorization, renewal

    async def get_authorization_history(
        self,
        authorization_id: int,
        company_id: Optional[int] = None
    ) -> List[AuthorizationHistory]:
        """Buscar histórico de uma autorização"""

        query = self.db.query(AuthorizationHistory).options(
            joinedload(AuthorizationHistory.performed_by_user).joinedload(User.person)
        ).filter(AuthorizationHistory.authorization_id == authorization_id)

        return query.order_by(desc(AuthorizationHistory.performed_at)).all()

    async def get_active_authorizations_by_patient(
        self,
        person_id: int,
        company_id: Optional[int] = None
    ) -> List[MedicalAuthorization]:
        """Buscar autorizações ativas de um paciente"""

        query = self.db.query(MedicalAuthorization).options(
            joinedload(MedicalAuthorization.service),
            joinedload(MedicalAuthorization.doctor).joinedload(User.person)
        ).join(ContractLive).filter(
            ContractLive.person_id == person_id,
            MedicalAuthorization.status == AuthorizationStatusEnum.ACTIVE.value,
            MedicalAuthorization.valid_from <= date.today(),
            MedicalAuthorization.valid_until >= date.today()
        )

        if company_id:
            query = query.join("contract").join("client").filter_by(company_id=company_id)

        return query.all()

    async def get_authorizations_expiring_soon(
        self,
        days: int = 7,
        company_id: Optional[int] = None
    ) -> List[MedicalAuthorization]:
        """Buscar autorizações que vencem em X dias"""

        expiry_date = date.today() + timedelta(days=days)

        query = self.db.query(MedicalAuthorization).options(
            joinedload(MedicalAuthorization.service),
            joinedload(MedicalAuthorization.contract_life).joinedload(ContractLive.person),
            joinedload(MedicalAuthorization.doctor).joinedload(User.person)
        ).filter(
            MedicalAuthorization.status == AuthorizationStatusEnum.ACTIVE.value,
            MedicalAuthorization.valid_until <= expiry_date,
            MedicalAuthorization.valid_until >= date.today()
        )

        if company_id:
            query = query.join(ContractLive).join(
                "contract"
            ).join("client").filter_by(company_id=company_id)

        return query.all()

    async def get_authorization_statistics(
        self,
        company_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obter estatísticas de autorizações"""

        query = self.db.query(MedicalAuthorization)

        if company_id:
            query = query.join(ContractLive).join(
                "contract"
            ).join("client").filter_by(company_id=company_id)

        if start_date:
            query = query.filter(MedicalAuthorization.created_at >= start_date)

        if end_date:
            query = query.filter(MedicalAuthorization.created_at <= end_date)

        # Basic counts
        total = query.count()
        active = query.filter(MedicalAuthorization.status == AuthorizationStatusEnum.ACTIVE.value).count()
        expired = query.filter(MedicalAuthorization.status == AuthorizationStatusEnum.EXPIRED.value).count()
        cancelled = query.filter(MedicalAuthorization.status == AuthorizationStatusEnum.CANCELLED.value).count()
        suspended = query.filter(MedicalAuthorization.status == AuthorizationStatusEnum.SUSPENDED.value).count()

        # Urgent authorizations
        urgent = query.filter(MedicalAuthorization.urgency_level == UrgencyLevelEnum.URGENT.value).count()

        # Supervision required
        supervision = query.filter(MedicalAuthorization.requires_supervision == True).count()

        # Session statistics
        sessions_stats = query.with_entities(
            func.sum(MedicalAuthorization.sessions_authorized),
            func.sum(MedicalAuthorization.sessions_remaining)
        ).first()

        # Average duration
        avg_duration = query.with_entities(
            func.avg(MedicalAuthorization.expected_duration_days)
        ).scalar()

        # Most common service
        common_service = self.db.query(
            ServicesCatalog.service_name,
            func.count(MedicalAuthorization.id).label('count')
        ).join(
            MedicalAuthorization
        ).group_by(
            ServicesCatalog.service_name
        ).order_by(
            desc('count')
        ).first()

        # Most active doctor
        active_doctor = self.db.query(
            func.coalesce(People.name, User.email_address).label('doctor_name'),
            func.count(MedicalAuthorization.id).label('count')
        ).join(
            User, MedicalAuthorization.doctor_id == User.id
        ).outerjoin(
            People, User.person_id == People.id
        ).group_by(
            'doctor_name'
        ).order_by(
            desc('count')
        ).first()

        return {
            'total_authorizations': total,
            'active_authorizations': active,
            'expired_authorizations': expired,
            'cancelled_authorizations': cancelled,
            'suspended_authorizations': suspended,
            'urgent_authorizations': urgent,
            'authorizations_requiring_supervision': supervision,
            'sessions_authorized_total': sessions_stats[0] or 0,
            'sessions_remaining_total': sessions_stats[1] or 0,
            'average_duration_days': float(avg_duration) if avg_duration else None,
            'most_common_service': common_service[0] if common_service else None,
            'most_active_doctor': active_doctor[0] if active_doctor else None
        }

    async def _create_history_entry(
        self,
        authorization_id: int,
        action: AuthorizationActionEnum,
        performed_by: int,
        field_changed: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuthorizationHistory:
        """Criar entrada no histórico"""

        history = AuthorizationHistory(
            authorization_id=authorization_id,
            action=action.value,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            performed_by=performed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.db.add(history)
        return history