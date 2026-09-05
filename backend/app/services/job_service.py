from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.enums import JobStatus
from app.models.job_opening import JobOpening
from app.schemas.job import JobCreate, JobUpdate


def create_job(db: Session, data: JobCreate, created_by: int) -> JobOpening:
    job = JobOpening(
        title=data.title,
        department=data.department,
        description=data.description,
        status=JobStatus.OPEN,
        created_by=created_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_or_404(db: Session, job_id: int) -> JobOpening:
    job = db.get(JobOpening, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job opening not found")
    return job


def list_jobs(db: Session, include_archived: bool) -> list[JobOpening]:
    query = db.query(JobOpening)
    if not include_archived:
        query = query.filter(JobOpening.status == JobStatus.OPEN)
    return query.order_by(JobOpening.created_at.desc()).all()


def list_jobs_with_counts(db: Session, include_archived: bool) -> list[tuple[JobOpening, int]]:
    """
    Returns (job, application_count) pairs in one query rather than N+1
    queries (one count query per job in a loop), which matters once there
    are dozens of job openings on the list page.
    """
    query = (
        db.query(JobOpening, func.count(Application.id))
        .outerjoin(Application, Application.job_id == JobOpening.id)
        .group_by(JobOpening.id)
    )
    if not include_archived:
        query = query.filter(JobOpening.status == JobStatus.OPEN)
    return query.order_by(JobOpening.created_at.desc()).all()


def update_job(db: Session, job: JobOpening, data: JobUpdate) -> JobOpening:
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


def archive_job(db: Session, job: JobOpening) -> JobOpening:
    """
    WHY archiving never touches applications: the spec is explicit that
    archiving must not delete or hide applications from the database -
    it only removes the JOB from default active views. Applications keep
    their job_id pointing at the (now archived) job unchanged.
    """
    if job.status == JobStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already archived")
    job.status = JobStatus.ARCHIVED
    db.commit()
    db.refresh(job)
    return job


def restore_job(db: Session, job: JobOpening) -> JobOpening:
    if job.status == JobStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is already open")
    job.status = JobStatus.OPEN
    db.commit()
    db.refresh(job)
    return job
