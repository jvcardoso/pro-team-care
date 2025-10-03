from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import Integer, and_, func, or_, select, text, update, desc
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.orm.models import (
    Contract,
    ContractBillingSchedule,
    ContractInvoice,
    PaymentReceipt,
    BillingAuditLog,
    PagBankTransaction,
    Client,
    People,
)
from app.infrastructure.services.tenant_context_service import get_tenant_context

logger = structlog.get_logger()


class BillingRepository:
    def __init__(self, db):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, "replace"):
            return dt.replace(tzinfo=None)
        return dt

    # ==========================================
    # BILLING SCHEDULE METHODS
    # ==========================================

    async def create_billing_schedule(self, schedule_data: Dict[str, Any]) -> ContractBillingSchedule:
        """Create a new billing schedule"""
        try:
            schedule = ContractBillingSchedule(
                contract_id=schedule_data["contract_id"],
                billing_cycle=schedule_data.get("billing_cycle", "MONTHLY"),
                billing_day=schedule_data.get("billing_day", 1),
                next_billing_date=schedule_data["next_billing_date"],
                amount_per_cycle=schedule_data["amount_per_cycle"],
                is_active=schedule_data.get("is_active", True),
                created_by=schedule_data.get("created_by"),
            )

            self.db.add(schedule)
            await self.db.flush()
            await self.db.refresh(schedule)

            logger.info(
                "Billing schedule created successfully",
                schedule_id=schedule.id,
                contract_id=schedule.contract_id,
            )

            return schedule

        except Exception as e:
            logger.error("Error creating billing schedule", error=str(e), schedule_data=schedule_data)
            raise

    async def get_billing_schedule_by_id(self, schedule_id: int) -> Optional[ContractBillingSchedule]:
        """Get billing schedule by ID"""
        try:
            query = (
                select(ContractBillingSchedule)
                .options(joinedload(ContractBillingSchedule.contract))
                .where(ContractBillingSchedule.id == schedule_id)
            )

            result = await self.db.execute(query)
            schedule = result.unique().scalar_one_or_none()

            if schedule:
                logger.info("Billing schedule retrieved successfully", schedule_id=schedule_id)
            else:
                logger.warning("Billing schedule not found", schedule_id=schedule_id)

            return schedule

        except Exception as e:
            logger.error("Error retrieving billing schedule", error=str(e), schedule_id=schedule_id)
            raise

    async def get_billing_schedule_by_contract(self, contract_id: int) -> Optional[ContractBillingSchedule]:
        """Get billing schedule by contract ID"""
        try:
            query = (
                select(ContractBillingSchedule)
                .where(ContractBillingSchedule.contract_id == contract_id)
                .where(ContractBillingSchedule.is_active == True)
            )

            result = await self.db.execute(query)
            schedule = result.scalar_one_or_none()

            return schedule

        except Exception as e:
            logger.error("Error retrieving billing schedule by contract", error=str(e), contract_id=contract_id)
            raise

    async def list_billing_schedules(
        self,
        contract_id: Optional[int] = None,
        billing_cycle: Optional[str] = None,
        is_active: Optional[bool] = None,
        next_billing_before: Optional[date] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List billing schedules with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(ContractBillingSchedule).options(
                joinedload(ContractBillingSchedule.contract)
            )

            # Apply filters
            filters = []
            if contract_id:
                filters.append(ContractBillingSchedule.contract_id == contract_id)
            if billing_cycle:
                filters.append(ContractBillingSchedule.billing_cycle == billing_cycle)
            if is_active is not None:
                filters.append(ContractBillingSchedule.is_active == is_active)
            if next_billing_before:
                filters.append(ContractBillingSchedule.next_billing_date <= next_billing_before)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(ContractBillingSchedule.id))
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(ContractBillingSchedule.next_billing_date).offset(offset).limit(size)
            result = await self.db.execute(query)
            schedules = result.unique().scalars().all()

            logger.info(
                "Billing schedules listed successfully",
                total=total,
                page=page,
                size=size,
            )

            return {
                "schedules": schedules,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing billing schedules", error=str(e))
            raise

    async def update_billing_schedule(self, schedule_id: int, update_data: Dict[str, Any]) -> Optional[ContractBillingSchedule]:
        """Update billing schedule"""
        try:
            update_data_with_timestamp = update_data.copy()
            update_data_with_timestamp["updated_at"] = datetime.utcnow()

            stmt = (
                update(ContractBillingSchedule)
                .where(ContractBillingSchedule.id == schedule_id)
                .values(**update_data_with_timestamp)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated schedule
            schedule = await self.get_billing_schedule_by_id(schedule_id)

            logger.info("Billing schedule updated successfully", schedule_id=schedule_id)
            return schedule

        except Exception as e:
            logger.error("Error updating billing schedule", error=str(e), schedule_id=schedule_id)
            raise

    # ==========================================
    # INVOICE METHODS
    # ==========================================

    async def _generate_invoice_number(self, contract_id: int) -> str:
        """Generate unique invoice number in format INV-{year}{month}-{contract_id}-{sequential}"""
        try:
            now = datetime.now()
            year_month = now.strftime("%Y%m")

            # Find highest sequential number for this contract and month
            query = select(func.count(ContractInvoice.id)).where(
                and_(
                    ContractInvoice.contract_id == contract_id,
                    func.extract('year', ContractInvoice.created_at) == now.year,
                    func.extract('month', ContractInvoice.created_at) == now.month
                )
            )
            result = await self.db.execute(query)
            count = result.scalar() or 0

            sequential = count + 1
            invoice_number = f"INV-{year_month}-{contract_id:06d}-{sequential:03d}"

            logger.info(
                "Generated invoice number",
                contract_id=contract_id,
                invoice_number=invoice_number,
                sequential=sequential,
            )

            return invoice_number

        except Exception as e:
            logger.error("Error generating invoice number", error=str(e), contract_id=contract_id)
            raise

    async def create_invoice(self, invoice_data: Dict[str, Any]) -> ContractInvoice:
        """Create a new invoice"""
        try:
            # Generate invoice number if not provided
            invoice_number = invoice_data.get("invoice_number")
            if not invoice_number:
                invoice_number = await self._generate_invoice_number(invoice_data["contract_id"])

            # Calculate total amount if not provided
            total_amount = invoice_data.get("total_amount")
            if not total_amount:
                base_amount = invoice_data.get("base_amount", Decimal("0"))
                additional_services = invoice_data.get("additional_services_amount", Decimal("0"))
                discounts = invoice_data.get("discounts", Decimal("0"))
                taxes = invoice_data.get("taxes", Decimal("0"))
                total_amount = base_amount + additional_services + taxes - discounts

            invoice = ContractInvoice(
                contract_id=invoice_data["contract_id"],
                invoice_number=invoice_number,
                billing_period_start=invoice_data["billing_period_start"],
                billing_period_end=invoice_data["billing_period_end"],
                lives_count=invoice_data["lives_count"],
                base_amount=invoice_data["base_amount"],
                additional_services_amount=invoice_data.get("additional_services_amount", Decimal("0")),
                discounts=invoice_data.get("discounts", Decimal("0")),
                taxes=invoice_data.get("taxes", Decimal("0")),
                total_amount=total_amount,
                status=invoice_data.get("status", "pendente"),
                due_date=invoice_data["due_date"],
                issued_date=invoice_data.get("issued_date", date.today()),
                payment_method=invoice_data.get("payment_method"),
                payment_reference=invoice_data.get("payment_reference"),
                payment_notes=invoice_data.get("payment_notes"),
                observations=invoice_data.get("observations"),
                created_by=invoice_data.get("created_by"),
                updated_by=invoice_data.get("created_by"),
            )

            self.db.add(invoice)
            await self.db.flush()
            await self.db.refresh(invoice)

            logger.info(
                "Invoice created successfully",
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                contract_id=invoice.contract_id,
            )

            return invoice

        except Exception as e:
            logger.error("Error creating invoice", error=str(e), invoice_data=invoice_data)
            raise

    async def get_invoice_by_id(self, invoice_id: int) -> Optional[ContractInvoice]:
        """Get invoice by ID with related data"""
        try:
            query = (
                select(ContractInvoice)
                .options(
                    joinedload(ContractInvoice.contract).joinedload(Contract.client).joinedload(Client.person),
                    selectinload(ContractInvoice.receipts),
                )
                .where(ContractInvoice.id == invoice_id)
            )

            result = await self.db.execute(query)
            invoice = result.unique().scalar_one_or_none()

            if invoice:
                logger.info("Invoice retrieved successfully", invoice_id=invoice_id)
            else:
                logger.warning("Invoice not found", invoice_id=invoice_id)

            return invoice

        except Exception as e:
            logger.error("Error retrieving invoice", error=str(e), invoice_id=invoice_id)
            raise

    async def list_invoices(
        self,
        contract_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        overdue_only: Optional[bool] = False,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List invoices with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(ContractInvoice).options(
                joinedload(ContractInvoice.contract).joinedload(Contract.client).joinedload(Client.person)
            )

            # Apply filters
            filters = []
            if contract_id:
                filters.append(ContractInvoice.contract_id == contract_id)
            if status:
                filters.append(ContractInvoice.status == status)
            if start_date:
                filters.append(ContractInvoice.issued_date >= start_date)
            if end_date:
                filters.append(ContractInvoice.issued_date <= end_date)
            if overdue_only:
                filters.append(
                    and_(
                        ContractInvoice.due_date < date.today(),
                        ContractInvoice.status.in_(["pendente", "enviada"])
                    )
                )

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(ContractInvoice.id))
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(desc(ContractInvoice.created_at)).offset(offset).limit(size)
            result = await self.db.execute(query)
            invoices = result.unique().scalars().all()

            logger.info(
                "Invoices listed successfully",
                total=total,
                page=page,
                size=size,
            )

            return {
                "invoices": invoices,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing invoices", error=str(e))
            raise

    async def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> Optional[ContractInvoice]:
        """Update invoice"""
        try:
            update_data_with_timestamp = update_data.copy()
            update_data_with_timestamp["updated_at"] = datetime.utcnow()

            stmt = (
                update(ContractInvoice)
                .where(ContractInvoice.id == invoice_id)
                .values(**update_data_with_timestamp)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated invoice
            invoice = await self.get_invoice_by_id(invoice_id)

            logger.info("Invoice updated successfully", invoice_id=invoice_id)
            return invoice

        except Exception as e:
            logger.error("Error updating invoice", error=str(e), invoice_id=invoice_id)
            raise

    async def update_invoice_status(self, invoice_id: int, status: str, **kwargs) -> Optional[ContractInvoice]:
        """Update invoice status with optional payment details"""
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            # Add payment-related fields if provided
            if "paid_date" in kwargs:
                update_data["paid_date"] = kwargs["paid_date"]
            if "payment_method" in kwargs:
                update_data["payment_method"] = kwargs["payment_method"]
            if "payment_reference" in kwargs:
                update_data["payment_reference"] = kwargs["payment_reference"]
            if "payment_notes" in kwargs:
                update_data["payment_notes"] = kwargs["payment_notes"]

            stmt = (
                update(ContractInvoice)
                .where(ContractInvoice.id == invoice_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated invoice
            invoice = await self.get_invoice_by_id(invoice_id)

            logger.info("Invoice status updated successfully", invoice_id=invoice_id, status=status)
            return invoice

        except Exception as e:
            logger.error("Error updating invoice status", error=str(e), invoice_id=invoice_id)
            raise

    # ==========================================
    # PAYMENT RECEIPT METHODS
    # ==========================================

    async def create_payment_receipt(self, receipt_data: Dict[str, Any]) -> PaymentReceipt:
        """Create a new payment receipt"""
        try:
            receipt = PaymentReceipt(
                invoice_id=receipt_data["invoice_id"],
                file_name=receipt_data["file_name"],
                file_path=receipt_data["file_path"],
                file_type=receipt_data.get("file_type"),
                file_size=receipt_data.get("file_size"),
                verification_status=receipt_data.get("verification_status", "pendente"),
                notes=receipt_data.get("notes"),
                uploaded_by=receipt_data.get("uploaded_by"),
            )

            self.db.add(receipt)
            await self.db.flush()
            await self.db.refresh(receipt)

            logger.info(
                "Payment receipt created successfully",
                receipt_id=receipt.id,
                invoice_id=receipt.invoice_id,
            )

            return receipt

        except Exception as e:
            logger.error("Error creating payment receipt", error=str(e), receipt_data=receipt_data)
            raise

    async def get_receipt_by_id(self, receipt_id: int) -> Optional[PaymentReceipt]:
        """Get receipt by ID"""
        try:
            query = (
                select(PaymentReceipt)
                .options(joinedload(PaymentReceipt.invoice))
                .where(PaymentReceipt.id == receipt_id)
            )

            result = await self.db.execute(query)
            receipt = result.unique().scalar_one_or_none()

            if receipt:
                logger.info("Payment receipt retrieved successfully", receipt_id=receipt_id)
            else:
                logger.warning("Payment receipt not found", receipt_id=receipt_id)

            return receipt

        except Exception as e:
            logger.error("Error retrieving payment receipt", error=str(e), receipt_id=receipt_id)
            raise

    async def list_payment_receipts(
        self,
        invoice_id: Optional[int] = None,
        verification_status: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 50,
    ) -> Dict[str, Any]:
        """List payment receipts with filtering"""
        try:
            offset = (page - 1) * size

            # Base query
            base_query = select(PaymentReceipt).options(
                joinedload(PaymentReceipt.invoice)
            )

            # Apply filters
            filters = []
            if invoice_id:
                filters.append(PaymentReceipt.invoice_id == invoice_id)
            if verification_status:
                filters.append(PaymentReceipt.verification_status == verification_status)
            if uploaded_by:
                filters.append(PaymentReceipt.uploaded_by == uploaded_by)
            if start_date:
                filters.append(func.date(PaymentReceipt.upload_date) >= start_date)
            if end_date:
                filters.append(func.date(PaymentReceipt.upload_date) <= end_date)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Count total
            count_query = select(func.count(PaymentReceipt.id))
            if filters:
                count_query = count_query.where(and_(*filters))

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Get paginated results
            query = base_query.order_by(desc(PaymentReceipt.upload_date)).offset(offset).limit(size)
            result = await self.db.execute(query)
            receipts = result.unique().scalars().all()

            logger.info(
                "Payment receipts listed successfully",
                total=total,
                page=page,
                size=size,
            )

            return {
                "receipts": receipts,
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size,
            }

        except Exception as e:
            logger.error("Error listing payment receipts", error=str(e))
            raise

    async def update_receipt_verification(
        self,
        receipt_id: int,
        verification_status: str,
        verified_by: int,
        notes: Optional[str] = None
    ) -> Optional[PaymentReceipt]:
        """Update receipt verification status"""
        try:
            update_data = {
                "verification_status": verification_status,
                "verified_by": verified_by,
                "verified_at": datetime.utcnow(),
            }

            if notes:
                update_data["notes"] = notes

            stmt = (
                update(PaymentReceipt)
                .where(PaymentReceipt.id == receipt_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated receipt
            receipt = await self.get_receipt_by_id(receipt_id)

            logger.info("Receipt verification updated successfully", receipt_id=receipt_id, status=verification_status)
            return receipt

        except Exception as e:
            logger.error("Error updating receipt verification", error=str(e), receipt_id=receipt_id)
            raise

    # ==========================================
    # DASHBOARD AND ANALYTICS METHODS
    # ==========================================

    async def get_billing_dashboard_metrics(self, company_id: Optional[int] = None) -> Dict[str, Any]:
        """Get billing dashboard metrics"""
        try:
            base_query = select(ContractInvoice)

            if company_id:
                base_query = base_query.join(Contract).join(Client).where(Client.company_id == company_id)

            # Total pending invoices
            pending_query = base_query.where(ContractInvoice.status.in_(["pendente", "enviada"]))
            pending_result = await self.db.execute(
                select(
                    func.count(ContractInvoice.id),
                    func.coalesce(func.sum(ContractInvoice.total_amount), 0)
                ).select_from(pending_query.subquery())
            )
            pending_count, pending_amount = pending_result.first() or (0, Decimal("0"))

            # Total overdue invoices
            overdue_query = base_query.where(
                and_(
                    ContractInvoice.due_date < date.today(),
                    ContractInvoice.status.in_(["pendente", "enviada"])
                )
            )
            overdue_result = await self.db.execute(
                select(
                    func.count(ContractInvoice.id),
                    func.coalesce(func.sum(ContractInvoice.total_amount), 0)
                ).select_from(overdue_query.subquery())
            )
            overdue_count, overdue_amount = overdue_result.first() or (0, Decimal("0"))

            # Current month metrics
            current_month_start = date.today().replace(day=1)
            next_month = (current_month_start.replace(month=current_month_start.month + 1)
                         if current_month_start.month < 12
                         else current_month_start.replace(year=current_month_start.year + 1, month=1))

            # Paid this month
            paid_this_month_query = base_query.where(
                and_(
                    ContractInvoice.status == "paga",
                    ContractInvoice.paid_date >= current_month_start,
                    ContractInvoice.paid_date < next_month
                )
            )
            paid_this_month_result = await self.db.execute(
                select(func.coalesce(func.sum(ContractInvoice.total_amount), 0))
                .select_from(paid_this_month_query.subquery())
            )
            paid_this_month = paid_this_month_result.scalar() or Decimal("0")

            # Expected this month (issued this month)
            expected_this_month_query = base_query.where(
                and_(
                    ContractInvoice.issued_date >= current_month_start,
                    ContractInvoice.issued_date < next_month
                )
            )
            expected_this_month_result = await self.db.execute(
                select(func.coalesce(func.sum(ContractInvoice.total_amount), 0))
                .select_from(expected_this_month_query.subquery())
            )
            expected_this_month = expected_this_month_result.scalar() or Decimal("0")

            # Collection rate
            collection_rate = (
                (paid_this_month / expected_this_month * 100)
                if expected_this_month > 0
                else Decimal("0")
            )

            return {
                "total_pending_invoices": pending_count,
                "total_pending_amount": pending_amount,
                "total_overdue_invoices": overdue_count,
                "total_overdue_amount": overdue_amount,
                "total_paid_this_month": paid_this_month,
                "total_expected_this_month": expected_this_month,
                "collection_rate_percentage": collection_rate.quantize(Decimal("0.01")),
            }

        except Exception as e:
            logger.error("Error getting billing dashboard metrics", error=str(e))
            raise

    async def get_contracts_billing_status(self, company_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get billing status for all contracts"""
        try:
            # Get contracts with their billing information
            query = (
                select(
                    Contract.id,
                    Contract.contract_number,
                    People.name.label("client_name"),
                    Contract.monthly_value,
                    func.count(ContractInvoice.id).filter(
                        ContractInvoice.status.in_(["pendente", "enviada"])
                    ).label("pending_invoices"),
                    func.coalesce(
                        func.sum(ContractInvoice.total_amount).filter(
                            ContractInvoice.status.in_(["pendente", "enviada"])
                        ), 0
                    ).label("pending_amount"),
                    func.count(ContractInvoice.id).filter(
                        and_(
                            ContractInvoice.due_date < func.current_date(),
                            ContractInvoice.status.in_(["pendente", "enviada"])
                        )
                    ).label("overdue_invoices"),
                    func.coalesce(
                        func.sum(ContractInvoice.total_amount).filter(
                            and_(
                                ContractInvoice.due_date < func.current_date(),
                                ContractInvoice.status.in_(["pendente", "enviada"])
                            )
                        ), 0
                    ).label("overdue_amount"),
                    func.max(ContractInvoice.paid_date).filter(
                        ContractInvoice.status == "paga"
                    ).label("last_payment_date"),
                    ContractBillingSchedule.next_billing_date,
                    Contract.status,
                )
                .select_from(Contract)
                .join(Client, Contract.client_id == Client.id)
                .join(People, Client.person_id == People.id)
                .outerjoin(ContractInvoice, Contract.id == ContractInvoice.contract_id)
                .outerjoin(ContractBillingSchedule, Contract.id == ContractBillingSchedule.contract_id)
                .where(Contract.status == "active")
                .group_by(
                    Contract.id,
                    Contract.contract_number,
                    People.name,
                    Contract.monthly_value,
                    ContractBillingSchedule.next_billing_date,
                    Contract.status,
                )
                .order_by(Contract.contract_number)
            )

            if company_id:
                query = query.where(Client.company_id == company_id)

            result = await self.db.execute(query)
            contracts_data = result.all()

            contracts_status = []
            for row in contracts_data:
                contracts_status.append({
                    "contract_id": row.id,
                    "contract_number": row.contract_number,
                    "client_name": row.client_name,
                    "monthly_value": row.monthly_value or Decimal("0"),
                    "pending_invoices": row.pending_invoices,
                    "pending_amount": row.pending_amount,
                    "overdue_invoices": row.overdue_invoices,
                    "overdue_amount": row.overdue_amount,
                    "last_payment_date": row.last_payment_date,
                    "next_billing_date": row.next_billing_date,
                    "status": row.status,
                })

            return contracts_status

        except Exception as e:
            logger.error("Error getting contracts billing status", error=str(e))
            raise

    async def get_upcoming_billings(self, days_ahead: int = 30, company_id: Optional[int] = None) -> List[ContractBillingSchedule]:
        """Get upcoming billing schedules"""
        try:
            cutoff_date = date.today() + timedelta(days=days_ahead)

            query = (
                select(ContractBillingSchedule)
                .options(joinedload(ContractBillingSchedule.contract))
                .where(
                    and_(
                        ContractBillingSchedule.is_active == True,
                        ContractBillingSchedule.next_billing_date <= cutoff_date
                    )
                )
                .order_by(ContractBillingSchedule.next_billing_date)
            )

            if company_id:
                query = query.join(Contract).join(Client).where(Client.company_id == company_id)

            result = await self.db.execute(query)
            upcoming_billings = result.unique().scalars().all()

            return upcoming_billings

        except Exception as e:
            logger.error("Error getting upcoming billings", error=str(e))
            raise

    # ==========================================
    # BULK OPERATIONS
    # ==========================================

    async def bulk_generate_invoices(
        self,
        contract_ids: Optional[List[int]] = None,
        billing_date: Optional[date] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate invoices for multiple contracts"""
        try:
            if billing_date is None:
                billing_date = date.today()

            # Get billing schedules to process
            query = (
                select(ContractBillingSchedule)
                .options(joinedload(ContractBillingSchedule.contract))
                .where(
                    and_(
                        ContractBillingSchedule.is_active == True,
                        ContractBillingSchedule.next_billing_date <= billing_date
                    )
                )
            )

            if contract_ids:
                query = query.where(ContractBillingSchedule.contract_id.in_(contract_ids))

            result = await self.db.execute(query)
            schedules = result.unique().scalars().all()

            generated_invoices = []
            errors = []
            successful = 0

            for schedule in schedules:
                try:
                    # Check if invoice already exists for this period (unless force regenerate)
                    if not force_regenerate:
                        existing_query = (
                            select(ContractInvoice)
                            .where(
                                and_(
                                    ContractInvoice.contract_id == schedule.contract_id,
                                    ContractInvoice.billing_period_start <= billing_date,
                                    ContractInvoice.billing_period_end >= billing_date
                                )
                            )
                        )
                        existing_result = await self.db.execute(existing_query)
                        existing_invoice = existing_result.scalar_one_or_none()

                        if existing_invoice:
                            errors.append(f"Invoice already exists for contract {schedule.contract_id}")
                            continue

                    # Calculate billing period
                    if schedule.billing_cycle == "MONTHLY":
                        billing_period_start = billing_date.replace(day=1)
                        next_month = billing_period_start.replace(month=billing_period_start.month + 1) if billing_period_start.month < 12 else billing_period_start.replace(year=billing_period_start.year + 1, month=1)
                        billing_period_end = next_month - timedelta(days=1)
                        due_date = billing_date + timedelta(days=30)
                    elif schedule.billing_cycle == "QUARTERLY":
                        # Calculate quarter start
                        quarter_start_month = ((billing_date.month - 1) // 3) * 3 + 1
                        billing_period_start = billing_date.replace(month=quarter_start_month, day=1)
                        billing_period_end = (billing_period_start + timedelta(days=90)).replace(day=1) - timedelta(days=1)
                        due_date = billing_date + timedelta(days=30)
                    else:
                        billing_period_start = billing_date.replace(day=1)
                        billing_period_end = billing_period_start.replace(day=28)  # Safe day for any month
                        due_date = billing_date + timedelta(days=30)

                    # Count active lives for the contract
                    lives_query = select(func.count()).select_from(
                        select(1)
                        .select_from(Contract)
                        .join(schedule.contract.lives)
                        .where(
                            and_(
                                Contract.id == schedule.contract_id,
                                or_(
                                    schedule.contract.lives.c.end_date == None,
                                    schedule.contract.lives.c.end_date >= billing_date
                                )
                            )
                        )
                        .subquery()
                    )
                    lives_result = await self.db.execute(lives_query)
                    lives_count = lives_result.scalar() or schedule.contract.lives_contracted

                    # Create invoice
                    invoice_data = {
                        "contract_id": schedule.contract_id,
                        "billing_period_start": billing_period_start,
                        "billing_period_end": billing_period_end,
                        "lives_count": lives_count,
                        "base_amount": schedule.amount_per_cycle,
                        "total_amount": schedule.amount_per_cycle,
                        "due_date": due_date,
                        "status": "enviada",
                    }

                    invoice = await self.create_invoice(invoice_data)
                    generated_invoices.append(invoice.id)
                    successful += 1

                except Exception as e:
                    error_msg = f"Error generating invoice for contract {schedule.contract_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Bulk invoice generation error", error=error_msg)

            return {
                "total_processed": len(schedules),
                "successful": successful,
                "failed": len(errors),
                "errors": errors,
                "generated_invoices": generated_invoices,
            }

        except Exception as e:
            logger.error("Error in bulk invoice generation", error=str(e))
            raise

    # ==========================================
    # PAGBANK INTEGRATION METHODS
    # ==========================================

    async def update_billing_method(
        self,
        schedule_id: int,
        billing_method: str,
        pagbank_data: Optional[Dict] = None
    ) -> Optional[ContractBillingSchedule]:
        """Update billing method and PagBank data for a schedule"""
        try:
            update_data = {
                "billing_method": billing_method,
                "updated_at": datetime.utcnow()
            }

            # Add PagBank specific fields if provided
            if pagbank_data:
                if "pagbank_subscription_id" in pagbank_data:
                    update_data["pagbank_subscription_id"] = pagbank_data["pagbank_subscription_id"]
                if "pagbank_customer_id" in pagbank_data:
                    update_data["pagbank_customer_id"] = pagbank_data["pagbank_customer_id"]
                if "auto_fallback_enabled" in pagbank_data:
                    update_data["auto_fallback_enabled"] = pagbank_data["auto_fallback_enabled"]

            # Reset attempt count when switching to recurrent
            if billing_method == "recurrent":
                update_data["attempt_count"] = 0
                update_data["last_attempt_date"] = None

            stmt = (
                update(ContractBillingSchedule)
                .where(ContractBillingSchedule.id == schedule_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated schedule
            schedule = await self.get_billing_schedule_by_id(schedule_id)

            logger.info(
                "Billing method updated successfully",
                schedule_id=schedule_id,
                billing_method=billing_method
            )

            return schedule

        except Exception as e:
            logger.error(
                "Error updating billing method",
                error=str(e),
                schedule_id=schedule_id,
                billing_method=billing_method
            )
            raise

    async def create_pagbank_transaction(self, transaction_data: Dict[str, Any]) -> PagBankTransaction:
        """Create PagBank transaction record"""
        try:
            transaction = PagBankTransaction(
                invoice_id=transaction_data["invoice_id"],
                transaction_type=transaction_data["transaction_type"],
                pagbank_transaction_id=transaction_data.get("pagbank_transaction_id"),
                pagbank_charge_id=transaction_data.get("pagbank_charge_id"),
                status=transaction_data["status"],
                amount=transaction_data["amount"],
                payment_method=transaction_data.get("payment_method"),
                error_message=transaction_data.get("error_message"),
                webhook_data=transaction_data.get("webhook_data"),
            )

            self.db.add(transaction)
            await self.db.flush()
            await self.db.refresh(transaction)

            logger.info(
                "PagBank transaction created successfully",
                transaction_id=transaction.id,
                invoice_id=transaction.invoice_id,
                type=transaction.transaction_type
            )

            return transaction

        except Exception as e:
            logger.error(
                "Error creating PagBank transaction",
                error=str(e),
                transaction_data=transaction_data
            )
            raise

    async def update_pagbank_transaction_status(
        self,
        transaction_id: int,
        status: str,
        webhook_data: Optional[Dict] = None
    ) -> Optional[PagBankTransaction]:
        """Update PagBank transaction status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }

            if webhook_data:
                update_data["webhook_data"] = webhook_data

                # Extract additional data from webhook if available
                if "payment_method" in webhook_data:
                    update_data["payment_method"] = webhook_data["payment_method"]
                if "error" in webhook_data:
                    update_data["error_message"] = str(webhook_data["error"])

            stmt = (
                update(PagBankTransaction)
                .where(PagBankTransaction.id == transaction_id)
                .values(**update_data)
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Get updated transaction
            query = select(PagBankTransaction).where(PagBankTransaction.id == transaction_id)
            result = await self.db.execute(query)
            transaction = result.scalar_one_or_none()

            logger.info(
                "PagBank transaction status updated",
                transaction_id=transaction_id,
                status=status
            )

            return transaction

        except Exception as e:
            logger.error(
                "Error updating PagBank transaction status",
                error=str(e),
                transaction_id=transaction_id
            )
            raise

    async def get_failed_recurrent_billings(self, days_back: int = 7) -> List[ContractBillingSchedule]:
        """Get billing schedules with failed recurrent payments for fallback processing"""
        try:
            cutoff_date = date.today() - timedelta(days=days_back)
            max_attempts = 3  # Configure this in settings

            query = (
                select(ContractBillingSchedule)
                .options(joinedload(ContractBillingSchedule.contract))
                .where(
                    and_(
                        ContractBillingSchedule.billing_method == "recurrent",
                        ContractBillingSchedule.auto_fallback_enabled == True,
                        ContractBillingSchedule.attempt_count >= max_attempts,
                        ContractBillingSchedule.last_attempt_date >= cutoff_date,
                        ContractBillingSchedule.is_active == True
                    )
                )
                .order_by(ContractBillingSchedule.last_attempt_date.desc())
            )

            result = await self.db.execute(query)
            failed_schedules = result.unique().scalars().all()

            logger.info(
                "Retrieved failed recurrent billings",
                count=len(failed_schedules),
                days_back=days_back
            )

            return failed_schedules

        except Exception as e:
            logger.error("Error getting failed recurrent billings", error=str(e))
            raise

    async def get_pagbank_transactions_by_invoice(self, invoice_id: int) -> List[PagBankTransaction]:
        """Get all PagBank transactions for an invoice"""
        try:
            query = (
                select(PagBankTransaction)
                .where(PagBankTransaction.invoice_id == invoice_id)
                .order_by(desc(PagBankTransaction.created_at))
            )

            result = await self.db.execute(query)
            transactions = result.scalars().all()

            return transactions

        except Exception as e:
            logger.error(
                "Error getting PagBank transactions by invoice",
                error=str(e),
                invoice_id=invoice_id
            )
            raise

    async def get_recurrent_billing_schedules(
        self,
        company_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[ContractBillingSchedule]:
        """Get all recurrent billing schedules"""
        try:
            filters = [ContractBillingSchedule.billing_method == "recurrent"]

            if not include_inactive:
                filters.append(ContractBillingSchedule.is_active == True)

            query = (
                select(ContractBillingSchedule)
                .options(
                    joinedload(ContractBillingSchedule.contract)
                    .joinedload(Contract.client)
                    .joinedload(Client.person)
                )
                .where(and_(*filters))
            )

            if company_id:
                query = query.join(Contract).join(Client).where(Client.company_id == company_id)

            result = await self.db.execute(query)
            schedules = result.unique().scalars().all()

            logger.info(
                "Retrieved recurrent billing schedules",
                count=len(schedules),
                company_id=company_id
            )

            return schedules

        except Exception as e:
            logger.error("Error getting recurrent billing schedules", error=str(e))
            raise

    async def get_billing_schedule_by_pagbank_subscription(
        self,
        subscription_id: str
    ) -> Optional[ContractBillingSchedule]:
        """Get billing schedule by PagBank subscription ID"""
        try:
            query = (
                select(ContractBillingSchedule)
                .options(joinedload(ContractBillingSchedule.contract))
                .where(ContractBillingSchedule.pagbank_subscription_id == subscription_id)
            )

            result = await self.db.execute(query)
            schedule = result.unique().scalar_one_or_none()

            if schedule:
                logger.info(
                    "Found billing schedule by PagBank subscription",
                    schedule_id=schedule.id,
                    subscription_id=subscription_id
                )
            else:
                logger.warning(
                    "Billing schedule not found for PagBank subscription",
                    subscription_id=subscription_id
                )

            return schedule

        except Exception as e:
            logger.error(
                "Error getting billing schedule by PagBank subscription",
                error=str(e),
                subscription_id=subscription_id
            )
            raise

    async def get_pagbank_transaction_by_charge_id(
        self,
        charge_id: str
    ) -> Optional[PagBankTransaction]:
        """Get PagBank transaction by charge ID"""
        try:
            query = (
                select(PagBankTransaction)
                .where(PagBankTransaction.pagbank_charge_id == charge_id)
            )

            result = await self.db.execute(query)
            transaction = result.scalar_one_or_none()

            return transaction

        except Exception as e:
            logger.error(
                "Error getting PagBank transaction by charge ID",
                error=str(e),
                charge_id=charge_id
            )
            raise

    async def increment_billing_attempt(self, schedule_id: int) -> None:
        """Increment attempt count for a billing schedule"""
        try:
            stmt = (
                update(ContractBillingSchedule)
                .where(ContractBillingSchedule.id == schedule_id)
                .values(
                    attempt_count=ContractBillingSchedule.attempt_count + 1,
                    last_attempt_date=date.today(),
                    updated_at=datetime.utcnow()
                )
            )

            await self.db.execute(stmt)
            await self.db.flush()

            logger.info("Billing attempt count incremented", schedule_id=schedule_id)

        except Exception as e:
            logger.error(
                "Error incrementing billing attempt",
                error=str(e),
                schedule_id=schedule_id
            )
            raise