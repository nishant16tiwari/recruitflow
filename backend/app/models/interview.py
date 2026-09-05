from datetime import date, datetime, time

from sqlalchemy import Date, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    interview_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Video Call")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    application = relationship("Application", back_populates="interviews")
    interview_interviewers = relationship(
        "InterviewInterviewer", back_populates="interview", cascade="all, delete-orphan"
    )
    # Convenience relationship straight to User rows (through the join
    # table) so the API schema can return interviewer names/emails without
    # the caller having to resolve InterviewInterviewer -> User manually.
    interviewers = relationship(
        "User", secondary="interview_interviewers", viewonly=True
    )


class InterviewInterviewer(Base):
    """Which interviewer(s) are on a specific scheduled interview."""

    __tablename__ = "interview_interviewers"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    interview = relationship("Interview", back_populates="interview_interviewers")
