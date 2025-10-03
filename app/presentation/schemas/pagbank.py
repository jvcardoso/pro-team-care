from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator


# ==========================================
# BASE SCHEMAS
# ==========================================

class PagBankBaseResponse(BaseModel):
    """Base response schema for PagBank operations"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


# ==========================================
# BILLING METHOD SCHEMAS
# ==========================================

class BillingMethodUpdate(BaseModel):
    """Schema for updating billing method"""
    billing_method: str = Field(..., description="Billing method: 'recurrent' or 'manual'")
    auto_fallback_enabled: bool = Field(default=True, description="Enable automatic fallback")

    @validator("billing_method")
    def validate_billing_method(cls, v):
        if v not in ["recurrent", "manual"]:
            raise ValueError("billing_method must be 'recurrent' or 'manual'")
        return v


class BillingMethodStatus(BaseModel):
    """Schema for billing method status response"""
    contract_id: int
    billing_method: str
    is_active: bool
    next_billing_date: Optional[str] = None
    auto_fallback_enabled: bool
    attempt_count: int
    last_attempt_date: Optional[str] = None
    pagbank_data: Optional[Dict[str, Any]] = None


# ==========================================
# RECURRENT BILLING SCHEMAS
# ==========================================

class CardData(BaseModel):
    """Schema for credit card data"""
    card_number: str = Field(..., description="Credit card number")
    card_expiry_month: str = Field(..., description="Card expiry month (MM)")
    card_expiry_year: str = Field(..., description="Card expiry year (YYYY)")
    card_cvv: str = Field(..., description="Card CVV")
    card_holder_name: str = Field(..., description="Card holder name")

    @validator("card_expiry_month")
    def validate_month(cls, v):
        if not v.isdigit() or not (1 <= int(v) <= 12):
            raise ValueError("Invalid expiry month")
        return v.zfill(2)

    @validator("card_expiry_year")
    def validate_year(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise ValueError("Invalid expiry year")
        return v

    @validator("card_cvv")
    def validate_cvv(cls, v):
        if not v.isdigit() or not (3 <= len(v) <= 4):
            raise ValueError("Invalid CVV")
        return v


class AddressData(BaseModel):
    """Schema for address data"""
    street: str = Field(..., description="Street name")
    number: str = Field(..., description="Street number")
    details: Optional[str] = Field(None, description="Additional address details")
    neighborhood: str = Field(..., description="Neighborhood")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State code (e.g., SP)")
    zip_code: str = Field(..., description="ZIP code")

    @validator("zip_code")
    def validate_zip_code(cls, v):
        # Remove any formatting
        zip_clean = v.replace("-", "").replace(".", "")
        if not zip_clean.isdigit() or len(zip_clean) != 8:
            raise ValueError("Invalid ZIP code format")
        return zip_clean


class ClientDataForRecurrent(BaseModel):
    """Schema for client data required for recurrent billing setup"""
    client_id: int
    name: str = Field(..., description="Client full name")
    email: str = Field(..., description="Client email")
    tax_id: str = Field(..., description="Client tax ID (CPF/CNPJ)")
    phone_area: str = Field(..., description="Phone area code")
    phone_number: str = Field(..., description="Phone number")
    address: AddressData
    card_data: CardData

    @validator("tax_id")
    def validate_tax_id(cls, v):
        # Remove formatting
        tax_clean = v.replace(".", "").replace("-", "").replace("/", "")
        if not tax_clean.isdigit():
            raise ValueError("Tax ID must contain only numbers")
        if len(tax_clean) not in [11, 14]:
            raise ValueError("Tax ID must be CPF (11 digits) or CNPJ (14 digits)")
        return tax_clean

    @validator("phone_area")
    def validate_phone_area(cls, v):
        if not v.isdigit() or len(v) != 2:
            raise ValueError("Phone area must be 2 digits")
        return v

    @validator("phone_number")
    def validate_phone_number(cls, v):
        phone_clean = v.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if not phone_clean.isdigit() or len(phone_clean) < 8:
            raise ValueError("Invalid phone number")
        return phone_clean


class RecurrentBillingSetupRequest(BaseModel):
    """Schema for setting up recurrent billing"""
    contract_id: int
    client_data: ClientDataForRecurrent


class RecurrentBillingSetupResponse(PagBankBaseResponse):
    """Schema for recurrent billing setup response"""
    contract_id: Optional[int] = None
    billing_method: Optional[str] = None
    pagbank_subscription_id: Optional[str] = None
    pagbank_customer_id: Optional[str] = None
    next_billing_date: Optional[str] = None
    setup_details: Optional[Dict[str, Any]] = None


# ==========================================
# CHECKOUT SCHEMAS
# ==========================================

class CheckoutSessionRequest(BaseModel):
    """Schema for creating checkout session"""
    invoice_id: int


class CheckoutSessionResponse(PagBankBaseResponse):
    """Schema for checkout session response"""
    invoice_id: Optional[int] = None
    checkout_url: Optional[str] = None
    session_id: Optional[str] = None
    expires_at: Optional[str] = None
    qr_code: Optional[str] = None
    transaction_id: Optional[int] = None


# ==========================================
# TRANSACTION SCHEMAS
# ==========================================

class PagBankTransactionSchema(BaseModel):
    """Schema for PagBank transaction"""
    id: int
    invoice_id: int
    transaction_type: str
    pagbank_transaction_id: Optional[str] = None
    pagbank_charge_id: Optional[str] = None
    status: str
    amount: Decimal
    payment_method: Optional[str] = None
    error_message: Optional[str] = None
    webhook_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionsListResponse(BaseModel):
    """Schema for transactions list response"""
    transactions: List[PagBankTransactionSchema]
    total: int
    page: int
    size: int
    pages: int


# ==========================================
# WEBHOOK SCHEMAS
# ==========================================

class WebhookRequest(BaseModel):
    """Schema for incoming webhook requests"""
    type: str = Field(..., description="Notification type")
    data: Dict[str, Any] = Field(..., description="Webhook data")


class WebhookResponse(PagBankBaseResponse):
    """Schema for webhook processing response"""
    notification_type: Optional[str] = None
    processed_data: Optional[Dict[str, Any]] = None


# ==========================================
# SUBSCRIPTION MANAGEMENT SCHEMAS
# ==========================================

class SubscriptionCancelRequest(BaseModel):
    """Schema for cancelling subscription"""
    contract_id: int
    reason: Optional[str] = Field(None, description="Cancellation reason")


class SubscriptionCancelResponse(PagBankBaseResponse):
    """Schema for subscription cancellation response"""
    contract_id: Optional[int] = None
    cancelled_subscription_id: Optional[str] = None
    new_billing_method: Optional[str] = None
    cancellation_details: Optional[Dict[str, Any]] = None


class SubscriptionSyncRequest(BaseModel):
    """Schema for syncing subscription status"""
    subscription_id: str


class SubscriptionSyncResponse(PagBankBaseResponse):
    """Schema for subscription sync response"""
    subscription_id: Optional[str] = None
    local_schedule_id: Optional[int] = None
    pagbank_status: Optional[str] = None
    sync_data: Optional[Dict[str, Any]] = None


# ==========================================
# BILLING AUTOMATION SCHEMAS
# ==========================================

class AutomaticBillingRequest(BaseModel):
    """Schema for triggering automatic billing"""
    billing_date: Optional[str] = Field(None, description="Billing date (YYYY-MM-DD)")
    force_regenerate: bool = Field(default=False, description="Force regenerate existing invoices")
    contract_ids: Optional[List[int]] = Field(None, description="Specific contract IDs to process")

    @validator("billing_date")
    def validate_billing_date(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("billing_date must be in YYYY-MM-DD format")
        return v


class AutomaticBillingResponse(PagBankBaseResponse):
    """Schema for automatic billing response"""
    total_processed: Optional[int] = None
    successful: Optional[int] = None
    failed: Optional[int] = None
    errors: Optional[List[str]] = None
    results: Optional[List[Dict[str, Any]]] = None
    executed_at: Optional[str] = None


# ==========================================
# FAILURE HANDLING SCHEMAS
# ==========================================

class BillingFailureRequest(BaseModel):
    """Schema for processing billing failure"""
    schedule_id: int
    error_details: Dict[str, Any]


class BillingFailureResponse(PagBankBaseResponse):
    """Schema for billing failure processing response"""
    schedule_id: Optional[int] = None
    contract_id: Optional[int] = None
    attempt_count: Optional[int] = None
    max_attempts: Optional[int] = None
    fallback_triggered: Optional[bool] = None
    new_billing_method: Optional[str] = None


# ==========================================
# ANALYTICS SCHEMAS
# ==========================================

class BillingMethodStats(BaseModel):
    """Schema for billing method statistics"""
    total_contracts: int
    recurrent_count: int
    manual_count: int
    recurrent_percentage: float
    manual_percentage: float
    failed_recurrent_count: int
    fallback_triggered_count: int


class PagBankDashboardResponse(BaseModel):
    """Schema for PagBank dashboard data"""
    billing_method_stats: BillingMethodStats
    recent_transactions: List[PagBankTransactionSchema]
    pending_checkouts: int
    failed_recurrent_billings: int
    total_revenue_recurrent: Decimal
    total_revenue_manual: Decimal


# ==========================================
# ERROR SCHEMAS
# ==========================================

class PagBankError(BaseModel):
    """Schema for PagBank API errors"""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationErrorResponse(BaseModel):
    """Schema for validation errors"""
    field: str
    message: str
    value: Optional[Any] = None


class ErrorResponse(PagBankBaseResponse):
    """Schema for error responses"""
    error_code: Optional[str] = None
    validation_errors: Optional[List[ValidationErrorResponse]] = None
    details: Optional[Dict[str, Any]] = None