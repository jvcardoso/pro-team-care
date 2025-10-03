from typing import Dict, List, Optional
import httpx
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal

from config.settings import settings


class PagBankService:
    """Service for PagBank payment integration (recurrent and checkout)"""

    def __init__(self):
        self.base_url_recurrent = "https://api.assinaturas.pagseguro.com"
        self.base_url_checkout = "https://api.pagseguro.com"
        self.token = settings.PAGBANK_TOKEN
        self.webhook_secret = settings.PAGBANK_WEBHOOK_SECRET
        self.environment = getattr(settings, 'PAGBANK_ENVIRONMENT', 'sandbox')

        # Use sandbox URLs if in sandbox mode
        if self.environment == 'sandbox':
            self.base_url_recurrent = "https://sandbox.api.assinaturas.pagseguro.com"
            self.base_url_checkout = "https://sandbox.api.pagseguro.com"

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to PagBank API"""
        default_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if headers:
            default_headers.update(headers)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers)
                elif method.upper() == "POST":
                    response = await client.post(
                        url,
                        json=data,
                        headers=default_headers
                    )
                elif method.upper() == "PUT":
                    response = await client.put(
                        url,
                        json=data,
                        headers=default_headers
                    )
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=default_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = "Unknown error"
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text

                raise Exception(f"PagBank API error {e.response.status_code}: {error_detail}")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

    # ==========================================
    # SAAS BILLING METHODS
    # ==========================================

    async def create_subscription(self, customer_data: Dict, plan_data: Dict) -> Dict:
        """Create SaaS subscription for company billing"""
        try:
            # First create customer
            customer_payload = {
                "reference": f"SAAS_CUSTOMER_{customer_data['document']}",
                "name": customer_data['name'],
                "email": customer_data['email'],
                "document": {
                    "type": "CPF" if len(customer_data['document']) == 11 else "CNPJ",
                    "value": customer_data['document']
                }
            }

            if customer_data.get('phone'):
                customer_payload["phone"] = {
                    "country": "55",
                    "area": customer_data['phone'][:2],
                    "number": customer_data['phone'][2:]
                }

            if customer_data.get('address'):
                customer_payload["address"] = customer_data['address']

            customer_response = await self._make_request(
                "POST",
                f"{self.base_url_recurrent}/customers",
                customer_payload
            )

            customer_id = customer_response.get("id")
            if not customer_id:
                raise Exception("Failed to create customer")

            # Create subscription plan
            plan_payload = {
                "reference": f"SAAS_PLAN_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": plan_data['name'],
                "description": f"Pro Team Care SaaS - {plan_data['name']}",
                "amount": {
                    "value": int(float(plan_data['amount']) * 100),  # Convert to cents
                    "currency": "BRL"
                },
                "interval": {
                    "unit": "MONTH",
                    "length": 1
                },
                "cycles": 0,  # Unlimited cycles
                "trial": {
                    "enabled": False
                }
            }

            plan_response = await self._make_request(
                "POST",
                f"{self.base_url_recurrent}/plans",
                plan_payload
            )

            plan_id = plan_response.get("id")
            if not plan_id:
                raise Exception("Failed to create plan")

            # Create subscription
            subscription_payload = {
                "reference": f"SAAS_SUB_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer_id": customer_id,
                "plan_id": plan_id,
                "payment_method": {
                    "type": "CREDIT_CARD"
                },
                "pro_rata": False,
                "auto_renewal": True
            }

            subscription_response = await self._make_request(
                "POST",
                f"{self.base_url_recurrent}/subscriptions",
                subscription_payload
            )

            return {
                "success": True,
                "customer_id": customer_id,
                "plan_id": plan_id,
                "subscription_id": subscription_response.get("id"),
                "subscription_code": subscription_response.get("code"),
                "status": subscription_response.get("status")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def charge_subscription(self, subscription_id: str, amount: Decimal, description: str) -> Dict:
        """Charge a SaaS subscription"""
        try:
            charge_payload = {
                "amount": {
                    "value": int(float(amount) * 100),  # Convert to cents
                    "currency": "BRL"
                },
                "description": description,
                "reference": f"SAAS_CHARGE_{subscription_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }

            response = await self._make_request(
                "POST",
                f"{self.base_url_recurrent}/subscriptions/{subscription_id}/charges",
                charge_payload
            )

            return {
                "success": True,
                "transaction_id": response.get("id"),
                "status": response.get("status"),
                "amount": amount
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel a SaaS subscription"""
        try:
            response = await self._make_request(
                "PUT",
                f"{self.base_url_recurrent}/subscriptions/{subscription_id}/cancel"
            )

            return {
                "success": True,
                "subscription_id": subscription_id,
                "status": response.get("status")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def create_checkout_session(self, checkout_data: Dict) -> Dict:
        """Create checkout session for SaaS invoice payment"""
        try:
            checkout_payload = {
                "reference_id": checkout_data["reference_id"],
                "customer": checkout_data["customer"],
                "items": [
                    {
                        "reference_id": checkout_data["reference_id"],
                        "name": checkout_data["description"],
                        "quantity": 1,
                        "unit_amount": int(float(checkout_data["amount"]) * 100)  # Convert to cents
                    }
                ],
                "payment_methods": [
                    {
                        "type": "CREDIT_CARD",
                        "brands": ["visa", "mastercard", "amex", "elo", "hipercard"]
                    },
                    {
                        "type": "DEBIT_CARD",
                        "brands": ["visa", "mastercard"]
                    },
                    {
                        "type": "PIX"
                    }
                ],
                "notification_urls": checkout_data.get("notification_urls", [])
            }

            if checkout_data.get("success_url"):
                checkout_payload["redirect_url"] = checkout_data["success_url"]

            response = await self._make_request(
                "POST",
                f"{self.base_url_checkout}/checkout-sessions",
                checkout_payload
            )

            return {
                "success": True,
                "session_id": response.get("id"),
                "checkout_url": response.get("links", [{}])[0].get("href"),
                "expires_at": response.get("expires_at")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==========================================
    # PAGAMENTOS RECORRENTES (ASSINATURAS) - LEGACY HOME CARE
    # ==========================================

    async def create_subscription_plan(self, contract_data: Dict) -> Dict:
        """Create subscription plan for recurrent billing"""
        plan_data = {
            "reference": f"PLAN_{contract_data['contract_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": f"Plano {contract_data['plan_name']}",
            "description": f"Plano mensal para contrato {contract_data['contract_number']}",
            "amount": {
                "value": int(float(contract_data['monthly_value']) * 100),  # Convert to cents
                "currency": "BRL"
            },
            "interval": {
                "unit": "MONTH",
                "length": 1
            },
            "cycles": 0,  # Unlimited cycles
            "trial": {
                "enabled": False
            }
        }

        url = f"{self.base_url_recurrent}/plans"
        response = await self._make_request("POST", url, plan_data)

        return {
            "plan_id": response.get("id"),
            "status": response.get("status"),
            "reference": response.get("reference"),
            "response": response
        }

    async def create_customer(self, client_data: Dict) -> Dict:
        """Create customer in PagBank for recurrent billing"""
        customer_data = {
            "reference": f"CUSTOMER_{client_data['client_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": client_data['name'],
            "email": client_data['email'],
            "tax_id": client_data['tax_id'],
            "phones": [
                {
                    "country": "55",
                    "area": client_data['phone_area'],
                    "number": client_data['phone_number'],
                    "type": "MOBILE"
                }
            ],
            "address": {
                "street": client_data['address']['street'],
                "number": client_data['address']['number'],
                "complement": client_data['address'].get('details', ''),
                "locality": client_data['address']['neighborhood'],
                "city": client_data['address']['city'],
                "region_code": client_data['address']['state'],
                "country": "BRA",
                "postal_code": client_data['address']['zip_code'].replace('-', '')
            }
        }

        url = f"{self.base_url_recurrent}/customers"
        response = await self._make_request("POST", url, customer_data)

        return {
            "customer_id": response.get("id"),
            "status": response.get("status"),
            "reference": response.get("reference"),
            "response": response
        }

    async def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        card_data: Dict
    ) -> Dict:
        """Create recurrent subscription with credit card"""
        subscription_data = {
            "reference": f"SUB_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "plan": {
                "id": plan_id
            },
            "customer": {
                "id": customer_id
            },
            "payment_method": {
                "type": "CREDIT_CARD",
                "card": {
                    "number": card_data['card_number'],
                    "exp_month": card_data['card_expiry_month'],
                    "exp_year": card_data['card_expiry_year'],
                    "security_code": card_data['card_cvv'],
                    "holder": {
                        "name": card_data['card_holder_name']
                    }
                }
            }
        }

        url = f"{self.base_url_recurrent}/subscriptions"
        response = await self._make_request("POST", url, subscription_data)

        return {
            "subscription_id": response.get("id"),
            "status": response.get("status"),
            "reference": response.get("reference"),
            "next_billing_date": response.get("next_invoice_at"),
            "response": response
        }

    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel recurrent subscription"""
        url = f"{self.base_url_recurrent}/subscriptions/{subscription_id}/cancel"
        response = await self._make_request("POST", url)

        return {
            "subscription_id": subscription_id,
            "status": response.get("status"),
            "cancelled_at": response.get("cancelled_at"),
            "response": response
        }

    async def get_subscription_status(self, subscription_id: str) -> Dict:
        """Get current subscription status"""
        url = f"{self.base_url_recurrent}/subscriptions/{subscription_id}"
        response = await self._make_request("GET", url)

        return {
            "subscription_id": subscription_id,
            "status": response.get("status"),
            "next_billing_date": response.get("next_invoice_at"),
            "response": response
        }

    # ==========================================
    # PAGAMENTOS AVULSOS (CHECKOUT)
    # ==========================================

    async def create_checkout_session(self, invoice_data: Dict) -> Dict:
        """Create checkout session for manual payment"""

        def _create_mock_response():
            """Create mock response for development/demo"""
            mock_session_id = f"mock_session_{invoice_data['invoice_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return {
                "session_id": mock_session_id,
                "checkout_url": f"https://mock-pagbank.proteamcare.com/checkout/{mock_session_id}",
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "qr_code": f"mock-qr-code-{mock_session_id}",
                "transaction_id": None,  # Will be set when payment is processed
                "response": {"status": "mock", "mode": "development"}
            }

        # Mock mode for development/demo when token is not configured
        if not self.token or self.token == "":
            return _create_mock_response()

        # Estrutura correta segundo documentação oficial PagBank
        checkout_data = {
            "reference_id": f"INV_{invoice_data['invoice_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer": {
                "name": invoice_data['customer_name'],
                "email": invoice_data['customer_email'],
                "tax_id": invoice_data['customer_tax_id'],
                "phones": [
                    {
                        "country": "55",
                        "area": invoice_data.get('customer_phone_area', '11'),
                        "number": invoice_data.get('customer_phone_number', '999999999'),
                        "type": "MOBILE"
                    }
                ]
            },
            "items": [
                {
                    "reference_id": f"ITEM_INV_{invoice_data['invoice_id']}",
                    "name": f"Fatura {invoice_data.get('invoice_number', invoice_data['invoice_id'])}",
                    "description": f"Pagamento de fatura Pro Team Care - {invoice_data.get('invoice_number', invoice_data['invoice_id'])}",
                    "quantity": 1,
                    "unit_amount": int(float(invoice_data['total_amount']) * 100)  # Convert to cents
                }
            ],
            "payment_methods": [
                {
                    "type": "CREDIT_CARD",
                    "brands": ["visa", "mastercard", "amex", "elo", "hipercard"]
                },
                {
                    "type": "DEBIT_CARD",
                    "brands": ["visa", "mastercard"]
                },
                {
                    "type": "PIX"
                },
                {
                    "type": "BOLETO"
                }
            ],
            "notification_urls": [
                f"{settings.BASE_URL}/api/v1/billing/webhooks/pagbank"
            ],
            "redirect_url": f"{settings.FRONTEND_URL}/billing/payment-result"
        }

        url = f"{self.base_url_checkout}/checkout-sessions"

        try:
            response = await self._make_request("POST", url, checkout_data)

            # Processar resposta da API PagBank checkout-sessions
            checkout_url = None
            qr_code = None

            # Extrair URL de checkout dos links retornados
            if response.get("links"):
                for link in response.get("links", []):
                    if link.get("rel") == "CHECKOUT":
                        checkout_url = link.get("href")
                        break

            # Extrair QR code se disponível (para PIX)
            if response.get("qr_codes"):
                qr_code = response.get("qr_codes", [{}])[0].get("text")

            return {
                "session_id": response.get("id"),
                "checkout_url": checkout_url,
                "expires_at": response.get("expires_at"),
                "qr_code": qr_code,
                "response": response
            }

        except Exception as e:
            # Fallback to mock mode if PagBank API fails (auth issues, etc.)
            print(f"PagBank API falhou, usando modo mock: {str(e)}")
            mock_response = _create_mock_response()
            mock_response["response"]["error"] = str(e)
            mock_response["response"]["fallback_reason"] = "pagbank_api_error"
            return mock_response

    async def get_transaction_status(self, transaction_id: str) -> Dict:
        """Get transaction status for checkout payment"""
        url = f"{self.base_url_checkout}/orders/{transaction_id}"
        response = await self._make_request("GET", url)

        charges = response.get("charges", [])
        if charges:
            charge = charges[0]
            return {
                "transaction_id": transaction_id,
                "charge_id": charge.get("id"),
                "status": charge.get("status"),
                "payment_method": charge.get("payment_method", {}).get("type"),
                "amount": charge.get("amount", {}).get("value", 0) / 100,  # Convert from cents
                "paid_at": charge.get("paid_at"),
                "response": response
            }
        else:
            return {
                "transaction_id": transaction_id,
                "status": response.get("status"),
                "response": response
            }

    # ==========================================
    # WEBHOOKS
    # ==========================================

    async def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature for security"""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured

        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    async def process_webhook_notification(self, payload: Dict) -> Dict:
        """Process webhook notification from PagBank"""
        notification_type = payload.get("type")
        data = payload.get("data", {})

        if notification_type == "SUBSCRIPTION":
            return await self._process_subscription_webhook(data)
        elif notification_type == "PAYMENT":
            return await self._process_payment_webhook(data)
        elif notification_type == "ORDER":
            return await self._process_order_webhook(data)
        else:
            return {
                "processed": False,
                "error": f"Unknown notification type: {notification_type}"
            }

    async def _process_subscription_webhook(self, data: Dict) -> Dict:
        """Process subscription webhook notification"""
        subscription_id = data.get("id")
        status = data.get("status")

        return {
            "processed": True,
            "type": "subscription",
            "subscription_id": subscription_id,
            "status": status,
            "data": data
        }

    async def _process_payment_webhook(self, data: Dict) -> Dict:
        """Process payment webhook notification"""
        charge_id = data.get("id")
        status = data.get("status")
        reference_id = data.get("reference_id")

        return {
            "processed": True,
            "type": "payment",
            "charge_id": charge_id,
            "status": status,
            "reference_id": reference_id,
            "data": data
        }

    async def _process_order_webhook(self, data: Dict) -> Dict:
        """Process order webhook notification"""
        order_id = data.get("id")
        status = data.get("status")
        reference_id = data.get("reference_id")

        return {
            "processed": True,
            "type": "order",
            "order_id": order_id,
            "status": status,
            "reference_id": reference_id,
            "data": data
        }

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    async def list_customer_subscriptions(self, customer_id: str) -> List[Dict]:
        """List all subscriptions for a customer"""
        url = f"{self.base_url_recurrent}/customers/{customer_id}/subscriptions"
        response = await self._make_request("GET", url)

        return response.get("subscriptions", [])

    async def get_plan_details(self, plan_id: str) -> Dict:
        """Get plan details"""
        url = f"{self.base_url_recurrent}/plans/{plan_id}"
        response = await self._make_request("GET", url)

        return response

    def format_amount_to_cents(self, amount: Decimal) -> int:
        """Convert decimal amount to cents for PagBank API"""
        return int(float(amount) * 100)

    def format_amount_from_cents(self, cents: int) -> Decimal:
        """Convert cents from PagBank API to decimal amount"""
        return Decimal(cents) / 100

    def map_pagbank_status_to_internal(self, pagbank_status: str, transaction_type: str) -> str:
        """Map PagBank status to internal status"""
        status_mapping = {
            # Subscription statuses
            "ACTIVE": "approved",
            "SUSPENDED": "declined",
            "CANCELLED": "cancelled",
            "EXPIRED": "failed",
            # Payment statuses
            "PAID": "approved",
            "DECLINED": "declined",
            "CANCELLED": "cancelled",
            "PENDING": "pending",
            "FAILED": "failed"
        }

        return status_mapping.get(pagbank_status.upper(), "pending")