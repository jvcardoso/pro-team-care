from datetime import date
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.repositories.billing_repository import BillingRepository
from app.infrastructure.services.billing_service import BillingService
from app.infrastructure.services.pagbank_webhook_service import PagBankWebhookService
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.billing import (  # Billing Schedule Schemas; Invoice Schemas; Receipt Schemas; Dashboard Schemas; Bulk Operations
    BillingDashboardMetrics,
    BillingDashboardResponse,
    BillingScheduleListParams,
    BillingScheduleListResponse,
    BulkInvoiceGeneration,
    BulkInvoiceGenerationResponse,
    BulkStatusUpdate,
    BulkStatusUpdateResponse,
    ContractBillingScheduleCreate,
    ContractBillingScheduleResponse,
    ContractBillingScheduleUpdate,
    ContractBillingStatus,
    ContractInvoiceCreate,
    ContractInvoiceDetailed,
    ContractInvoiceResponse,
    ContractInvoiceUpdate,
    InvoiceListParams,
    InvoiceListResponse,
    InvoiceStatus,
    PaymentMethod,
    PaymentReceiptCreate,
    PaymentReceiptResponse,
    PaymentReceiptUpdate,
    ReceiptListParams,
    ReceiptListResponse,
    VerificationStatus,
)
from app.presentation.schemas.pagbank import (  # PagBank Schemas
    AutomaticBillingRequest,
    AutomaticBillingResponse,
    BillingMethodStatus,
    BillingMethodUpdate,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PagBankDashboardResponse,
    RecurrentBillingSetupRequest,
    RecurrentBillingSetupResponse,
    SubscriptionCancelRequest,
    SubscriptionCancelResponse,
    TransactionsListResponse,
    WebhookRequest,
    WebhookResponse,
)

router = APIRouter()


# ==========================================
# BILLING SCHEDULE ENDPOINTS
# ==========================================


