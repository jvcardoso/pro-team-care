from typing import List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.infrastructure.auth import get_current_user
from app.domain.entities.user import User
from app.presentation.decorators.simple_permissions import require_permission
from app.infrastructure.services.billing_scheduler_service import (
    billing_scheduler,
    JobResult,
    JobStatus
)

router = APIRouter()


# ==========================================
# REQUEST/RESPONSE SCHEMAS
# ==========================================

class ScheduleAutoBillingRequest(BaseModel):
    billing_date: Optional[str] = Field(None, description="Billing date (YYYY-MM-DD)")
    force_regenerate: bool = Field(default=False, description="Force regenerate existing invoices")
    contract_ids: Optional[List[int]] = Field(None, description="Specific contract IDs to process")


class ScheduleFallbackRequest(BaseModel):
    days_back: int = Field(default=7, description="Days to look back for failed billings", ge=1, le=30)


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[dict] = None
    error_message: Optional[str] = None
    metrics: Optional[dict] = None


class SchedulerMetricsResponse(BaseModel):
    total_jobs_executed: int
    completed_jobs: int
    failed_jobs: int
    running_jobs: int
    success_rate: float
    jobs_last_24h: int
    average_execution_time: float
    max_concurrent_jobs: int
    job_timeout_seconds: int


# ==========================================
# JOB SCHEDULING ENDPOINTS
# ==========================================

@router.post("/jobs/schedule-auto-billing")
@require_permission("billing_admin", context_type="system")
async def schedule_automatic_billing(
    request: ScheduleAutoBillingRequest,
    current_user: User = Depends(get_current_user),
):
    """Schedule automatic billing job for due schedules"""
    try:
        # Parse billing date if provided
        billing_date = None
        if request.billing_date:
            try:
                billing_date = datetime.strptime(request.billing_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid billing_date format. Use YYYY-MM-DD"
                )

        job_id = await billing_scheduler.schedule_automatic_billing(
            billing_date=billing_date,
            force_regenerate=request.force_regenerate,
            contract_ids=request.contract_ids
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": "Automatic billing job scheduled successfully",
            "billing_date": billing_date.isoformat() if billing_date else None
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling automatic billing: {str(e)}"
        )


@router.post("/jobs/schedule-recurrent-billing")
@require_permission("billing_admin", context_type="system")
async def schedule_recurrent_billing(
    current_user: User = Depends(get_current_user),
):
    """Schedule recurrent billing processing job"""
    try:
        job_id = await billing_scheduler.schedule_recurrent_billing()

        return {
            "success": True,
            "job_id": job_id,
            "message": "Recurrent billing job scheduled successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling recurrent billing: {str(e)}"
        )


@router.post("/jobs/schedule-fallback-processing")
@require_permission("billing_admin", context_type="system")
async def schedule_fallback_processing(
    request: ScheduleFallbackRequest,
    current_user: User = Depends(get_current_user),
):
    """Schedule fallback processing for failed recurrent billings"""
    try:
        job_id = await billing_scheduler.schedule_fallback_processing(
            days_back=request.days_back
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": "Fallback processing job scheduled successfully",
            "days_back": request.days_back
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling fallback processing: {str(e)}"
        )


@router.post("/jobs/schedule-status-sync")
@require_permission("billing_admin", context_type="system")
async def schedule_status_sync(
    current_user: User = Depends(get_current_user),
):
    """Schedule invoice status synchronization job"""
    try:
        job_id = await billing_scheduler.schedule_invoice_status_sync()

        return {
            "success": True,
            "job_id": job_id,
            "message": "Status sync job scheduled successfully"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling status sync: {str(e)}"
        )


# ==========================================
# JOB MONITORING ENDPOINTS
# ==========================================

