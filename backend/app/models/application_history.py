from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import HistoryEventType, Stage


class ApplicationHistory(Base):
    """
    Append-only audit log. WHY there is no update/delete anywhere in this
    codebase for this table: the requirement is that history must be
    tamper-proof, so the guarantee has to come from "no code path exists
    to mutate it" rather than from a permission check that could be
    misconfigured. Every service function that changes application state
    creates a new row here in the SAME transaction as the state change,
    so history and state can never drift apart.
    """

    __tablename__ = "application_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[HistoryEventType] = mapped_column(
        Enum(HistoryEventType, name="history_event_type"), nullable=False
    )
    from_stage: Mapped[Stage | None] = mapped_column(Enum(Stage, name="application_stage"), nullable=True)
    to_stage: Mapped[Stage | None] = mapped_column(Enum(Stage, name="application_stage"), nullable=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    application = relationship("Application", back_populates="history")
    actor = relationship("User")
