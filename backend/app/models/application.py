from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Stage


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # An application belongs to exactly one job opening. RESTRICT (not CASCADE)
    # ensures a job can never be deleted out from under its applications -
    # in practice jobs are archived, never deleted, but this is a safety net.
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job_openings.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    candidate_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="Other", index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    applied_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date(), index=True)

    current_stage: Mapped[Stage] = mapped_column(
        Enum(Stage, name="application_stage"), nullable=False, default=Stage.APPLIED, index=True
    )

    # WHY this field matters: stall detection and reinstatement both depend
    # on knowing exactly when the application entered its CURRENT stage -
    # not when it was created. This is updated every time current_stage changes.
    stage_entered_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    # WHY nullable: only populated while current_stage == REJECTED. Holds the
    # stage the candidate was in immediately before rejection, so reinstatement
    # can restore it exactly instead of resetting to Applied.
    previous_stage_before_rejection: Mapped[Stage | None] = mapped_column(
        Enum(Stage, name="application_stage"), nullable=True
    )

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), index=True)

    job = relationship("JobOpening", back_populates="applications")
    panel = relationship("ApplicationPanel", back_populates="application", cascade="all, delete-orphan")
    history = relationship(
        "ApplicationHistory", back_populates="application", cascade="all, delete-orphan",
        order_by="ApplicationHistory.created_at",
    )
    feedback_entries = relationship("Feedback", back_populates="application", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        # Speeds up the very common "applications for job X in stage Y" query
        # used by both the job detail page and dashboard stage breakdown.
        Index("ix_applications_job_stage", "job_id", "current_stage"),
    )
