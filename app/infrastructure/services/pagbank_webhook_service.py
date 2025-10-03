from typing import Dict, Optional
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.infrastructure.services.pagbank_service import PagBankService
from app.infrastructure.repositories.billing_repository import BillingRepository
from app.infrastructure.orm.models import (
    ContractBillingSchedule,
    ContractInvoice,
    PagBankTransaction
)


class PagBankWebhookService:
    """Service for processing PagBank webhooks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pagbank_service = PagBankService()
        self.billing_repository = BillingRepository(db)

    async def handle_webhook_notification(self, payload: Dict, signature: str) -> Dict:
        """Main webhook handler"""
        try:
            # Verify webhook signature
            payload_str = str(payload)
            is_valid = await self.pagbank_service.verify_webhook_signature(payload_str, signature)

            if not is_valid:
                return {
                    "success": False,
                    "error": "Invalid webhook signature"
                }

            # Process notification based on type
            notification_type = payload.get("type")

            if notification_type == "SUBSCRIPTION":
                return await self.handle_subscription_notification(payload)
            elif notification_type == "PAYMENT":
                return await self.handle_payment_notification(payload)
            elif notification_type == "ORDER":
                return await self.handle_checkout_notification(payload)
            else:
                return {
                    "success": False,
                    "error": f"Unknown notification type: {notification_type}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Webhook processing failed: {str(e)}"
            }

    async def handle_subscription_notification(self, payload: Dict) -> Dict:
        """Process subscription-related notifications"""
        try:
            data = payload.get("data", {})
            subscription_id = data.get("id")
            status = data.get("status")
            reference = data.get("reference")

            if not subscription_id:
                return {
                    "success": False,
                    "error": "Missing subscription_id in notification"
                }

            # Find billing schedule with this subscription
            schedule = await self._find_billing_schedule_by_subscription(subscription_id)
            if not schedule:
                return {
                    "success": False,
                    "error": f"Billing schedule not found for subscription {subscription_id}"
                }

            # Update schedule based on subscription status
            await self._update_schedule_from_subscription_status(schedule, status, data)

            # If subscription payment failed, handle fallback
            if status in ["SUSPENDED", "CANCELLED", "PAYMENT_FAILED"]:
                await self._handle_subscription_failure(schedule, data)

            # If successful payment, reset attempt count
            elif status == "ACTIVE":
                await self._reset_billing_attempts(schedule)

            await self.db.commit()

            return {
                "success": True,
                "subscription_id": subscription_id,
                "status": status,
                "schedule_id": schedule.id
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Subscription notification failed: {str(e)}"
            }

    async def handle_payment_notification(self, payload: Dict) -> Dict:
        """Process payment-related notifications"""
        try:
            data = payload.get("data", {})
            charge_id = data.get("id")
            status = data.get("status")
            reference_id = data.get("reference_id")

            if not charge_id:
                return {
                    "success": False,
                    "error": "Missing charge_id in notification"
                }

            # Find transaction by charge_id or reference
            transaction = await self._find_pagbank_transaction(charge_id, reference_id)
            if not transaction:
                return {
                    "success": False,
                    "error": f"Transaction not found for charge {charge_id}"
                }

            # Update transaction status
            await self._update_transaction_status(transaction, status, data)

            # Update invoice status if payment approved
            if status == "PAID":
                await self._mark_invoice_as_paid(transaction.invoice_id, data)

            await self.db.commit()

            return {
                "success": True,
                "charge_id": charge_id,
                "status": status,
                "transaction_id": transaction.id
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Payment notification failed: {str(e)}"
            }

    async def handle_checkout_notification(self, payload: Dict) -> Dict:
        """Process checkout/order notifications"""
        try:
            data = payload.get("data", {})
            order_id = data.get("id")
            status = data.get("status")
            reference_id = data.get("reference_id")

            if not order_id:
                return {
                    "success": False,
                    "error": "Missing order_id in notification"
                }

            # Extract invoice ID from reference
            invoice_id = self._extract_invoice_id_from_reference(reference_id)
            if not invoice_id:
                return {
                    "success": False,
                    "error": f"Could not extract invoice_id from reference {reference_id}"
                }

            # Find or create transaction
            transaction = await self._find_or_create_checkout_transaction(
                invoice_id, order_id, data
            )

            # Update transaction status
            await self._update_transaction_status(transaction, status, data)

            # If order has charges, process them
            charges = data.get("charges", [])
            if charges:
                for charge in charges:
                    charge_status = charge.get("status")
                    if charge_status == "PAID":
                        await self._mark_invoice_as_paid(invoice_id, charge)

            await self.db.commit()

            return {
                "success": True,
                "order_id": order_id,
                "status": status,
                "transaction_id": transaction.id
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Checkout notification failed: {str(e)}"
            }

    async def sync_subscription_status(self, subscription_id: str) -> Dict:
        """Manually sync subscription status with PagBank"""
        try:
            # Get current status from PagBank
            pagbank_status = await self.pagbank_service.get_subscription_status(subscription_id)

            # Find local billing schedule
            schedule = await self._find_billing_schedule_by_subscription(subscription_id)
            if not schedule:
                return {
                    "success": False,
                    "error": f"Billing schedule not found for subscription {subscription_id}"
                }

            # Update local status
            await self._update_schedule_from_subscription_status(
                schedule,
                pagbank_status.get("status"),
                pagbank_status
            )

            await self.db.commit()

            return {
                "success": True,
                "subscription_id": subscription_id,
                "local_schedule_id": schedule.id,
                "pagbank_status": pagbank_status.get("status")
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "error": f"Sync failed: {str(e)}"
            }

    # ==========================================
    # PRIVATE HELPER METHODS
    # ==========================================

    async def _find_billing_schedule_by_subscription(self, subscription_id: str) -> Optional[ContractBillingSchedule]:
        """Find billing schedule by PagBank subscription ID"""
        stmt = select(ContractBillingSchedule).where(
            ContractBillingSchedule.pagbank_subscription_id == subscription_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_pagbank_transaction(self, charge_id: str, reference_id: str) -> Optional[PagBankTransaction]:
        """Find PagBank transaction by charge ID or reference"""
        stmt = select(PagBankTransaction).where(
            (PagBankTransaction.pagbank_charge_id == charge_id) |
            (PagBankTransaction.pagbank_transaction_id == reference_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_schedule_from_subscription_status(
        self,
        schedule: ContractBillingSchedule,
        status: str,
        data: Dict
    ) -> None:
        """Update billing schedule based on subscription status"""
        # Map PagBank status to our internal status
        internal_status = self.pagbank_service.map_pagbank_status_to_internal(status, "recurrent")

        # Update next billing date if provided
        next_billing = data.get("next_invoice_at")
        if next_billing:
            try:
                next_billing_date = datetime.fromisoformat(next_billing.replace('Z', '+00:00')).date()
                schedule.next_billing_date = next_billing_date
            except:
                pass  # Keep existing date if parsing fails

        # Update last attempt if this is a failure
        if status in ["SUSPENDED", "CANCELLED", "PAYMENT_FAILED"]:
            schedule.last_attempt_date = datetime.now().date()
            schedule.attempt_count += 1

        await self.db.flush()

    async def _handle_subscription_failure(self, schedule: ContractBillingSchedule, data: Dict) -> None:
        """Handle subscription payment failure"""
        max_attempts = 3  # Configure this in settings

        if schedule.attempt_count >= max_attempts and schedule.auto_fallback_enabled:
            # Switch to manual billing
            schedule.billing_method = "manual"
            schedule.pagbank_subscription_id = None
            schedule.attempt_count = 0

            # TODO: Send notification to customer about fallback
            # await self._send_fallback_notification(schedule)

    async def _reset_billing_attempts(self, schedule: ContractBillingSchedule) -> None:
        """Reset billing attempt count after successful payment"""
        schedule.attempt_count = 0
        schedule.last_attempt_date = None
        await self.db.flush()

    async def _update_transaction_status(
        self,
        transaction: PagBankTransaction,
        status: str,
        data: Dict
    ) -> None:
        """Update PagBank transaction status"""
        internal_status = self.pagbank_service.map_pagbank_status_to_internal(
            status,
            transaction.transaction_type
        )

        # Update transaction attributes
        transaction.status = internal_status
        transaction.webhook_data = data
        transaction.updated_at = datetime.now()

        # Update charge ID if provided
        charge_id = data.get("id")
        if charge_id:
            transaction.pagbank_charge_id = str(charge_id)

        await self.db.flush()

    async def _mark_invoice_as_paid(self, invoice_id: int, payment_data: Dict) -> None:
        """Mark invoice as paid and update payment details"""
        stmt = update(ContractInvoice).where(
            ContractInvoice.id == invoice_id
        ).values(
            status="paga",
            paid_date=datetime.now().date(),
            payment_method="pagbank",
            payment_reference=payment_data.get("id"),
            payment_notes=f"Pagamento PagBank confirmado automaticamente",
            updated_at=datetime.now()
        )

        await self.db.execute(stmt)

    async def _extract_invoice_id_from_reference(self, reference_id: str) -> Optional[int]:
        """Extract invoice ID from PagBank reference"""
        if not reference_id:
            return None

        try:
            # Expected format: "INV_{invoice_id}_{timestamp}"
            if reference_id.startswith("INV_"):
                parts = reference_id.split("_")
                if len(parts) >= 2:
                    return int(parts[1])
        except (ValueError, IndexError):
            pass

        return None

    async def _find_or_create_checkout_transaction(
        self,
        invoice_id: int,
        order_id: str,
        data: Dict
    ) -> PagBankTransaction:
        """Find existing or create new checkout transaction"""
        # Try to find existing transaction
        stmt = select(PagBankTransaction).where(
            PagBankTransaction.invoice_id == invoice_id,
            PagBankTransaction.pagbank_transaction_id == order_id
        )
        result = await self.db.execute(stmt)
        transaction = result.scalar_one_or_none()

        if not transaction:
            # Create new transaction
            transaction = PagBankTransaction(
                invoice_id=invoice_id,
                transaction_type="checkout",
                pagbank_transaction_id=order_id,
                status="pending",
                amount=self.pagbank_service.format_amount_from_cents(
                    data.get("amount", {}).get("value", 0)
                ),
                webhook_data=data
            )
            self.db.add(transaction)
            await self.db.flush()

        return transaction

    async def _send_fallback_notification(self, schedule: ContractBillingSchedule) -> None:
        """Send notification about fallback to manual billing"""
        # TODO: Implement notification system
        # This could send email, SMS, or create in-app notification
        pass