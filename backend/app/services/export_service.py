import csv
import io

from sqlalchemy.orm import Session, joinedload

from app.models.application import Application
from app.models.enums import JobStatus

CSV_HEADERS = [
    "Candidate Name",
    "Candidate Email",
    "Job Opening",
    "Source",
    "Applied Date",
    "Current Stage",
]


def generate_pipeline_csv(db: Session) -> str:
    """
    WHY "every OPEN application" is interpreted as "applications under a
    job opening whose status is OPEN" (documented ambiguity resolution,
    also noted in the README): this is the "Export Pipeline CSV" action
    sitting right next to the active/default applications view, which
    itself only shows non-archived jobs by default. Reading "open" as
    "job is open" keeps the export consistent with what a recruiter is
    actually looking at when they click the button, rather than filtering
    by the application's OWN stage (which already has its own Rejected/
    Hired states with different meanings).
    """
    applications = (
        db.query(Application)
        .join(Application.job)
        .filter(Application.job.has(status=JobStatus.OPEN))
        .options(joinedload(Application.job))
        .order_by(Application.job_id, Application.created_at)
        .all()
    )

    buffer = io.StringIO()
    # WHY csv.writer instead of manual string joining: it handles quoting
    # and escaping (commas, quotes, newlines inside candidate names/notes)
    # correctly per RFC 4180, which manual string concatenation would get
    # wrong the moment a candidate's name contains a comma.
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)

    for app_ in applications:
        writer.writerow(
            [
                app_.candidate_name,
                app_.candidate_email,
                app_.job.title,
                app_.source,
                app_.applied_date.isoformat(),
                app_.current_stage.value,
            ]
        )

    return buffer.getvalue()
