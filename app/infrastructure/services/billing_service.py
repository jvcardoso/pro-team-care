import mimetypes
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.orm.models import (
    Contract,
    ContractBillingSchedule,
    ContractInvoice,
    ContractLive,
    PaymentReceipt,
)
from app.infrastructure.repositories.billing_repository import BillingRepository
from app.infrastructure.repositories.contract_repository import ContractRepository
from app.infrastructure.services.pagbank_service import PagBankService

logger = structlog.get_logger()


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.billing_repository = BillingRepository(db)
        self.contract_repository = ContractRepository(db)
        self.pagbank_service = PagBankService()

    # ==========================================
    # AUTOMATIC BILLING METHODS
    # ==========================================

    async def run_automatic_billing(
        self, billing_date: Optional[date] = None, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Run automatic billing process for all due schedules"""
        try:
            if billing_date is None:
                billing_date = date.today()

            logger.info(
                "Starting automatic billing process",
                billing_date=billing_date,
                force_regenerate=force_regenerate,
            )

            # Get all schedules that are due for billing
            due_schedules = await self._get_due_billing_schedules(billing_date)

            generated_invoices = []
            errors = []
            successful = 0

            for schedule in due_schedules:
                try:
                    invoice = await self._generate_invoice_for_schedule(
                        schedule, billing_date, force_regenerate
                    )
                    if invoice:
                        generated_invoices.append(invoice.id)
                        successful += 1
                        logger.info(
                            "Invoice generated successfully",
                            schedule_id=schedule.id,
                            contract_id=schedule.contract_id,
                            invoice_id=invoice.id,
                        )
                except Exception as e:
                    error_msg = (
                        f"Error generating invoice for schedule {schedule.id}: {str(e)}"
                    )
                    errors.append(error_msg)
                    logger.error(
                        "Invoice generation failed",
                        error=error_msg,
                        schedule_id=schedule.id,
                    )

            # Update overdue invoices status
            await self._update_overdue_invoices()

            result = {
                "total_schedules_processed": len(due_schedules),
                "successful_invoices": successful,
                "failed_invoices": len(errors),
                "generated_invoice_ids": generated_invoices,
                "errors": errors,
                "billing_date": billing_date.isoformat(),
            }

            logger.info("Automatic billing process completed", result=result)
            return result

        except Exception as e:
            logger.error("Automatic billing process failed", error=str(e))
            raise

    async def _get_due_billing_schedules(
        self, billing_date: date
    ) -> List[ContractBillingSchedule]:
        """Get all billing schedules that are due for billing"""
        try:
            # Get schedules where next_billing_date <= billing_date and is_active = true
            query = (
                select(ContractBillingSchedule)
                .where(
                    and_(
                        ContractBillingSchedule.next_billing_date <= billing_date,
                        ContractBillingSchedule.is_active == True,
                    )
                )
                .order_by(ContractBillingSchedule.next_billing_date)
            )

            result = await self.db.execute(query)
            schedules = result.scalars().all()

            logger.info(
                f"Found {len(schedules)} due billing schedules",
                billing_date=billing_date,
            )
            return schedules

        except Exception as e:
            logger.error("Error getting due billing schedules", error=str(e))
            raise

    async def _generate_invoice_for_schedule(
        self,
        schedule: ContractBillingSchedule,
        billing_date: date,
        force_regenerate: bool = False,
    ) -> Optional[ContractInvoice]:
        """Generate invoice for a specific billing schedule"""
        try:
            # Get contract details
            contract = await self.contract_repository.get_contract_by_id(
                schedule.contract_id
            )
            if not contract or contract.status != "active":
                logger.warning(
                    "Skipping inactive contract",
                    contract_id=schedule.contract_id,
                    status=contract.status if contract else "not_found",
                )
                return None

            # Calculate billing period based on cycle
            billing_period = self._calculate_billing_period(
                schedule.billing_cycle, billing_date
            )

            # Check if invoice already exists for this period
            if not force_regenerate:
                existing_invoice = await self._check_existing_invoice(
                    schedule.contract_id, billing_period["start"], billing_period["end"]
                )
                if existing_invoice:
                    logger.info(
                        "Invoice already exists for period",
                        contract_id=schedule.contract_id,
                        period_start=billing_period["start"],
                        period_end=billing_period["end"],
                    )
                    return existing_invoice

            # Count active lives for the billing period
            lives_count = await self._count_active_lives(
                contract, billing_period["end"]
            )

            # Calculate amounts
            base_amount = schedule.amount_per_cycle
            additional_services_amount = await self._calculate_additional_services(
                contract, billing_period["start"], billing_period["end"]
            )

            # Calculate due date (typically 30 days from issue date)
            due_date = billing_date + timedelta(days=30)

            # Create invoice data
            invoice_data = {
                "contract_id": schedule.contract_id,
                "billing_period_start": billing_period["start"],
                "billing_period_end": billing_period["end"],
                "lives_count": lives_count,
                "base_amount": base_amount,
                "additional_services_amount": additional_services_amount,
                "total_amount": base_amount + additional_services_amount,
                "due_date": due_date,
                "issued_date": billing_date,
                "status": "enviada",  # Automatically set as sent
            }

            # Create invoice
            invoice = await self.billing_repository.create_invoice(invoice_data)

            return invoice

        except Exception as e:
            logger.error(
                "Error generating invoice for schedule",
                error=str(e),
                schedule_id=schedule.id,
                contract_id=schedule.contract_id,
            )
            raise

    def _calculate_billing_period(
        self, billing_cycle: str, billing_date: date
    ) -> Dict[str, date]:
        """Calculate billing period start and end dates based on cycle"""
        if billing_cycle == "MONTHLY":
            # Monthly: first day of month to last day of month
            start_date = billing_date.replace(day=1)
            if billing_date.month == 12:
                end_date = billing_date.replace(
                    year=billing_date.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_date = billing_date.replace(
                    month=billing_date.month + 1, day=1
                ) - timedelta(days=1)

        elif billing_cycle == "QUARTERLY":
            # Quarterly: start of quarter to end of quarter
            quarter_start_month = ((billing_date.month - 1) // 3) * 3 + 1
            start_date = billing_date.replace(month=quarter_start_month, day=1)

            if quarter_start_month == 10:  # Q4
                end_date = billing_date.replace(
                    year=billing_date.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_date = billing_date.replace(
                    month=quarter_start_month + 3, day=1
                ) - timedelta(days=1)

        elif billing_cycle == "SEMI_ANNUAL":
            # Semi-annual: 6 months periods
            if billing_date.month <= 6:
                start_date = billing_date.replace(month=1, day=1)
                end_date = billing_date.replace(month=6, day=30)
            else:
                start_date = billing_date.replace(month=7, day=1)
                end_date = billing_date.replace(month=12, day=31)

        elif billing_cycle == "ANNUAL":
            # Annual: January 1 to December 31
            start_date = billing_date.replace(month=1, day=1)
            end_date = billing_date.replace(month=12, day=31)

        else:  # Default to monthly
            start_date = billing_date.replace(day=1)
            if billing_date.month == 12:
                end_date = billing_date.replace(
                    year=billing_date.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_date = billing_date.replace(
                    month=billing_date.month + 1, day=1
                ) - timedelta(days=1)

        return {"start": start_date, "end": end_date}

    async def _check_existing_invoice(
        self, contract_id: int, period_start: date, period_end: date
    ) -> Optional[ContractInvoice]:
        """Check if invoice already exists for the given period"""
        try:
            query = select(ContractInvoice).where(
                and_(
                    ContractInvoice.contract_id == contract_id,
                    ContractInvoice.billing_period_start <= period_end,
                    ContractInvoice.billing_period_end >= period_start,
                )
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("Error checking existing invoice", error=str(e))
            return None

    async def _count_active_lives(self, contract: Contract, period_end: date) -> int:
        """Count active lives for a contract at the end of billing period"""
        try:
            query = select(func.count(ContractLive.id)).where(
                and_(
                    ContractLive.contract_id == contract.id,
                    ContractLive.status == "active",
                    ContractLive.start_date <= period_end,
                    or_(
                        ContractLive.end_date.is_(None),
                        ContractLive.end_date >= period_end,
                    ),
                )
            )

            result = await self.db.execute(query)
            count = result.scalar() or 0

            # If no active lives found, use contracted lives as fallback
            return max(count, contract.lives_contracted)

        except Exception as e:
            logger.error("Error counting active lives", error=str(e))
            return contract.lives_contracted

    async def _calculate_additional_services(
        self, contract: Contract, period_start: date, period_end: date
    ) -> Decimal:
        """Calculate additional services amount for the billing period"""
        try:
            # This would integrate with service executions
            # For now, return 0 as additional services calculation can be complex
            # TODO: Implement based on service_executions table when needed
            return Decimal("0.00")

        except Exception as e:
            logger.error("Error calculating additional services", error=str(e))
            return Decimal("0.00")

    async def _update_overdue_invoices(self):
        """Update status of overdue invoices"""
        try:
            from sqlalchemy import update

            # Update invoices that are past due date and still pending/sent
            stmt = (
                update(ContractInvoice)
                .where(
                    and_(
                        ContractInvoice.due_date < date.today(),
                        ContractInvoice.status.in_(["pendente", "enviada"]),
                    )
                )
                .values(status="vencida", updated_at=datetime.utcnow())
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            updated_count = result.rowcount
            if updated_count > 0:
                logger.info(f"Updated {updated_count} invoices to overdue status")

        except Exception as e:
            logger.error("Error updating overdue invoices", error=str(e))

    # ==========================================
    # FILE UPLOAD METHODS
    # ==========================================

    async def upload_payment_receipt(
        self,
        invoice_id: int,
        file_name: str,
        file_content: bytes,
        file_type: str,
        notes: Optional[str] = None,
        uploaded_by: Optional[int] = None,
    ) -> PaymentReceipt:
        """Upload and store a payment receipt file"""
        try:
            # Validate invoice exists
            invoice = await self.billing_repository.get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            # Generate unique filename
            file_extension = self._get_file_extension(file_name, file_type)
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Create upload directory if it doesn't exist
            upload_dir = self._get_upload_directory()
            os.makedirs(upload_dir, exist_ok=True)

            # Save file to disk
            file_path = os.path.join(upload_dir, unique_filename)
            await self._save_file_to_disk(file_path, file_content)

            # Create receipt record
            receipt_data = {
                "invoice_id": invoice_id,
                "file_name": file_name,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": len(file_content),
                "notes": notes,
                "uploaded_by": uploaded_by,
            }

            receipt = await self.billing_repository.create_payment_receipt(receipt_data)

            logger.info(
                "Payment receipt uploaded successfully",
                receipt_id=receipt.id,
                invoice_id=invoice_id,
                file_name=file_name,
                file_size=len(file_content),
            )

            return receipt

        except Exception as e:
            logger.error(
                "Error uploading payment receipt",
                error=str(e),
                invoice_id=invoice_id,
                file_name=file_name,
            )
            raise

    def _get_file_extension(self, file_name: str, file_type: str) -> str:
        """Get file extension from filename or content type"""
        # Try to get extension from filename first
        if "." in file_name:
            return "." + file_name.split(".")[-1].lower()

        # Fall back to content type mapping
        extension_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "application/pdf": ".pdf",
        }

        return extension_map.get(file_type, ".bin")

    def _get_upload_directory(self) -> str:
        """Get the upload directory for payment receipts"""
        # Create directory structure: uploads/receipts/YYYY/MM/
        now = datetime.now()
        upload_dir = os.path.join(
            "uploads", "receipts", str(now.year), f"{now.month:02d}"
        )
        return upload_dir

    async def _save_file_to_disk(self, file_path: str, file_content: bytes):
        """Save file content to disk asynchronously"""
        try:
            import aiofiles

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)

        except ImportError:
            # Fallback to synchronous write if aiofiles is not available
            with open(file_path, "wb") as f:
                f.write(file_content)

    # ==========================================
    # BUSINESS LOGIC METHODS
    # ==========================================

    async def calculate_contract_monthly_revenue(
        self, contract_id: int
    ) -> Dict[str, Any]:
        """Calculate monthly revenue for a specific contract"""
        try:
            # Get contract
            contract = await self.contract_repository.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            # Get billing schedule
            schedule = await self.billing_repository.get_billing_schedule_by_contract(
                contract_id
            )
            if not schedule:
                return {
                    "contract_id": contract_id,
                    "monthly_revenue": Decimal("0.00"),
                    "error": "No billing schedule found",
                }

            # Calculate monthly equivalent
            monthly_revenue = self._convert_to_monthly_amount(
                schedule.amount_per_cycle, schedule.billing_cycle
            )

            return {
                "contract_id": contract_id,
                "contract_number": contract.contract_number,
                "billing_cycle": schedule.billing_cycle,
                "amount_per_cycle": schedule.amount_per_cycle,
                "monthly_revenue": monthly_revenue,
                "next_billing_date": schedule.next_billing_date,
            }

        except Exception as e:
            logger.error(
                "Error calculating contract monthly revenue",
                error=str(e),
                contract_id=contract_id,
            )
            raise

    def _convert_to_monthly_amount(
        self, amount: Decimal, billing_cycle: str
    ) -> Decimal:
        """Convert amount to monthly equivalent based on billing cycle"""
        conversion_factors = {
            "MONTHLY": Decimal("1.0"),
            "QUARTERLY": Decimal("0.33333"),  # 1/3
            "SEMI_ANNUAL": Decimal("0.16667"),  # 1/6
            "ANNUAL": Decimal("0.08333"),  # 1/12
        }

        factor = conversion_factors.get(billing_cycle, Decimal("1.0"))
        return (amount * factor).quantize(Decimal("0.01"))

    async def forecast_revenue(
        self, months_ahead: int = 12, company_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Forecast revenue for the next N months"""
        try:
            # Get all active billing schedules
            schedules_result = await self.billing_repository.list_billing_schedules(
                is_active=True, page=1, size=1000
            )
            schedules = schedules_result["schedules"]

            # Calculate monthly forecast
            monthly_forecast = {}
            current_date = date.today()

            for month in range(months_ahead):
                forecast_date = current_date + timedelta(days=30 * month)
                month_key = forecast_date.strftime("%Y-%m")

                monthly_revenue = Decimal("0.00")
                for schedule in schedules:
                    monthly_equivalent = self._convert_to_monthly_amount(
                        schedule.amount_per_cycle, schedule.billing_cycle
                    )
                    monthly_revenue += monthly_equivalent

                monthly_forecast[month_key] = monthly_revenue

            total_forecast = sum(monthly_forecast.values())

            return {
                "months_ahead": months_ahead,
                "monthly_forecast": monthly_forecast,
                "total_forecast": total_forecast,
                "average_monthly": (
                    total_forecast / months_ahead
                    if months_ahead > 0
                    else Decimal("0.00")
                ),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error forecasting revenue", error=str(e))
            raise

    async def generate_billing_summary_report(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Generate billing summary report for a date range"""
        try:
            # Get invoices for the period
            invoices_result = await self.billing_repository.list_invoices(
                start_date=start_date, end_date=end_date, page=1, size=1000
            )
            invoices = invoices_result["invoices"]

            # Calculate totals by status
            status_summary = {}
            total_amount = Decimal("0.00")
            total_paid = Decimal("0.00")
            total_pending = Decimal("0.00")

            for invoice in invoices:
                status = invoice.status
                amount = invoice.total_amount

                if status not in status_summary:
                    status_summary[status] = {"count": 0, "amount": Decimal("0.00")}

                status_summary[status]["count"] += 1
                status_summary[status]["amount"] += amount

                total_amount += amount
                if status == "paga":
                    total_paid += amount
                elif status in ["pendente", "enviada"]:
                    total_pending += amount

            # Calculate collection rate
            collection_rate = (
                (total_paid / total_amount * 100)
                if total_amount > 0
                else Decimal("0.00")
            )

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_invoices": len(invoices),
                    "total_amount": total_amount,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "collection_rate": collection_rate.quantize(Decimal("0.01")),
                },
                "status_breakdown": status_summary,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error generating billing summary report", error=str(e))
            raise

    # ==========================================
    # PAGBANK INTEGRATION METHODS
    # ==========================================

    async def setup_recurrent_billing(
        self, contract_id: int, client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Setup recurrent billing with PagBank for a contract"""
        try:
            # Get contract and billing schedule
            contract = await self.contract_repository.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")

            schedule = await self.billing_repository.get_billing_schedule_by_contract(
                contract_id
            )
            if not schedule:
                raise ValueError(
                    f"No billing schedule found for contract {contract_id}"
                )

            # Prepare contract data for PagBank
            contract_data = {
                "contract_id": contract.id,
                "contract_number": contract.contract_number,
                "plan_name": contract.plan_name,
                "monthly_value": schedule.amount_per_cycle,
            }

            # Step 1: Create subscription plan
            logger.info("Creating PagBank subscription plan", contract_id=contract_id)
            plan_result = await self.pagbank_service.create_subscription_plan(
                contract_data
            )

            if not plan_result.get("plan_id"):
                raise Exception(f"Failed to create PagBank plan: {plan_result}")

            # Step 2: Create customer
            logger.info("Creating PagBank customer", contract_id=contract_id)
            customer_result = await self.pagbank_service.create_customer(client_data)

            if not customer_result.get("customer_id"):
                raise Exception(f"Failed to create PagBank customer: {customer_result}")

            # Step 3: Create subscription
            logger.info("Creating PagBank subscription", contract_id=contract_id)
            subscription_result = await self.pagbank_service.create_subscription(
                plan_result["plan_id"],
                customer_result["customer_id"],
                client_data,  # Contains card data
            )

            if not subscription_result.get("subscription_id"):
                raise Exception(
                    f"Failed to create PagBank subscription: {subscription_result}"
                )

            # Step 4: Update billing schedule
            pagbank_data = {
                "pagbank_subscription_id": subscription_result["subscription_id"],
                "pagbank_customer_id": customer_result["customer_id"],
                "auto_fallback_enabled": True,
            }

            updated_schedule = await self.billing_repository.update_billing_method(
                schedule.id, "recurrent", pagbank_data
            )

            logger.info(
                "Recurrent billing setup completed successfully",
                contract_id=contract_id,
                subscription_id=subscription_result["subscription_id"],
            )

            return {
                "success": True,
                "contract_id": contract_id,
                "billing_method": "recurrent",
                "pagbank_subscription_id": subscription_result["subscription_id"],
                "pagbank_customer_id": customer_result["customer_id"],
                "next_billing_date": subscription_result.get("next_billing_date"),
                "setup_details": {
                    "plan": plan_result,
                    "customer": customer_result,
                    "subscription": subscription_result,
                },
            }

        except Exception as e:
            logger.error(
                "Error setting up recurrent billing",
                error=str(e),
                contract_id=contract_id,
            )
            raise

    async def setup_manual_billing(self, contract_id: int) -> Dict[str, Any]:
        """Setup manual billing for a contract"""
        try:
            # Get billing schedule
            schedule = await self.billing_repository.get_billing_schedule_by_contract(
                contract_id
            )
            if not schedule:
                raise ValueError(
                    f"No billing schedule found for contract {contract_id}"
                )

            # Update billing method to manual
            updated_schedule = await self.billing_repository.update_billing_method(
                schedule.id, "manual", {"auto_fallback_enabled": True}
            )

            logger.info("Manual billing setup completed", contract_id=contract_id)

            return {
                "success": True,
                "contract_id": contract_id,
                "billing_method": "manual",
                "schedule_id": schedule.id,
            }

        except Exception as e:
            logger.error(
                "Error setting up manual billing", error=str(e), contract_id=contract_id
            )
            raise

    async def process_recurrent_billing_failure(
        self, schedule_id: int, error_details: Dict
    ) -> Dict[str, Any]:
        """Process failure in recurrent billing and handle fallback"""
        try:
            # Increment attempt count
            await self.billing_repository.increment_billing_attempt(schedule_id)

            # Get updated schedule
            schedule = await self.billing_repository.get_billing_schedule_by_id(
                schedule_id
            )
            if not schedule:
                raise ValueError(f"Billing schedule {schedule_id} not found")

            max_attempts = 3  # Configure this in settings

            result = {
                "schedule_id": schedule_id,
                "contract_id": schedule.contract_id,
                "attempt_count": schedule.attempt_count,
                "max_attempts": max_attempts,
                "fallback_triggered": False,
            }

            # Check if should trigger fallback
            if (
                schedule.attempt_count >= max_attempts
                and schedule.auto_fallback_enabled
            ):
                logger.info(
                    "Triggering fallback to manual billing",
                    schedule_id=schedule_id,
                    attempt_count=schedule.attempt_count,
                )

                # Switch to manual billing
                await self.billing_repository.update_billing_method(
                    schedule.id,
                    "manual",
                    {"pagbank_subscription_id": None, "auto_fallback_enabled": True},
                )

                result["fallback_triggered"] = True
                result["new_billing_method"] = "manual"

                # TODO: Send notification to customer about fallback
                # await self._send_fallback_notification(schedule)

            logger.info(
                "Recurrent billing failure processed",
                schedule_id=schedule_id,
                result=result,
            )

            return result

        except Exception as e:
            logger.error(
                "Error processing recurrent billing failure",
                error=str(e),
                schedule_id=schedule_id,
            )
            raise

    async def create_checkout_for_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Create PagBank checkout session for a specific invoice"""
        try:
            # Get invoice with related data
            invoice = await self.billing_repository.get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            # Get client data from contract relationship
            contract = invoice.contract
            client = contract.client
            person = client.person

            # Get address and contact info
            address = None
            phone = None
            email = None

            if person.addresses:
                address = person.addresses[0]  # Get first address
            if person.phones:
                phone = person.phones[0]  # Get first phone
            if person.emails:
                email = person.emails[0]  # Get first email

            # Prepare invoice data for checkout
            invoice_data = {
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "contract_number": contract.contract_number,
                "total_amount": invoice.total_amount,
                "customer_name": person.name,
                "customer_email": (
                    email.email_address if email else "no-email@proteamcare.com"
                ),
                "customer_tax_id": person.tax_id,
                "customer_phone_area": (
                    phone.number[:2] if phone and len(phone.number) >= 10 else "11"
                ),
                "customer_phone_number": (
                    phone.number[2:]
                    if phone and len(phone.number) >= 10
                    else "999999999"
                ),
            }

            # Create checkout session
            checkout_result = await self.pagbank_service.create_checkout_session(
                invoice_data
            )

            # Create transaction record
            transaction_data = {
                "invoice_id": invoice_id,
                "transaction_type": "checkout",
                "pagbank_transaction_id": checkout_result.get("session_id"),
                "status": "pending",
                "amount": invoice.total_amount,
            }

            transaction = await self.billing_repository.create_pagbank_transaction(
                transaction_data
            )

            logger.info(
                "Checkout session created successfully",
                invoice_id=invoice_id,
                session_id=checkout_result.get("session_id"),
                transaction_id=transaction.id,
            )

            return {
                "success": True,
                "invoice_id": invoice_id,
                "checkout_url": checkout_result.get("checkout_url"),
                "session_id": checkout_result.get("session_id"),
                "expires_at": checkout_result.get("expires_at"),
                "qr_code": checkout_result.get("qr_code"),
                "transaction_id": transaction.id,
            }

        except Exception as e:
            logger.error(
                "Error creating checkout for invoice",
                error=str(e),
                invoice_id=invoice_id,
            )
            raise

    async def run_automatic_recurrent_billing(self) -> Dict[str, Any]:
        """Execute automatic recurrent billing for all due schedules"""
        try:
            logger.info("Starting automatic recurrent billing process")

            # Get all recurrent billing schedules that are due
            recurrent_schedules = (
                await self.billing_repository.get_recurrent_billing_schedules()
            )

            processed = 0
            successful = 0
            failed = 0
            errors = []
            results = []

            today = date.today()

            for schedule in recurrent_schedules:
                try:
                    # Check if billing is due
                    if schedule.next_billing_date > today:
                        continue

                    processed += 1

                    # Get subscription status from PagBank
                    if schedule.pagbank_subscription_id:
                        subscription_status = (
                            await self.pagbank_service.get_subscription_status(
                                schedule.pagbank_subscription_id
                            )
                        )

                        if subscription_status.get("status") == "ACTIVE":
                            # Subscription is active, billing should be automatic
                            # Just create invoice for this period
                            invoice = await self._generate_invoice_for_schedule(
                                schedule, today
                            )

                            if invoice:
                                successful += 1
                                results.append(
                                    {
                                        "schedule_id": schedule.id,
                                        "contract_id": schedule.contract_id,
                                        "status": "success",
                                        "invoice_id": invoice.id,
                                    }
                                )
                            else:
                                failed += 1
                                error_msg = f"Failed to generate invoice for schedule {schedule.id}"
                                errors.append(error_msg)
                                results.append(
                                    {
                                        "schedule_id": schedule.id,
                                        "contract_id": schedule.contract_id,
                                        "status": "failed",
                                        "error": error_msg,
                                    }
                                )
                        else:
                            # Subscription has issues, handle failure
                            failure_result = (
                                await self.process_recurrent_billing_failure(
                                    schedule.id,
                                    {
                                        "subscription_status": subscription_status.get(
                                            "status"
                                        )
                                    },
                                )
                            )

                            failed += 1
                            results.append(
                                {
                                    "schedule_id": schedule.id,
                                    "contract_id": schedule.contract_id,
                                    "status": "failed",
                                    "failure_result": failure_result,
                                }
                            )

                except Exception as e:
                    failed += 1
                    error_msg = f"Error processing schedule {schedule.id}: {str(e)}"
                    errors.append(error_msg)
                    results.append(
                        {
                            "schedule_id": schedule.id,
                            "contract_id": schedule.contract_id,
                            "status": "error",
                            "error": error_msg,
                        }
                    )

            result = {
                "total_processed": processed,
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "results": results,
                "executed_at": datetime.utcnow().isoformat(),
            }

            logger.info("Automatic recurrent billing completed", result=result)
            return result

        except Exception as e:
            logger.error("Error in automatic recurrent billing", error=str(e))
            raise

    async def cancel_recurrent_subscription(self, contract_id: int) -> Dict[str, Any]:
        """Cancel recurrent subscription for a contract"""
        try:
            # Get billing schedule
            schedule = await self.billing_repository.get_billing_schedule_by_contract(
                contract_id
            )
            if not schedule:
                raise ValueError(
                    f"No billing schedule found for contract {contract_id}"
                )

            if (
                schedule.billing_method != "recurrent"
                or not schedule.pagbank_subscription_id
            ):
                return {
                    "success": True,
                    "message": "Contract is not using recurrent billing",
                    "contract_id": contract_id,
                }

            # Cancel subscription in PagBank
            cancel_result = await self.pagbank_service.cancel_subscription(
                schedule.pagbank_subscription_id
            )

            # Update billing schedule to manual
            await self.billing_repository.update_billing_method(
                schedule.id,
                "manual",
                {"pagbank_subscription_id": None, "pagbank_customer_id": None},
            )

            logger.info(
                "Recurrent subscription cancelled successfully",
                contract_id=contract_id,
                subscription_id=schedule.pagbank_subscription_id,
            )

            return {
                "success": True,
                "contract_id": contract_id,
                "cancelled_subscription_id": schedule.pagbank_subscription_id,
                "new_billing_method": "manual",
                "cancellation_details": cancel_result,
            }

        except Exception as e:
            logger.error(
                "Error cancelling recurrent subscription",
                error=str(e),
                contract_id=contract_id,
            )
            raise

    async def get_billing_method_status(self, contract_id: int) -> Dict[str, Any]:
        """Get current billing method status for a contract"""
        try:
            # Get billing schedule
            schedule = await self.billing_repository.get_billing_schedule_by_contract(
                contract_id
            )
            if not schedule:
                raise ValueError(
                    f"No billing schedule found for contract {contract_id}"
                )

            result = {
                "contract_id": contract_id,
                "billing_method": schedule.billing_method,
                "is_active": schedule.is_active,
                "next_billing_date": (
                    schedule.next_billing_date.isoformat()
                    if schedule.next_billing_date
                    else None
                ),
                "auto_fallback_enabled": schedule.auto_fallback_enabled,
                "attempt_count": schedule.attempt_count,
                "last_attempt_date": (
                    schedule.last_attempt_date.isoformat()
                    if schedule.last_attempt_date
                    else None
                ),
            }

            # Add PagBank specific data if recurrent
            if (
                schedule.billing_method == "recurrent"
                and schedule.pagbank_subscription_id
            ):
                try:
                    # Get current subscription status from PagBank
                    subscription_status = (
                        await self.pagbank_service.get_subscription_status(
                            schedule.pagbank_subscription_id
                        )
                    )

                    result["pagbank_data"] = {
                        "subscription_id": schedule.pagbank_subscription_id,
                        "customer_id": schedule.pagbank_customer_id,
                        "subscription_status": subscription_status.get("status"),
                        "next_billing_date": subscription_status.get(
                            "next_billing_date"
                        ),
                    }
                except Exception as e:
                    result["pagbank_data"] = {
                        "subscription_id": schedule.pagbank_subscription_id,
                        "customer_id": schedule.pagbank_customer_id,
                        "status_check_error": str(e),
                    }

            return result

        except Exception as e:
            logger.error(
                "Error getting billing method status",
                error=str(e),
                contract_id=contract_id,
            )
            raise
