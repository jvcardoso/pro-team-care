from typing import Any, Dict, List, Optional
from datetime import date, datetime

import structlog
from sqlalchemy import Integer, and_, func, or_, select, text
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.orm.models import (
    Contract,
    ContractLive,
    ContractService,
    ContractLifeService,
    ServicesCatalog,
    ServiceExecution,
)
from app.infrastructure.orm.models import Client as ClientEntity
from app.infrastructure.orm.models import Company, People
from app.infrastructure.orm.models import Establishments
from app.infrastructure.services.tenant_context_service import get_tenant_context

logger = structlog.get_logger()


class ContractRepository:
    def __init__(self, db):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, "replace"):
            return dt.replace(tzinfo=None)
        return dt

    async def _generate_contract_number(self, client_id: int) -> str:
        """Generate unique contract number in format CLI{client_id}-{sequential}"""
        try:
            # Get client ID padded to 6 digits
            client_prefix = f"CLI{client_id:06d}"

            # Find highest sequential number for this client
            try:
                query = select(func.count(Contract.id)).where(
                    Contract.client_id == client_id
                )
                result = await self.db.execute(query)
                count = result.scalar() or 0
            except Exception:
                # If table doesn't exist, start from 0
                count = 0

            # Generate next sequential number
            sequential = count + 1
            contract_number = f"{client_prefix}-{sequential:03d}"

            logger.info(
                "Generated contract number",
                client_id=client_id,
                contract_number=contract_number,
                sequential=sequential,
            )

            return contract_number

        except Exception as e:
            logger.error("Error generating contract number", error=str(e), client_id=client_id)
            raise

    async def create_contract(self, contract_data: Dict[str, Any]) -> Contract:
        """Create a new contract"""
        try:
            # Generate contract number
            contract_number = await self._generate_contract_number(contract_data["client_id"])

            # Create contract entity
            contract = Contract(
                client_id=contract_data["client_id"],
                contract_number=contract_number,
                contract_type=contract_data.get("contract_type", "INDIVIDUAL"),
                lives_contracted=contract_data.get("lives_contracted", 1),
                lives_minimum=contract_data.get("lives_minimum"),
                lives_maximum=contract_data.get("lives_maximum"),
                allows_substitution=contract_data.get("allows_substitution", False),
                control_period=contract_data.get("control_period", "MONTHLY"),
                plan_name=contract_data.get("plan_name", "Default Plan"),
                monthly_value=contract_data.get("monthly_value"),
                start_date=contract_data["start_date"],
                end_date=contract_data.get("end_date"),
                service_addresses=contract_data.get("service_addresses"),
                status=contract_data.get("status", "active"),
                created_by=contract_data.get("created_by"),
                updated_by=contract_data.get("created_by"),  # Set updated_by to same as created_by initially
            )

            self.db.add(contract)
            await self.db.flush()
            await self.db.refresh(contract)

            logger.info(
                "Contract created successfully",
                contract_id=contract.id,
                contract_number=contract.contract_number,
                client_id=contract.client_id,
            )

            return contract

        except Exception as e:
            logger.error("Error creating contract", error=str(e), contract_data=contract_data)
            raise

    async def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """Get contract by ID with related data"""
        try:
            tenant_context = get_tenant_context()

            query = (
                select(Contract)
                .options(
                    joinedload(Contract.client).joinedload(ClientEntity.person),
                    joinedload(Contract.lives),
                    joinedload(Contract.services),
                )
                .where(Contract.id == contract_id)
            )

            # Add tenant context filtering if available
            if tenant_context and tenant_context.current_company_id:
                query = query.join(ClientEntity).where(
                    ClientEntity.company_id == tenant_context.current_company_id
                )

            result = await self.db.execute(query)
            contract = result.unique().scalar_one_or_none()

            if contract:
                logger.info("Contract retrieved successfully", contract_id=contract_id)
            else:
                logger.warning("Contract not found", contract_id=contract_id)

            return contract

        except Exception as e:
            logger.error("Error retrieving contract", error=str(e), contract_id=contract_id)
            raise

    async def list_contracts(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None,
        contract_type: Optional[str] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List contracts with filtering and pagination"""
        try:
            logger.info("Starting contract list query", client_id=client_id, status=status, contract_type=contract_type, page=page, size=size)
            tenant_context = get_tenant_context()
            logger.info("Tenant context retrieved", company_id=tenant_context.current_company_id if tenant_context else None)
            logger.info("Tenant context object", tenant_context=tenant_context)
            offset = (page - 1) * size

            # Base query
            base_query = select(Contract)

            # Add tenant context filtering (temporarily disabled for debugging)
            # if tenant_context and tenant_context.current_company_id:
            #     base_query = base_query.join(ClientEntity).join(Establishments).where(
            #         Establishments.company_id == tenant_context.current_company_id
            #     )

            # Apply filters
            filters = []
            if client_id:
                filters.append(Contract.client_id == client_id)
            if status:
                filters.append(Contract.status == status)
            if contract_type:
                filters.append(Contract.contract_type == contract_type)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            logger.info("Executing count query")
            count_query = select(func.count(Contract.id))

            # Apply the same filters as base_query
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            logger.info("Count query completed", total=total)

            # Get paginated results
            logger.info("Executing main query")
            query = base_query.order_by(Contract.created_at.desc()).offset(offset).limit(size)
            result = await self.db.execute(query)
            contracts = result.scalars().all()
            logger.info("Main query completed", contracts_count=len(contracts))

            logger.info(
                "Contracts listed successfully",
                total=total,
                page=page,
                size=size,
                filters={"client_id": client_id, "status": status, "contract_type": contract_type},
            )

            return {
                "contracts": contracts,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing contracts", error=str(e))
            raise

    async def update_contract(self, contract_id: int, update_data: Dict[str, Any]) -> Optional[Contract]:
        """Update contract"""
        try:
            # Use SQLAlchemy update query
            from sqlalchemy import update

            # Add updated_at to the update data
            update_data_with_timestamp = update_data.copy()
            update_data_with_timestamp["updated_at"] = datetime.utcnow()

            stmt = (
                update(Contract)
                .where(Contract.id == contract_id)
                .values(**update_data_with_timestamp)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated contract
            contract = await self.get_contract_by_id(contract_id)

            logger.info("Contract updated successfully", contract_id=contract_id)
            return contract

        except Exception as e:
            logger.error("Error updating contract", error=str(e), contract_id=contract_id)
            raise

    async def update_contract_status(self, contract_id: int, status: str) -> Optional[Contract]:
        """Update contract status"""
        try:
            # Use SQLAlchemy update query
            from sqlalchemy import update

            stmt = (
                update(Contract)
                .where(Contract.id == contract_id)
                .values(status=status, updated_at=datetime.utcnow())
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated contract
            contract = await self.get_contract_by_id(contract_id)

            logger.info("Contract status updated successfully", contract_id=contract_id, status=status)
            return contract

        except Exception as e:
            logger.error("Error updating contract status", error=str(e), contract_id=contract_id)
            raise

    async def delete_contract(self, contract_id: int) -> bool:
        """Soft delete contract"""
        try:
            # Use SQLAlchemy update query
            from sqlalchemy import update

            stmt = (
                update(Contract)
                .where(Contract.id == contract_id)
                .values(
                    status="deleted",
                    updated_at=datetime.utcnow()
                )
            )

            result = await self.db.execute(stmt)
            await self.db.flush()

            # Check if any row was updated
            if result.rowcount > 0:
                logger.info("Contract deleted successfully", contract_id=contract_id)
                return True
            else:
                logger.warning("Contract not found for deletion", contract_id=contract_id)
                return False

        except Exception as e:
            logger.error("Error deleting contract", error=str(e), contract_id=contract_id)
            raise


class ServicesRepository:
    def __init__(self, db):
        self.db = db

    async def list_services_catalog(
        self,
        category: Optional[str] = None,
        service_type: Optional[str] = None,
        page: int = 1,
        size: int = 100,
    ) -> Dict[str, Any]:
        """List services from catalog with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(ServicesCatalog).where(
                ServicesCatalog.status == 'active'
            )

            # Apply filters
            filters = []
            if category:
                filters.append(ServicesCatalog.service_category == category)
            if service_type:
                filters.append(ServicesCatalog.service_type == service_type)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(ServicesCatalog.id)).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(ServicesCatalog.service_name).offset(offset).limit(size)
            result = await self.db.execute(query)
            services = result.scalars().all()

            logger.info(
                "Services catalog listed successfully",
                total=total,
                page=page,
                size=size,
                filters={"category": category, "service_type": service_type},
            )

            return {
                "services": services,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing services catalog", error=str(e))
            raise

    async def get_service_by_id(self, service_id: int) -> Optional[ServicesCatalog]:
        """Get service by ID"""
        try:
            query = select(ServicesCatalog).where(
                ServicesCatalog.id == service_id
            )

            result = await self.db.execute(query)
            service = result.scalar_one_or_none()

            if service:
                logger.info("Service retrieved successfully", service_id=service_id)
            else:
                logger.warning("Service not found", service_id=service_id)

            return service

        except Exception as e:
            logger.error("Error retrieving service", error=str(e), service_id=service_id)
            raise