"""
Post-Reset Verification and Audit Service.
"""

from typing import Optional
from datetime import datetime
from app.models.maintenance import MaintenanceRecord
from app.models.counter import WastePadRecord
from app.core.constants import MaintenanceOperation, OperationResult
from app.database.repository import MaintenanceRepository
from app.core.logger import get_logger

log = get_logger("app.services.verification")


class VerificationService:
    def __init__(self, repo: Optional[MaintenanceRepository] = None):
        self.repo = repo or MaintenanceRepository()

    def verify_reset(
        self,
        serial_number: str,
        operation: MaintenanceOperation,
        pre_record: WastePadRecord,
        post_record: WastePadRecord,
        notes: Optional[str] = None
    ) -> MaintenanceRecord:
        """Verify counter transition before/after reset and record audit log."""
        pre_val = pre_record.main_pad.current_points
        post_val = post_record.main_pad.current_points

        # Verification rule: post counter must be strictly less than pre counter (ideally 0)
        is_verified = (post_val < pre_val) or (post_val == 0)
        result_status = OperationResult.VERIFIED if is_verified else OperationResult.FAILED

        err_msg = None
        if not is_verified:
            err_msg = f"Post-reset verification failed: counter did not decrease (pre={pre_val}, post={post_val})"
            log.error(err_msg)
        else:
            log.info(f"Reset verified successfully: pre={pre_val} -> post={post_val}")

        record = MaintenanceRecord(
            timestamp=datetime.now(),
            printer_model="Epson L3110 Series",
            serial_number=serial_number,
            operation_type=operation,
            pre_counter_value=pre_val,
            post_counter_value=post_val,
            status=result_status,
            error_message=err_msg,
            notes=notes,
        )

        try:
            self.repo.add_record(record)
        except Exception as e:
            log.error(f"Failed to persist maintenance record: {e}")

        return record
