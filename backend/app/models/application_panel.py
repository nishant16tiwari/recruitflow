from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationPanel(Base):
    """
    Join table: which interviewers are assigned to which applications.
    Many-to-many. Role correctness (only INTERVIEWER-role users may be added)
    is enforced in the service layer, since a plain FK can't express
    "FK to users WHERE role = INTERVIEWER" in a portable way.
    """

    __tablename__ = "application_panel"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now())

    application = relationship("Application", back_populates="panel")
    interviewer = relationship("User", back_populates="panel_assignments")

    __table_args__ = (
        UniqueConstraint("application_id", "interviewer_id", name="uq_application_interviewer"),
    )
