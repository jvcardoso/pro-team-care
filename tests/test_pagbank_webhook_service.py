from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.orm.models import (
    ContractBillingSchedule,
    ContractInvoice,
    PagBankTransaction,
)
from app.infrastructure.services.pagbank_webhook_service import PagBankWebhookService


class TestPagBankWebhookService:
    """Test cases for PagBankWebhookService"""

    @pytest.fixture
    def mock_db(self):
        """Mock AsyncSession"""
        return AsyncMock()

    @pytest.fixture
    def webhook_service(self, mock_db):
        """Fixture for PagBankWebhookService instance"""
        return PagBankWebhookService(mock_db)

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    async def test_handle_webhook_invalid_signature(
        self, mock_pagbank_class, webhook_service
    ):
        """Test webhook handling with invalid signature"""
        mock_pagbank = MagicMock()
        mock_pagbank.verify_webhook_signature = AsyncMock(return_value=False)
        mock_pagbank_class.return_value = mock_pagbank

        payload = {"type": "SUBSCRIPTION", "data": {}}
        signature = "invalid_signature"

        result = await webhook_service.handle_webhook_notification(payload, signature)

        assert result["success"] is False
        assert "Invalid webhook signature" in result["error"]

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    async def test_handle_webhook_unknown_type(
        self, mock_pagbank_class, webhook_service
    ):
        """Test webhook handling with unknown notification type"""
        mock_pagbank = MagicMock()
        mock_pagbank.verify_webhook_signature = AsyncMock(return_value=True)
        mock_pagbank_class.return_value = mock_pagbank

        payload = {"type": "UNKNOWN", "data": {}}
        signature = "valid_signature"

        result = await webhook_service.handle_webhook_notification(payload, signature)

        assert result["success"] is False
        assert "Unknown notification type" in result["error"]

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    @patch.object(PagBankWebhookService, "handle_subscription_notification")
    async def test_handle_webhook_subscription(
        self, mock_handle_subscription, mock_pagbank_class, webhook_service
    ):
        """Test webhook handling for subscription notifications"""
        mock_pagbank = MagicMock()
        mock_pagbank.verify_webhook_signature = AsyncMock(return_value=True)
        mock_pagbank_class.return_value = mock_pagbank

        mock_handle_subscription.return_value = {
            "success": True,
            "subscription_id": "SUB_123",
        }

        payload = {"type": "SUBSCRIPTION", "data": {"id": "SUB_123"}}
        signature = "valid_signature"

        result = await webhook_service.handle_webhook_notification(payload, signature)

        mock_handle_subscription.assert_called_once_with(payload)
        assert result["success"] is True
        assert result["subscription_id"] == "SUB_123"

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    @patch.object(PagBankWebhookService, "handle_payment_notification")
    async def test_handle_webhook_payment(
        self, mock_handle_payment, mock_pagbank_class, webhook_service
    ):
        """Test webhook handling for payment notifications"""
        mock_pagbank = MagicMock()
        mock_pagbank.verify_webhook_signature = AsyncMock(return_value=True)
        mock_pagbank_class.return_value = mock_pagbank

        mock_handle_payment.return_value = {"success": True, "charge_id": "CHARGE_123"}

        payload = {"type": "PAYMENT", "data": {"id": "CHARGE_123"}}
        signature = "valid_signature"

        result = await webhook_service.handle_webhook_notification(payload, signature)

        mock_handle_payment.assert_called_once_with(payload)
        assert result["success"] is True
        assert result["charge_id"] == "CHARGE_123"

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    @patch.object(PagBankWebhookService, "handle_checkout_notification")
    async def test_handle_webhook_checkout(
        self, mock_handle_checkout, mock_pagbank_class, webhook_service
    ):
        """Test webhook handling for checkout notifications"""
        mock_pagbank = MagicMock()
        mock_pagbank.verify_webhook_signature = AsyncMock(return_value=True)
        mock_pagbank_class.return_value = mock_pagbank

        mock_handle_checkout.return_value = {"success": True, "order_id": "ORDER_123"}

        payload = {"type": "ORDER", "data": {"id": "ORDER_123"}}
        signature = "valid_signature"

        result = await webhook_service.handle_webhook_notification(payload, signature)

        mock_handle_checkout.assert_called_once_with(payload)
        assert result["success"] is True
        assert result["order_id"] == "ORDER_123"

    async def test_handle_subscription_notification_missing_subscription_id(
        self, webhook_service
    ):
        """Test subscription notification with missing subscription ID"""
        payload = {"data": {}}

        result = await webhook_service.handle_subscription_notification(payload)

        assert result["success"] is False
        assert "Missing subscription_id" in result["error"]

    @patch.object(PagBankWebhookService, "_find_billing_schedule_by_subscription")
    async def test_handle_subscription_notification_schedule_not_found(
        self, mock_find_schedule, webhook_service
    ):
        """Test subscription notification when billing schedule is not found"""
        mock_find_schedule.return_value = None

        payload = {"data": {"id": "SUB_123", "status": "ACTIVE"}}

        result = await webhook_service.handle_subscription_notification(payload)

        assert result["success"] is False
        assert "Billing schedule not found" in result["error"]

    @patch.object(PagBankWebhookService, "_find_billing_schedule_by_subscription")
    @patch.object(PagBankWebhookService, "_update_schedule_from_subscription_status")
    @patch.object(PagBankWebhookService, "_reset_billing_attempts")
    async def test_handle_subscription_notification_success_active(
        self,
        mock_reset_attempts,
        mock_update_schedule,
        mock_find_schedule,
        webhook_service,
    ):
        """Test successful subscription notification for active status"""
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_find_schedule.return_value = mock_schedule

        payload = {"data": {"id": "SUB_123", "status": "ACTIVE"}}

        result = await webhook_service.handle_subscription_notification(payload)

        assert result["success"] is True
        assert result["subscription_id"] == "SUB_123"
        assert result["status"] == "ACTIVE"
        mock_update_schedule.assert_called_once()
        mock_reset_attempts.assert_called_once_with(mock_schedule)

    @patch.object(PagBankWebhookService, "_find_billing_schedule_by_subscription")
    @patch.object(PagBankWebhookService, "_update_schedule_from_subscription_status")
    @patch.object(PagBankWebhookService, "_handle_subscription_failure")
    async def test_handle_subscription_notification_failure_handling(
        self,
        mock_handle_failure,
        mock_update_schedule,
        mock_find_schedule,
        webhook_service,
    ):
        """Test subscription notification with failure status"""
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_find_schedule.return_value = mock_schedule

        payload = {"data": {"id": "SUB_123", "status": "SUSPENDED"}}

        result = await webhook_service.handle_subscription_notification(payload)

        assert result["success"] is True
        mock_handle_failure.assert_called_once_with(mock_schedule, payload["data"])

    async def test_handle_payment_notification_missing_charge_id(self, webhook_service):
        """Test payment notification with missing charge ID"""
        payload = {"data": {}}

        result = await webhook_service.handle_payment_notification(payload)

        assert result["success"] is False
        assert "Missing charge_id" in result["error"]

    @patch.object(PagBankWebhookService, "_find_pagbank_transaction")
    async def test_handle_payment_notification_transaction_not_found(
        self, mock_find_transaction, webhook_service
    ):
        """Test payment notification when transaction is not found"""
        mock_find_transaction.return_value = None

        payload = {"data": {"id": "CHARGE_123", "status": "PAID"}}

        result = await webhook_service.handle_payment_notification(payload)

        assert result["success"] is False
        assert "Transaction not found" in result["error"]

    @patch.object(PagBankWebhookService, "_find_pagbank_transaction")
    @patch.object(PagBankWebhookService, "_update_transaction_status")
    @patch.object(PagBankWebhookService, "_mark_invoice_as_paid")
    async def test_handle_payment_notification_success_paid(
        self, mock_mark_paid, mock_update_status, mock_find_transaction, webhook_service
    ):
        """Test successful payment notification for paid status"""
        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_transaction.invoice_id = 100
        mock_find_transaction.return_value = mock_transaction

        payload = {"data": {"id": "CHARGE_123", "status": "PAID"}}

        result = await webhook_service.handle_payment_notification(payload)

        assert result["success"] is True
        assert result["charge_id"] == "CHARGE_123"
        assert result["status"] == "PAID"
        mock_update_status.assert_called_once()
        mock_mark_paid.assert_called_once_with(100, payload["data"])

    async def test_handle_checkout_notification_missing_order_id(self, webhook_service):
        """Test checkout notification with missing order ID"""
        payload = {"data": {}}

        result = await webhook_service.handle_checkout_notification(payload)

        assert result["success"] is False
        assert "Missing order_id" in result["error"]

    @patch.object(PagBankWebhookService, "_extract_invoice_id_from_reference")
    async def test_handle_checkout_notification_invalid_reference(
        self, mock_extract_invoice, webhook_service
    ):
        """Test checkout notification with invalid reference"""
        mock_extract_invoice.return_value = None

        payload = {"data": {"id": "ORDER_123", "reference_id": "INVALID_REF"}}

        result = await webhook_service.handle_checkout_notification(payload)

        assert result["success"] is False
        assert "Could not extract invoice_id" in result["error"]

    @patch.object(PagBankWebhookService, "_extract_invoice_id_from_reference")
    @patch.object(PagBankWebhookService, "_find_or_create_checkout_transaction")
    @patch.object(PagBankWebhookService, "_update_transaction_status")
    @patch.object(PagBankWebhookService, "_mark_invoice_as_paid")
    async def test_handle_checkout_notification_success_with_paid_charge(
        self,
        mock_mark_paid,
        mock_update_status,
        mock_find_or_create,
        mock_extract_invoice,
        webhook_service,
    ):
        """Test successful checkout notification with paid charge"""
        mock_extract_invoice.return_value = 100
        mock_transaction = MagicMock()
        mock_transaction.id = 1
        mock_find_or_create.return_value = mock_transaction

        payload = {
            "data": {
                "id": "ORDER_123",
                "reference_id": "INV_100_123456",
                "status": "PAID",
                "charges": [{"status": "PAID", "id": "CHARGE_123"}],
            }
        }

        result = await webhook_service.handle_checkout_notification(payload)

        assert result["success"] is True
        assert result["order_id"] == "ORDER_123"
        mock_mark_paid.assert_called_once_with(
            100, {"status": "PAID", "id": "CHARGE_123"}
        )

    async def test_extract_invoice_id_from_reference_valid(self, webhook_service):
        """Test extracting invoice ID from valid reference"""
        reference = "INV_123_1234567890"
        result = await webhook_service._extract_invoice_id_from_reference(reference)
        assert result == 123

    async def test_extract_invoice_id_from_reference_invalid(self, webhook_service):
        """Test extracting invoice ID from invalid reference"""
        invalid_references = ["", "INVALID", "INV_", "INV_abc_123", "OTHER_123_456"]
        for ref in invalid_references:
            result = await webhook_service._extract_invoice_id_from_reference(ref)
            assert result is None

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    async def test_sync_subscription_status_success(
        self, mock_pagbank_class, webhook_service
    ):
        """Test successful subscription status sync"""
        mock_pagbank = MagicMock()
        mock_pagbank.get_subscription_status = AsyncMock(
            return_value={"status": "ACTIVE", "next_invoice_at": "2025-02-01T00:00:00Z"}
        )
        mock_pagbank_class.return_value = mock_pagbank

        mock_schedule = MagicMock()
        mock_schedule.id = 1

        with patch.object(
            webhook_service,
            "_find_billing_schedule_by_subscription",
            return_value=mock_schedule,
        ), patch.object(
            webhook_service, "_update_schedule_from_subscription_status"
        ) as mock_update:

            result = await webhook_service.sync_subscription_status("SUB_123")

            assert result["success"] is True
            assert result["subscription_id"] == "SUB_123"
            assert result["pagbank_status"] == "ACTIVE"
            mock_update.assert_called_once()

    @patch("app.infrastructure.services.pagbank_webhook_service.PagBankService")
    async def test_sync_subscription_status_schedule_not_found(
        self, mock_pagbank_class, webhook_service
    ):
        """Test subscription sync when schedule is not found"""
        mock_pagbank = MagicMock()
        mock_pagbank_class.return_value = mock_pagbank

        with patch.object(
            webhook_service, "_find_billing_schedule_by_subscription", return_value=None
        ):
            result = await webhook_service.sync_subscription_status("SUB_123")

            assert result["success"] is False
            assert "Billing schedule not found" in result["error"]
