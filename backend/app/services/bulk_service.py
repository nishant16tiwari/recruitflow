from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.enums import HistoryEventType, Stage
from app.schemas.bulk import BulkActionResult
from app.services import history_service, pipeline_service


def bulk_advance(db: Session, application_ids: list[int], actor_id: int) -> list[BulkActionResult]:
    """
    WHY per-item commits rather than one commit for the whole batch: if
    item 7 out of 20 hits an unexpected DB error, a shared transaction
    would force a rollback that wipes out items 1-6, which already
    reported success to the caller in earlier iterations - a false
    positive. Committing each successful item immediately means "success"
    reported in the response is always already durably saved, and one
    item's failure genuinely cannot affect any other item, exactly as the
    bulk-action requirement demands.
    """
    results: list[BulkActionResult] = []

    for application_id in application_ids:
        application = db.get(Application, application_id)
        if not application:
            results.append(
                BulkActionResult(application_id=application_id, success=False, reason="Application not found")
            )
            continue

        is_valid, next_stage, reason = pipeline_service.check_advance(application, requested_to_stage=None)
        if not is_valid:
            results.append(
                BulkActionResult(application_id=application_id, success=False, reason=reason)
            )
            continue

        try:
            old_stage = application.current_stage
            pipeline_service.touch_stage(application, next_stage)
            history_service.record_event(
                db,
                application_id=application.id,
                event_type=HistoryEventType.STAGE_CHANGE,
                actor_id=actor_id,
                from_stage=old_stage,
                to_stage=next_stage,
                note="Bulk advance",
            )
            db.commit()
            results.append(
                BulkActionResult(
                    application_id=application_id, success=True, old_stage=old_stage, new_stage=next_stage
                )
            )
        except Exception as exc:  # noqa: BLE001 - deliberately broad: one bad row must not abort the batch
            db.rollback()
            results.append(
                BulkActionResult(application_id=application_id, success=False, reason=f"Unexpected error: {exc}")
            )

    return results


def bulk_reject(db: Session, application_ids: list[int], actor_id: int) -> list[BulkActionResult]:
    results: list[BulkActionResult] = []

    for application_id in application_ids:
        application = db.get(Application, application_id)
        if not application:
            results.append(
                BulkActionResult(application_id=application_id, success=False, reason="Application not found")
            )
            continue

        is_valid, reason = pipeline_service.check_reject(application)
        if not is_valid:
            results.append(BulkActionResult(application_id=application_id, success=False, reason=reason))
            continue

        try:
            old_stage = application.current_stage
            application.previous_stage_before_rejection = old_stage
            pipeline_service.touch_stage(application, Stage.REJECTED)
            history_service.record_event(
                db,
                application_id=application.id,
                event_type=HistoryEventType.REJECTED,
                actor_id=actor_id,
                from_stage=old_stage,
                to_stage=Stage.REJECTED,
                note="Bulk reject",
            )
            db.commit()
            results.append(
                BulkActionResult(
                    application_id=application_id,
                    success=True,
                    old_stage=old_stage,
                    new_stage=Stage.REJECTED,
                )
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            results.append(
                BulkActionResult(application_id=application_id, success=False, reason=f"Unexpected error: {exc}")
            )

    return results
