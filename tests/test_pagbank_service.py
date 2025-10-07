# Temporarily patch the import for testing
import sys
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, "/home/juliano/Projetos/pro_team_care_16")
from unittest.mock import MagicMock, patch

# Mock the settings import
mock_settings = MagicMock()
mock_settings.PAGBANK_TOKEN = "test_token"
mock_settings.PAGBANK_WEBHOOK_SECRET = "test_secret"
mock_settings.PAGBANK_ENVIRONMENT = "sandbox"
mock_settings.BASE_URL = "http://localhost:8000"
mock_settings.FRONTEND_URL = "http://localhost:3000"

with patch.dict(
    "sys.modules", {"app.config.settings": MagicMock(settings=mock_settings)}
):
    from app.infrastructure.services.pagbank_service import PagBankService


class TestPagBankService:
    """Test cases for PagBankService"""

    @pytest.fixture
    def pagbank_service(self):
        """Fixture for PagBankService instance"""
        return PagBankService()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        mock_settings = MagicMock()
        mock_settings.PAGBANK_TOKEN = "test_token"
        mock_settings.PAGBANK_WEBHOOK_SECRET = "test_secret"
        mock_settings.PAGBANK_ENVIRONMENT = "sandbox"
        mock_settings.BASE_URL = "http://localhost:8000"
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        with patch(
            "app.infrastructure.services.pagbank_service.settings", mock_settings
        ):
            yield

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_subscription_plan_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful subscription plan creation"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "PLAN_123",
            "status": "ACTIVE",
            "reference": "PLAN_1_20250122120000",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        contract_data = {
            "contract_id": 1,
            "plan_name": "Plano Básico",
            "contract_number": "CTR001",
            "monthly_value": "100.00",
        }

        result = await pagbank_service.create_subscription_plan(contract_data)

        assert result["plan_id"] == "PLAN_123"
        assert result["status"] == "ACTIVE"
        assert "PLAN_1_" in result["reference"]

        # Verify the request was made correctly
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        assert call_args[0][0].endswith("/plans")
        request_data = call_args[1]["json"]
        assert request_data["amount"]["value"] == 10000  # 100.00 * 100

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_subscription_plan_api_error(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test subscription plan creation with API error"""
        from httpx import HTTPStatusError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid data"}

        mock_client.return_value.__aenter__.return_value.post.side_effect = (
            HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
        )

        contract_data = {
            "contract_id": 1,
            "plan_name": "Plano Básico",
            "contract_number": "CTR001",
            "monthly_value": "100.00",
        }

        with pytest.raises(Exception) as exc_info:
            await pagbank_service.create_subscription_plan(contract_data)

        assert "PagBank API error 400" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_customer_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful customer creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "CUST_123",
            "status": "ACTIVE",
            "reference": "CUSTOMER_1_20250122120000",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        client_data = {
            "client_id": 1,
            "name": "João Silva",
            "email": "joao@example.com",
            "tax_id": "12345678900",
            "phone_area": "11",
            "phone_number": "999999999",
            "address": {
                "street": "Rua A",
                "number": "123",
                "details": "Apt 1",
                "neighborhood": "Centro",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01234-567",
            },
        }

        result = await pagbank_service.create_customer(client_data)

        assert result["customer_id"] == "CUST_123"
        assert result["status"] == "ACTIVE"

        # Verify request data structure
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["name"] == "João Silva"
        assert request_data["email"] == "joao@example.com"
        assert request_data["address"]["postal_code"] == "01234567"  # Formatted

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_subscription_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful subscription creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "SUB_123",
            "status": "ACTIVE",
            "reference": "SUB_20250122120000",
            "next_invoice_at": "2025-02-22T00:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        card_data = {
            "card_number": "4111111111111111",
            "card_expiry_month": 12,
            "card_expiry_year": 2025,
            "card_cvv": "123",
            "card_holder_name": "João Silva",
        }

        result = await pagbank_service.create_subscription(
            "PLAN_123", "CUST_123", card_data
        )

        assert result["subscription_id"] == "SUB_123"
        assert result["status"] == "ACTIVE"

        # Verify card data in request
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["plan"]["id"] == "PLAN_123"
        assert request_data["customer"]["id"] == "CUST_123"
        assert request_data["payment_method"]["card"]["number"] == "4111111111111111"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_cancel_subscription_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful subscription cancellation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "CANCELLED",
            "cancelled_at": "2025-01-22T12:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        result = await pagbank_service.cancel_subscription("SUB_123")

        assert result["subscription_id"] == "SUB_123"
        assert result["status"] == "CANCELLED"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_create_checkout_session_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful checkout session creation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "CHECKOUT_123",
            "links": [{"href": "https://checkout.pagseguro.com/123"}],
            "expiration_date": "2025-01-29T12:00:00Z",
            "qr_codes": [{"text": "QR_CODE_DATA"}],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        invoice_data = {
            "invoice_id": 1,
            "invoice_number": "INV001",
            "contract_number": "CTR001",
            "total_amount": "150.00",
            "customer_name": "João Silva",
            "customer_email": "joao@example.com",
            "customer_tax_id": "12345678900",
            "customer_phone_area": "11",
            "customer_phone_number": "999999999",
        }

        result = await pagbank_service.create_checkout_session(invoice_data)

        assert result["session_id"] == "CHECKOUT_123"
        assert result["checkout_url"] == "https://checkout.pagseguro.com/123"
        assert result["qr_code"] == "QR_CODE_DATA"

        # Verify amount conversion
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        request_data = call_args[1]["json"]
        assert request_data["amount"]["value"] == 15000  # 150.00 * 100

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_transaction_status_success(
        self, mock_client, pagbank_service, mock_settings
    ):
        """Test successful transaction status retrieval"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "charges": [
                {
                    "id": "CHARGE_123",
                    "status": "PAID",
                    "amount": {"value": 15000},
                    "payment_method": {"type": "PIX"},
                    "paid_at": "2025-01-22T12:00:00Z",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await pagbank_service.get_transaction_status("ORDER_123")

        assert result["transaction_id"] == "ORDER_123"
        assert result["charge_id"] == "CHARGE_123"
        assert result["status"] == "PAID"
        assert result["payment_method"] == "PIX"
        assert result["amount"] == 150.0  # Converted from cents

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, pagbank_service, mock_settings):
        """Test webhook signature verification with valid signature"""
        payload = '{"test": "data"}'
        secret = "test_secret"
        expected_signature = "sha256=" + "some_hash"  # Would be calculated properly

        with patch.object(pagbank_service, "webhook_secret", secret):
            # Mock hmac for testing
            with patch("hmac.new") as mock_hmac:
                mock_hash = MagicMock()
                mock_hash.hexdigest.return_value = "some_hash"
                mock_hmac.return_value = mock_hash

                result = await pagbank_service.verify_webhook_signature(
                    payload, "sha256=some_hash"
                )

                assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(
        self, pagbank_service, mock_settings
    ):
        """Test webhook signature verification with invalid signature"""
        payload = '{"test": "data"}'

        with patch.object(pagbank_service, "webhook_secret", "test_secret"):
            with patch("hmac.new") as mock_hmac:
                mock_hash = MagicMock()
                mock_hash.hexdigest.return_value = "wrong_hash"
                mock_hmac.return_value = mock_hash

                result = await pagbank_service.verify_webhook_signature(
                    payload, "sha256=different_hash"
                )

                assert result is False

    @pytest.mark.asyncio
    async def test_process_webhook_subscription(self, pagbank_service, mock_settings):
        """Test processing subscription webhook"""
        payload = {
            "type": "SUBSCRIPTION",
            "data": {"id": "SUB_123", "status": "ACTIVE"},
        }

        result = await pagbank_service.process_webhook_notification(payload)

        assert result["processed"] is True
        assert result["type"] == "subscription"
        assert result["subscription_id"] == "SUB_123"

    @pytest.mark.asyncio
    async def test_process_webhook_payment(self, pagbank_service, mock_settings):
        """Test processing payment webhook"""
        payload = {
            "type": "PAYMENT",
            "data": {"id": "CHARGE_123", "status": "PAID", "reference_id": "REF_123"},
        }

        result = await pagbank_service.process_webhook_notification(payload)

        assert result["processed"] is True
        assert result["type"] == "payment"
        assert result["charge_id"] == "CHARGE_123"

    @pytest.mark.asyncio
    async def test_process_webhook_unknown_type(self, pagbank_service, mock_settings):
        """Test processing webhook with unknown type"""
        payload = {"type": "UNKNOWN", "data": {}}

        result = await pagbank_service.process_webhook_notification(payload)

        assert result["processed"] is False
        assert "Unknown notification type" in result["error"]

    def test_format_amount_to_cents(self, pagbank_service):
        """Test amount formatting to cents"""
        assert pagbank_service.format_amount_to_cents(Decimal("100.50")) == 10050
        assert pagbank_service.format_amount_to_cents(Decimal("0.01")) == 1

    def test_format_amount_from_cents(self, pagbank_service):
        """Test amount formatting from cents"""
        assert pagbank_service.format_amount_from_cents(10050) == Decimal("100.50")
        assert pagbank_service.format_amount_from_cents(1) == Decimal("0.01")

    def test_map_pagbank_status_to_internal(self, pagbank_service):
        """Test status mapping from PagBank to internal"""
        # Subscription statuses
        assert (
            pagbank_service.map_pagbank_status_to_internal("ACTIVE", "recurrent")
            == "approved"
        )
        assert (
            pagbank_service.map_pagbank_status_to_internal("SUSPENDED", "recurrent")
            == "declined"
        )
        assert (
            pagbank_service.map_pagbank_status_to_internal("CANCELLED", "recurrent")
            == "cancelled"
        )

        # Payment statuses
        assert (
            pagbank_service.map_pagbank_status_to_internal("PAID", "checkout")
            == "approved"
        )
        assert (
            pagbank_service.map_pagbank_status_to_internal("DECLINED", "checkout")
            == "declined"
        )
        assert (
            pagbank_service.map_pagbank_status_to_internal("PENDING", "checkout")
            == "pending"
        )

        # Unknown status defaults to pending
        assert (
            pagbank_service.map_pagbank_status_to_internal("UNKNOWN", "checkout")
            == "pending"
        )
