from datetime import datetime

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Stage


class AlertDismissal(Base):
    """
    WHY keyed by (application_id, stage, stage_entered_at) rather than just
    application_id: a dismissal must only suppress ONE stall episode, not
    all future stalls on that application forever.

    stage_entered_at changes every time the application's stage changes
    (including reinstatement, which resets it). So this triple uniquely
    identifies "this particular stretch of time the application spent in
    this particular stage." Dismissing it only matches that exact triple -
    the moment the application moves to a new stage (new stage_entered_at),
    the old dismissal simply stops being relevant, and if it stalls again
    later (same or different stage, new stage_entered_at), no matching
    dismissal exists yet, so the alert naturally reappears with zero cron
    jobs or expiry logic needed.
    """

    __tablename__ = "alert_dismissals"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[Stage] = mapped_column(Enum(Stage, name="application_stage"), nullable=False)
    stage_entered_at: Mapped[datetime] = mapped_column(nullable=False)
    dismissed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    dismissed_at: Mapped[datetime] = mapped_column(server_default=func.now())

    application = relationship("Application")

    __table_args__ = (
        UniqueConstraint(
            "application_id", "stage", "stage_entered_at", name="uq_alert_dismissal_episode"
        ),
    )
