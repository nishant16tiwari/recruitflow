import enum


class UserRole(str, enum.Enum):
    RECRUITER = "RECRUITER"
    INTERVIEWER = "INTERVIEWER"


class JobStatus(str, enum.Enum):
    OPEN = "OPEN"
    ARCHIVED = "ARCHIVED"


class Stage(str, enum.Enum):
    """
    The pipeline stages. REJECTED is modeled as a stage value on the
    application itself (rather than a separate boolean) so that "current
    state" always has one source of truth, and the valid-transition map
    (see services/pipeline.py) can treat REJECTED uniformly.
    """

    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    HIRED = "Hired"
    REJECTED = "Rejected"


class HistoryEventType(str, enum.Enum):
    CREATED = "CREATED"
    STAGE_CHANGE = "STAGE_CHANGE"
    REJECTED = "REJECTED"
    REINSTATED = "REINSTATED"
    FEEDBACK = "FEEDBACK"
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED"
    INTERVIEWER_ASSIGNED = "INTERVIEWER_ASSIGNED"
    INTERVIEWER_REMOVED = "INTERVIEWER_REMOVED"
    INTERVIEW_CANCELLED = "INTERVIEW_CANCELLED"