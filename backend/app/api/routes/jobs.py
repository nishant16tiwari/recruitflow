from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_recruiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import ApplicationRead
from app.schemas.job import JobCreate, JobRead, JobReadWithCount, JobUpdate
from app.services import application_service, job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobReadWithCount])
def list_jobs(
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    rows = job_service.list_jobs_with_counts(db, include_archived)
    return [
        JobReadWithCount(**JobRead.model_validate(job).model_dump(), application_count=count)
        for job, count in rows
    ]


@router.post("", response_model=JobRead, status_code=201)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    return job_service.create_job(db, data, created_by=current_user.id)


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    return job_service.get_job_or_404(db, job_id)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    job = job_service.get_job_or_404(db, job_id)
    return job_service.update_job(db, job, data)


@router.post("/{job_id}/archive", response_model=JobRead)
def archive_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    job = job_service.get_job_or_404(db, job_id)
    return job_service.archive_job(db, job)


@router.post("/{job_id}/restore", response_model=JobRead)
def restore_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    job = job_service.get_job_or_404(db, job_id)
    return job_service.restore_job(db, job)


@router.get("/{job_id}/applications", response_model=list[ApplicationRead])
def list_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_recruiter),
):
    job_service.get_job_or_404(db, job_id)  # 404 if the job itself doesn't exist
    return application_service.list_applications_for_job(db, job_id)