@router.get("/schedules", response_model=BillingScheduleListResponse)
@require_permission("billing_view", context_type="company")
async def list_billing_schedules(
    params: BillingScheduleListParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List billing schedules with filtering and pagination"""
    repository = BillingRepository(db)

    result = await repository.list_billing_schedules(
        contract_id=params.contract_id,
        billing_cycle=params.billing_cycle,
        is_active=params.is_active,
        next_billing_before=params.next_billing_before,
        page=params.page,
        size=params.size,
    )

    return BillingScheduleListResponse(**result)


@router.get("/schedules/{schedule_id}", response_model=ContractBillingScheduleResponse)
@require_permission("billing_view", context_type="company")
async def get_billing_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get billing schedule by ID"""
    repository = BillingRepository(db)
    schedule = await repository.get_billing_schedule_by_id(schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Billing schedule not found"
        )

    return schedule


@router.post("/schedules", response_model=ContractBillingScheduleResponse)
@require_permission("billing_create", context_type="company")
async def create_billing_schedule(
    schedule_data: ContractBillingScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new billing schedule"""
    repository = BillingRepository(db)

    # Check if schedule already exists for this contract
    existing_schedule = await repository.get_billing_schedule_by_contract(
        schedule_data.contract_id
    )
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Billing schedule already exists for this contract",
        )

    schedule = await repository.create_billing_schedule(schedule_data.model_dump())
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ContractBillingScheduleResponse)
@require_permission("billing_update", context_type="company")
async def update_billing_schedule(
    schedule_id: int,
    schedule_data: ContractBillingScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update billing schedule"""
    repository = BillingRepository(db)

    schedule = await repository.update_billing_schedule(
        schedule_id, schedule_data.model_dump(exclude_unset=True)
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Billing schedule not found"
        )

    return schedule


# ==========================================
# INVOICE ENDPOINTS
# ==========================================


@router.get("/invoices", response_model=InvoiceListResponse)
@require_permission("billing_view", context_type="company")
async def list_invoices(
    params: InvoiceListParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List invoices with filtering and pagination"""
    repository = BillingRepository(db)

    result = await repository.list_invoices(
        contract_id=params.contract_id,
        status=params.status,
        start_date=params.start_date,
        end_date=params.end_date,
        overdue_only=params.overdue_only,
        page=params.page,
        size=params.size,
    )

    return InvoiceListResponse(**result)


@router.get("/invoices/{invoice_id}", response_model=ContractInvoiceDetailed)
@require_permission("billing_view", context_type="company")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get invoice by ID with detailed information"""
    repository = BillingRepository(db)
    invoice = await repository.get_invoice_by_id(invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    # Calculate additional fields for detailed view
    invoice_dict = {
        **invoice.__dict__,
        "receipts_count": len(invoice.receipts) if invoice.receipts else 0,
        "is_overdue": invoice.due_date < date.today()
        and invoice.status in ["pendente", "enviada"],
        "days_overdue": (
            max(0, (date.today() - invoice.due_date).days)
            if invoice.due_date < date.today()
            else 0
        ),
    }

    return ContractInvoiceDetailed.model_validate(invoice_dict)


@router.post("/invoices", response_model=ContractInvoiceResponse)
@require_permission("billing_create", context_type="company")
async def create_invoice(
    invoice_data: ContractInvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new invoice"""
    repository = BillingRepository(db)

    invoice = await repository.create_invoice(invoice_data.model_dump())
    return invoice


@router.put("/invoices/{invoice_id}", response_model=ContractInvoiceResponse)
@require_permission("billing_update", context_type="company")
async def update_invoice(
    invoice_id: int,
    invoice_data: ContractInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update invoice"""
    repository = BillingRepository(db)

    invoice = await repository.update_invoice(
        invoice_id, invoice_data.model_dump(exclude_unset=True)
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    return invoice


@router.patch("/invoices/{invoice_id}/status", response_model=ContractInvoiceResponse)
@require_permission("billing_update", context_type="company")
async def update_invoice_status(
    invoice_id: int,
    status: InvoiceStatus,
    paid_date: Optional[date] = None,
    payment_method: Optional[PaymentMethod] = None,
    payment_reference: Optional[str] = None,
    payment_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update invoice status with payment details"""
    repository = BillingRepository(db)

    kwargs = {}
    if paid_date:
        kwargs["paid_date"] = paid_date
    if payment_method:
        kwargs["payment_method"] = payment_method
    if payment_reference:
        kwargs["payment_reference"] = payment_reference
    if payment_notes:
        kwargs["payment_notes"] = payment_notes

    invoice = await repository.update_invoice_status(invoice_id, status, **kwargs)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    return invoice


# ==========================================
# PAYMENT RECEIPT ENDPOINTS
# ==========================================


@router.get("/receipts", response_model=ReceiptListResponse)
@require_permission("billing_view", context_type="company")
async def list_payment_receipts(
    params: ReceiptListParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List payment receipts with filtering and pagination"""
    repository = BillingRepository(db)

    result = await repository.list_payment_receipts(
        invoice_id=params.invoice_id,
        verification_status=params.verification_status,
        uploaded_by=params.uploaded_by,
        start_date=params.start_date,
        end_date=params.end_date,
        page=params.page,
        size=params.size,
    )

    return ReceiptListResponse(**result)


@router.get("/receipts/{receipt_id}", response_model=PaymentReceiptResponse)
@require_permission("billing_view", context_type="company")
async def get_payment_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get payment receipt by ID"""
    repository = BillingRepository(db)
    receipt = await repository.get_receipt_by_id(receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment receipt not found"
        )

    return receipt


@router.post("/receipts/upload", response_model=PaymentReceiptResponse)
@require_permission("billing_create", context_type="company")
async def upload_payment_receipt(
    invoice_id: int = Form(...),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a payment receipt file"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG and PDF files are allowed",
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )

    # Use billing service to handle file upload
    billing_service = BillingService(db)
    receipt = await billing_service.upload_payment_receipt(
        invoice_id=invoice_id,
        file_name=file.filename,
        file_content=content,
        file_type=file.content_type,
        notes=notes,
    )

    return receipt


@router.patch("/receipts/{receipt_id}/verify", response_model=PaymentReceiptResponse)
@require_permission("billing_approve", context_type="company")
async def verify_payment_receipt(
    receipt_id: int,
    verification_status: VerificationStatus,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify or reject a payment receipt"""
    repository = BillingRepository(db)

    verified_by = current_user.id

    receipt = await repository.update_receipt_verification(
        receipt_id, verification_status, verified_by, notes
    )

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment receipt not found"
        )

    return receipt


# ==========================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# ==========================================


@router.get("/dashboard", response_model=BillingDashboardResponse)
@require_permission("billing_view", context_type="company")
async def get_billing_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get billing dashboard data with metrics and recent activity"""
    repository = BillingRepository(db)

    # Get metrics
    metrics_data = await repository.get_billing_dashboard_metrics()
    metrics = BillingDashboardMetrics(**metrics_data)

    # Get recent invoices (last 10)
    recent_invoices_result = await repository.list_invoices(page=1, size=10)
    recent_invoices = recent_invoices_result["invoices"]

    # Get contracts billing status
    contracts_status_data = await repository.get_contracts_billing_status()
    contracts_status = [
        ContractBillingStatus(**contract) for contract in contracts_status_data
    ]

    # Get upcoming billings (next 30 days)
    upcoming_billings = await repository.get_upcoming_billings(days_ahead=30)

    return BillingDashboardResponse(
        metrics=metrics,
        recent_invoices=recent_invoices,
        contracts_status=contracts_status,
        upcoming_billings=upcoming_billings,
    )


@router.get("/analytics/metrics", response_model=BillingDashboardMetrics)
@require_permission("billing_view", context_type="company")
async def get_billing_metrics(
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get billing analytics metrics"""
    repository = BillingRepository(db)

    metrics_data = await repository.get_billing_dashboard_metrics(company_id)
    return BillingDashboardMetrics(**metrics_data)


@router.get("/contracts/{contract_id}/status", response_model=ContractBillingStatus)
@require_permission("billing_view", context_type="company")
async def get_contract_billing_status(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get billing status for a specific contract"""
    repository = BillingRepository(db)

    # Get contracts status and filter by contract_id
    contracts_status_data = await repository.get_contracts_billing_status()
    contract_status = next(
        (
            contract
            for contract in contracts_status_data
            if contract["contract_id"] == contract_id
        ),
        None,
    )

    if not contract_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or has no billing data",
        )

    return ContractBillingStatus(**contract_status)


# ==========================================
# BULK OPERATIONS ENDPOINTS
# ==========================================


@router.post("/invoices/bulk-generate", response_model=BulkInvoiceGenerationResponse)
@require_permission("billing_create", context_type="company")
async def bulk_generate_invoices(
    request: BulkInvoiceGeneration,
    db: AsyncSession = Depends(get_db),
):
    """Generate invoices in bulk for multiple contracts"""
    repository = BillingRepository(db)

    result = await repository.bulk_generate_invoices(
        contract_ids=request.contract_ids,
        billing_date=request.billing_date,
        force_regenerate=request.force_regenerate,
    )

    return BulkInvoiceGenerationResponse(**result)


@router.patch("/invoices/bulk-status", response_model=BulkStatusUpdateResponse)
@require_permission("billing_update", context_type="company")
async def bulk_update_invoice_status(
    request: BulkStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update status for multiple invoices in bulk"""
    repository = BillingRepository(db)

    successful = 0
    failed = 0
    errors = []
    updated_invoices = []

    for invoice_id in request.invoice_ids:
        try:
            kwargs = {}
            if request.payment_date:
                kwargs["paid_date"] = request.payment_date
            if request.payment_method:
                kwargs["payment_method"] = request.payment_method
            if request.payment_reference:
                kwargs["payment_reference"] = request.payment_reference
            if request.notes:
                kwargs["payment_notes"] = request.notes

            invoice = await repository.update_invoice_status(
                invoice_id, request.new_status, **kwargs
            )

            if invoice:
                updated_invoices.append(invoice_id)
                successful += 1
            else:
                errors.append(f"Invoice {invoice_id} not found")
                failed += 1
        except Exception as e:
            errors.append(f"Error updating invoice {invoice_id}: {str(e)}")
            failed += 1

    return BulkStatusUpdateResponse(
        total_processed=len(request.invoice_ids),
        successful=successful,
        failed=failed,
        errors=errors,
        updated_invoices=updated_invoices,
    )


# ==========================================
# AUTOMATIC BILLING ENDPOINTS
# ==========================================


@router.post("/auto-billing/run")
@require_permission("billing_admin", context_type="company")
async def run_automatic_billing(
    billing_date: Optional[date] = Query(
        None, description="Date to run billing for (default: today)"
    ),
    force_regenerate: bool = Query(
        False, description="Force regenerate existing invoices"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Run automatic billing process for due schedules"""
    billing_service = BillingService(db)

    result = await billing_service.run_automatic_billing(
        billing_date=billing_date, force_regenerate=force_regenerate
    )

    return {"message": "Automatic billing process completed", "result": result}


@router.get("/auto-billing/upcoming")
@require_permission("billing_view", context_type="company")
async def get_upcoming_billings(
    days_ahead: int = Query(30, description="Number of days to look ahead"),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming billing schedules"""
    repository = BillingRepository(db)

    upcoming_billings = await repository.get_upcoming_billings(days_ahead=days_ahead)

    return {
        "upcoming_billings": upcoming_billings,
        "total_count": len(upcoming_billings),
        "days_ahead": days_ahead,
    }


# ==========================================
# PAGBANK INTEGRATION ENDPOINTS
# ==========================================


@router.get("/pagbank/billing-method/{contract_id}", response_model=BillingMethodStatus)
@require_permission("billing_view", context_type="company")
async def get_billing_method_status(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get billing method status for a contract"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.get_billing_method_status(contract_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting billing method status: {str(e)}",
        )


@router.post("/pagbank/setup-recurrent", response_model=RecurrentBillingSetupResponse)
@require_permission("billing_manage", context_type="company")
async def setup_recurrent_billing(
    request: RecurrentBillingSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Setup recurrent billing with PagBank for a contract"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.setup_recurrent_billing(
            request.contract_id, request.client_data.dict()
        )
        return RecurrentBillingSetupResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up recurrent billing: {str(e)}",
        )


@router.post("/pagbank/setup-manual/{contract_id}")
@require_permission("billing_manage", context_type="company")
async def setup_manual_billing(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Setup manual billing for a contract"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.setup_manual_billing(contract_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up manual billing: {str(e)}",
        )


@router.post("/pagbank/create-checkout", response_model=CheckoutSessionResponse)
@require_permission("billing_manage", context_type="company")
async def create_checkout_session(
    request: CheckoutSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create PagBank checkout session for an invoice"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.create_checkout_for_invoice(request.invoice_id)
        return CheckoutSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout session: {str(e)}",
        )


@router.post("/pagbank/cancel-subscription", response_model=SubscriptionCancelResponse)
@require_permission("billing_manage", context_type="company")
async def cancel_recurrent_subscription(
    request: SubscriptionCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel recurrent subscription for a contract"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.cancel_recurrent_subscription(
            request.contract_id
        )
        return SubscriptionCancelResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling subscription: {str(e)}",
        )


@router.post("/pagbank/run-recurrent-billing", response_model=AutomaticBillingResponse)
@require_permission("billing_admin", context_type="system")
async def run_automatic_recurrent_billing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute automatic recurrent billing for all due schedules"""
    try:
        billing_service = BillingService(db)
        result = await billing_service.run_automatic_recurrent_billing()
        return AutomaticBillingResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running automatic recurrent billing: {str(e)}",
        )


@router.get(
    "/pagbank/transactions/{invoice_id}", response_model=TransactionsListResponse
)
@require_permission("billing_view", context_type="company")
async def get_invoice_pagbank_transactions(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all PagBank transactions for an invoice"""
    try:
        repository = BillingRepository(db)
        transactions = await repository.get_pagbank_transactions_by_invoice(invoice_id)

        return TransactionsListResponse(
            transactions=transactions,
            total=len(transactions),
            page=1,
            size=len(transactions),
            pages=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting PagBank transactions: {str(e)}",
        )


@router.post("/pagbank/webhooks", response_model=WebhookResponse)
async def pagbank_webhook_handler(
    request: WebhookRequest,
    signature: str = Query(..., alias="x-hub-signature-256"),
    db: AsyncSession = Depends(get_db),
):
    """Handle PagBank webhook notifications"""
    try:
        webhook_service = PagBankWebhookService(db)
        result = await webhook_service.handle_webhook_notification(
            request.dict(), signature
        )

        return WebhookResponse(
            success=result.get("success", False),
            message=result.get("message", "Webhook processed"),
            error=result.get("error"),
            notification_type=request.type,
            processed_data=result,
        )
    except Exception as e:
        return WebhookResponse(
            success=False,
            error=f"Webhook processing failed: {str(e)}",
            notification_type=request.type,
        )