@router.get("/jobs/{job_id}", response_model=JobResponse)
@require_permission("billing_view", context_type="system")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get status of a specific job"""
    job_result = await billing_scheduler.get_job_status(job_id)

    if not job_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return JobResponse(
        job_id=job_result.job_id,
        job_type=job_result.job_type,
        status=job_result.status.value,
        started_at=job_result.started_at,
        completed_at=job_result.completed_at,
        result_data=job_result.result_data,
        error_message=job_result.error_message,
        metrics=job_result.metrics
    )


@router.get("/jobs", response_model=List[JobResponse])
@require_permission("billing_view", context_type="system")
async def list_job_history(
    limit: int = Query(50, description="Maximum number of jobs to return", ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """List job execution history"""
    job_results = await billing_scheduler.get_job_history(limit=limit)

    return [
        JobResponse(
            job_id=result.job_id,
            job_type=result.job_type,
            status=result.status.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            result_data=result.result_data,
            error_message=result.error_message,
            metrics=result.metrics
        )
        for result in job_results
    ]


@router.get("/jobs/running/list")
@require_permission("billing_view", context_type="system")
async def list_running_jobs(
    current_user: User = Depends(get_current_user),
):
    """List all currently running jobs"""
    running_jobs = await billing_scheduler.list_running_jobs()

    return {
        "running_jobs": running_jobs,
        "total_running": len(running_jobs)
    }


@router.post("/jobs/{job_id}/cancel")
@require_permission("billing_admin", context_type="system")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel a running job"""
    success = await billing_scheduler.cancel_job(job_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not running"
        )

    return {
        "success": True,
        "job_id": job_id,
        "message": "Job cancelled successfully"
    }


# ==========================================
# SCHEDULER METRICS ENDPOINTS
# ==========================================

@router.get("/scheduler/metrics", response_model=SchedulerMetricsResponse)
@require_permission("billing_view", context_type="system")
async def get_scheduler_metrics(
    current_user: User = Depends(get_current_user),
):
    """Get scheduler performance metrics"""
    metrics = billing_scheduler.get_scheduler_metrics()

    return SchedulerMetricsResponse(**metrics)


@router.get("/scheduler/health")
@require_permission("billing_view", context_type="system")
async def get_scheduler_health(
    current_user: User = Depends(get_current_user),
):
    """Get scheduler health status"""
    running_jobs = await billing_scheduler.list_running_jobs()
    metrics = billing_scheduler.get_scheduler_metrics()

    # Determine health status
    health_status = "healthy"
    issues = []

    # Check for too many failed jobs
    if metrics["total_jobs_executed"] > 0:
        failure_rate = (metrics["failed_jobs"] / metrics["total_jobs_executed"]) * 100
        if failure_rate > 20:  # More than 20% failure rate
            health_status = "degraded"
            issues.append(f"High failure rate: {failure_rate:.1f}%")

    # Check for stuck jobs (running for more than timeout)
    max_timeout = billing_scheduler.job_timeout
    if len(running_jobs) > metrics["max_concurrent_jobs"]:
        health_status = "degraded"
        issues.append(f"Too many concurrent jobs: {len(running_jobs)}")

    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "running_jobs_count": len(running_jobs),
        "total_jobs_executed": metrics["total_jobs_executed"],
        "success_rate": metrics["success_rate"],
        "average_execution_time": metrics["average_execution_time"],
        "issues": issues,
        "uptime_info": {
            "max_concurrent_jobs": metrics["max_concurrent_jobs"],
            "job_timeout_seconds": metrics["job_timeout_seconds"],
            "jobs_last_24h": metrics["jobs_last_24h"]
        }
    }


# ==========================================
# CONVENIENCE ENDPOINTS
# ==========================================

@router.post("/quick-actions/run-daily-billing")
@require_permission("billing_admin", context_type="system")
async def run_daily_billing_jobs(
    current_user: User = Depends(get_current_user),
):
    """Run all daily billing jobs in sequence"""
    try:
        jobs_scheduled = []

        # 1. Schedule automatic billing
        auto_billing_job = await billing_scheduler.schedule_automatic_billing()
        jobs_scheduled.append({
            "type": "automatic_billing",
            "job_id": auto_billing_job
        })

        # 2. Schedule recurrent billing
        recurrent_job = await billing_scheduler.schedule_recurrent_billing()
        jobs_scheduled.append({
            "type": "recurrent_billing",
            "job_id": recurrent_job
        })

        # 3. Schedule fallback processing
        fallback_job = await billing_scheduler.schedule_fallback_processing(days_back=3)
        jobs_scheduled.append({
            "type": "fallback_processing",
            "job_id": fallback_job
        })

        # 4. Schedule status sync
        sync_job = await billing_scheduler.schedule_invoice_status_sync()
        jobs_scheduled.append({
            "type": "status_sync",
            "job_id": sync_job
        })

        return {
            "success": True,
            "message": "Daily billing jobs scheduled successfully",
            "jobs_scheduled": jobs_scheduled,
            "total_jobs": len(jobs_scheduled)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling daily billing jobs: {str(e)}"
        )