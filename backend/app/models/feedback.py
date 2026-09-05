from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Feedback(Base):
    """
    Interviewer feedback. Also mirrored into ApplicationHistory at write time
    so the timeline view has a single source to read from, but this table
    remains the canonical, immutable record (e.g. if we ever add a
    "feedback details" page).
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    application = relationship("Application", back_populates="feedback_entries")
    interviewer = relationship("User")
