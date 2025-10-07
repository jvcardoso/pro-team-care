import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.repositories.billing_repository import BillingRepository
from app.infrastructure.services.billing_service import BillingService

logger = structlog.get_logger()


class JobStatus(Enum):
    """Job execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Result of a scheduled job execution"""

    job_id: str
    job_type: str
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class BillingSchedulerService:
    """Service for scheduling and executing billing automation jobs"""

    def __init__(self):
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self.job_results: List[JobResult] = []
        self.max_concurrent_jobs = 3
        self.job_timeout = 3600  # 1 hour in seconds

    async def schedule_automatic_billing(
        self,
        billing_date: Optional[date] = None,
        force_regenerate: bool = False,
        contract_ids: Optional[List[int]] = None,
    ) -> str:
        """Schedule automatic billing job"""
        if billing_date is None:
            billing_date = date.today()

        job_id = f"auto_billing_{billing_date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}"

        # Check if similar job is already running
        if self._is_similar_job_running("auto_billing", billing_date):
            raise ValueError(
                f"Automatic billing job for {billing_date} is already running"
            )

        logger.info(
            "Scheduling automatic billing job",
            job_id=job_id,
            billing_date=billing_date,
            force_regenerate=force_regenerate,
            contract_ids=contract_ids,
        )

        # Create and start the job
        task = asyncio.create_task(
            self._execute_automatic_billing_job(
                job_id=job_id,
                billing_date=billing_date,
                force_regenerate=force_regenerate,
                contract_ids=contract_ids,
            )
        )

        self.running_jobs[job_id] = task
        return job_id

    async def schedule_recurrent_billing(self) -> str:
        """Schedule recurrent billing processing job"""
        job_id = f"recurrent_billing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Check if recurrent billing is already running
        if self._is_similar_job_running("recurrent_billing"):
            raise ValueError("Recurrent billing job is already running")

        logger.info("Scheduling recurrent billing job", job_id=job_id)

        # Create and start the job
        task = asyncio.create_task(self._execute_recurrent_billing_job(job_id=job_id))

        self.running_jobs[job_id] = task
        return job_id

    async def schedule_fallback_processing(self, days_back: int = 7) -> str:
        """Schedule fallback processing for failed recurrent billings"""
        job_id = f"fallback_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(
            "Scheduling fallback processing job", job_id=job_id, days_back=days_back
        )

        # Create and start the job
        task = asyncio.create_task(
            self._execute_fallback_processing_job(job_id=job_id, days_back=days_back)
        )

        self.running_jobs[job_id] = task
        return job_id

    async def schedule_invoice_status_sync(self) -> str:
        """Schedule job to sync invoice status with payment providers"""
        job_id = f"status_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info("Scheduling invoice status sync job", job_id=job_id)

        # Create and start the job
        task = asyncio.create_task(self._execute_status_sync_job(job_id=job_id))

        self.running_jobs[job_id] = task
        return job_id

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id not in self.running_jobs:
            return False

        task = self.running_jobs[job_id]
        if not task.done():
            task.cancel()
            logger.info("Job cancelled", job_id=job_id)

            # Update job result
            for result in self.job_results:
                if result.job_id == job_id:
                    result.status = JobStatus.CANCELLED
                    result.completed_at = datetime.now()
                    break

        return True

    async def get_job_status(self, job_id: str) -> Optional[JobResult]:
        """Get status of a specific job"""
        for result in self.job_results:
            if result.job_id == job_id:
                return result
        return None

    async def list_running_jobs(self) -> List[str]:
        """List all currently running jobs"""
        # Clean up completed tasks
        await self._cleanup_completed_tasks()
        return list(self.running_jobs.keys())

    async def get_job_history(self, limit: int = 50) -> List[JobResult]:
        """Get job execution history"""
        # Sort by completion time, most recent first
        sorted_results = sorted(
            self.job_results, key=lambda x: x.completed_at or x.started_at, reverse=True
        )
        return sorted_results[:limit]

    # ==========================================
    # PRIVATE JOB EXECUTION METHODS
    # ==========================================

    async def _execute_automatic_billing_job(
        self,
        job_id: str,
        billing_date: date,
        force_regenerate: bool,
        contract_ids: Optional[List[int]],
    ) -> None:
        """Execute automatic billing job"""
        job_result = JobResult(
            job_id=job_id,
            job_type="auto_billing",
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )
        self.job_results.append(job_result)

        try:
            async with get_db() as db:
                billing_service = BillingService(db)

                logger.info(
                    "Starting automatic billing execution",
                    job_id=job_id,
                    billing_date=billing_date,
                )

                result = await billing_service.run_automatic_billing(
                    billing_date=billing_date, force_regenerate=force_regenerate
                )

                job_result.status = JobStatus.COMPLETED
                job_result.completed_at = datetime.now()
                job_result.result_data = result
                job_result.metrics = {
                    "total_schedules_processed": result.get(
                        "total_schedules_processed", 0
                    ),
                    "successful_invoices": result.get("successful_invoices", 0),
                    "failed_invoices": result.get("failed_invoices", 0),
                    "execution_time_seconds": (
                        job_result.completed_at - job_result.started_at
                    ).total_seconds(),
                }

                logger.info(
                    "Automatic billing job completed successfully",
                    job_id=job_id,
                    metrics=job_result.metrics,
                )

        except Exception as e:
            job_result.status = JobStatus.FAILED
            job_result.completed_at = datetime.now()
            job_result.error_message = str(e)

            logger.error(
                "Automatic billing job failed",
                job_id=job_id,
                error=str(e),
                exc_info=True,
            )

        finally:
            # Remove from running jobs
            self.running_jobs.pop(job_id, None)

    async def _execute_recurrent_billing_job(self, job_id: str) -> None:
        """Execute recurrent billing job"""
        job_result = JobResult(
            job_id=job_id,
            job_type="recurrent_billing",
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )
        self.job_results.append(job_result)

        try:
            async with get_db() as db:
                billing_service = BillingService(db)

                logger.info("Starting recurrent billing execution", job_id=job_id)

                result = await billing_service.run_automatic_recurrent_billing()

                job_result.status = JobStatus.COMPLETED
                job_result.completed_at = datetime.now()
                job_result.result_data = result
                job_result.metrics = {
                    "total_processed": result.get("total_processed", 0),
                    "successful": result.get("successful", 0),
                    "failed": result.get("failed", 0),
                    "execution_time_seconds": (
                        job_result.completed_at - job_result.started_at
                    ).total_seconds(),
                }

                logger.info(
                    "Recurrent billing job completed successfully",
                    job_id=job_id,
                    metrics=job_result.metrics,
                )

        except Exception as e:
            job_result.status = JobStatus.FAILED
            job_result.completed_at = datetime.now()
            job_result.error_message = str(e)

            logger.error(
                "Recurrent billing job failed",
                job_id=job_id,
                error=str(e),
                exc_info=True,
            )

        finally:
            # Remove from running jobs
            self.running_jobs.pop(job_id, None)

    async def _execute_fallback_processing_job(
        self, job_id: str, days_back: int
    ) -> None:
        """Execute fallback processing job"""
        job_result = JobResult(
            job_id=job_id,
            job_type="fallback_processing",
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )
        self.job_results.append(job_result)

        try:
            async with get_db() as db:
                billing_repository = BillingRepository(db)
                billing_service = BillingService(db)

                logger.info(
                    "Starting fallback processing", job_id=job_id, days_back=days_back
                )

                # Get failed recurrent billings
                failed_schedules = (
                    await billing_repository.get_failed_recurrent_billings(
                        days_back=days_back
                    )
                )

                processed = 0
                fallbacks_triggered = 0
                errors = []

                for schedule in failed_schedules:
                    try:
                        # Process billing failure
                        failure_result = (
                            await billing_service.process_recurrent_billing_failure(
                                schedule_id=schedule.id,
                                error_details={
                                    "reason": "scheduled_fallback_processing"
                                },
                            )
                        )

                        processed += 1
                        if failure_result.get("fallback_triggered"):
                            fallbacks_triggered += 1

                        logger.info(
                            "Processed failed schedule",
                            job_id=job_id,
                            schedule_id=schedule.id,
                            fallback_triggered=failure_result.get("fallback_triggered"),
                        )

                    except Exception as e:
                        error_msg = f"Error processing schedule {schedule.id}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg, job_id=job_id)

                job_result.status = JobStatus.COMPLETED
                job_result.completed_at = datetime.now()
                job_result.result_data = {
                    "total_failed_schedules": len(failed_schedules),
                    "processed": processed,
                    "fallbacks_triggered": fallbacks_triggered,
                    "errors": errors,
                }
                job_result.metrics = {
                    "total_processed": processed,
                    "fallbacks_triggered": fallbacks_triggered,
                    "error_count": len(errors),
                    "execution_time_seconds": (
                        job_result.completed_at - job_result.started_at
                    ).total_seconds(),
                }

                logger.info(
                    "Fallback processing job completed successfully",
                    job_id=job_id,
                    metrics=job_result.metrics,
                )

        except Exception as e:
            job_result.status = JobStatus.FAILED
            job_result.completed_at = datetime.now()
            job_result.error_message = str(e)

            logger.error(
                "Fallback processing job failed",
                job_id=job_id,
                error=str(e),
                exc_info=True,
            )

        finally:
            # Remove from running jobs
            self.running_jobs.pop(job_id, None)

    async def _execute_status_sync_job(self, job_id: str) -> None:
        """Execute invoice status synchronization job"""
        job_result = JobResult(
            job_id=job_id,
            job_type="status_sync",
            status=JobStatus.RUNNING,
            started_at=datetime.now(),
        )
        self.job_results.append(job_result)

        try:
            async with get_db() as db:
                billing_repository = BillingRepository(db)

                logger.info("Starting invoice status sync", job_id=job_id)

                # Get recent invoices with pending payments
                cutoff_date = date.today() - timedelta(days=30)
                invoices_result = await billing_repository.list_invoices(
                    start_date=cutoff_date,
                    status="enviada",  # Sent invoices
                    page=1,
                    size=1000,
                )

                invoices = invoices_result["invoices"]
                synced = 0
                updated = 0
                errors = []

                for invoice in invoices:
                    try:
                        # Get PagBank transactions for this invoice
                        transactions = await billing_repository.get_pagbank_transactions_by_invoice(
                            invoice.id
                        )

                        synced += 1

                        # Check if any transaction shows payment completed
                        for transaction in transactions:
                            if transaction.status == "approved":
                                # Update invoice status
                                await billing_repository.update_invoice_status(
                                    invoice.id,
                                    "paga",
                                    paid_date=transaction.updated_at.date(),
                                    payment_method="pagbank",
                                    payment_reference=transaction.pagbank_charge_id,
                                )
                                updated += 1
                                break

                        logger.debug(
                            "Synced invoice status",
                            job_id=job_id,
                            invoice_id=invoice.id,
                            transactions_count=len(transactions),
                        )

                    except Exception as e:
                        error_msg = f"Error syncing invoice {invoice.id}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg, job_id=job_id)

                job_result.status = JobStatus.COMPLETED
                job_result.completed_at = datetime.now()
                job_result.result_data = {
                    "total_invoices": len(invoices),
                    "synced": synced,
                    "updated": updated,
                    "errors": errors,
                }
                job_result.metrics = {
                    "invoices_synced": synced,
                    "invoices_updated": updated,
                    "error_count": len(errors),
                    "execution_time_seconds": (
                        job_result.completed_at - job_result.started_at
                    ).total_seconds(),
                }

                logger.info(
                    "Status sync job completed successfully",
                    job_id=job_id,
                    metrics=job_result.metrics,
                )

        except Exception as e:
            job_result.status = JobStatus.FAILED
            job_result.completed_at = datetime.now()
            job_result.error_message = str(e)

            logger.error(
                "Status sync job failed", job_id=job_id, error=str(e), exc_info=True
            )

        finally:
            # Remove from running jobs
            self.running_jobs.pop(job_id, None)

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    def _is_similar_job_running(
        self, job_type: str, context_date: Optional[date] = None
    ) -> bool:
        """Check if a similar job is already running"""
        for job_id, task in self.running_jobs.items():
            if not task.done():
                if job_type == "auto_billing" and context_date:
                    if job_id.startswith(
                        f"auto_billing_{context_date.strftime('%Y%m%d')}"
                    ):
                        return True
                elif job_type in job_id:
                    return True
        return False

    async def _cleanup_completed_tasks(self) -> None:
        """Remove completed tasks from running jobs"""
        completed_jobs = []
        for job_id, task in self.running_jobs.items():
            if task.done():
                completed_jobs.append(job_id)

        for job_id in completed_jobs:
            self.running_jobs.pop(job_id, None)

    def get_scheduler_metrics(self) -> Dict[str, Any]:
        """Get scheduler performance metrics"""
        total_jobs = len(self.job_results)
        completed_jobs = len(
            [r for r in self.job_results if r.status == JobStatus.COMPLETED]
        )
        failed_jobs = len([r for r in self.job_results if r.status == JobStatus.FAILED])
        running_jobs = len(self.running_jobs)

        recent_jobs = [
            r
            for r in self.job_results
            if r.started_at >= datetime.now() - timedelta(hours=24)
        ]

        return {
            "total_jobs_executed": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "running_jobs": running_jobs,
            "success_rate": (
                (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            ),
            "jobs_last_24h": len(recent_jobs),
            "average_execution_time": self._calculate_average_execution_time(),
            "max_concurrent_jobs": self.max_concurrent_jobs,
            "job_timeout_seconds": self.job_timeout,
        }

    def _calculate_average_execution_time(self) -> float:
        """Calculate average execution time for completed jobs"""
        completed_jobs_with_time = [
            r
            for r in self.job_results
            if r.status == JobStatus.COMPLETED and r.completed_at
        ]

        if not completed_jobs_with_time:
            return 0.0

        total_time = sum(
            [
                (r.completed_at - r.started_at).total_seconds()
                for r in completed_jobs_with_time
            ]
        )

        return total_time / len(completed_jobs_with_time)


# Global scheduler instance
billing_scheduler = BillingSchedulerService()
