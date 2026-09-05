from datetime import datetime, timedelta, timezone

from app.models.application import Application


def _create_job_and_app(recruiter_client, name="Alice", email="a@x.com"):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"})
    job_id = job.json()["id"]
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job_id, "candidate_name": name, "candidate_email": email}
    )
    return app_.json()["id"]


def _backdate(db_session, app_id, days_ago):
    app_row = db_session.get(Application, app_id)
    app_row.stage_entered_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db_session.commit()


def test_fresh_application_not_stalled(recruiter_client):
    _create_job_and_app(recruiter_client)
    alerts = recruiter_client.get("/alerts").json()
    assert alerts["count"] == 0


def test_stalled_application_appears_in_alerts(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 15)

    alerts = recruiter_client.get("/alerts").json()
    assert alerts["count"] == 1
    assert alerts["alerts"][0]["application_id"] == app_id
    assert alerts["alerts"][0]["days_in_stage"] >= 15


def test_9_days_not_yet_stalled(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 9)
    alerts = recruiter_client.get("/alerts").json()
    assert alerts["count"] == 0


def test_11_days_is_stalled(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 11)
    alerts = recruiter_client.get("/alerts").json()
    assert alerts["count"] == 1


def test_dismiss_removes_alert(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 15)
    assert recruiter_client.get("/alerts").json()["count"] == 1

    dismiss = recruiter_client.post(f"/alerts/{app_id}/dismiss")
    assert dismiss.status_code == 204

    assert recruiter_client.get("/alerts").json()["count"] == 0


def test_double_dismiss_is_idempotent(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 15)
    assert recruiter_client.post(f"/alerts/{app_id}/dismiss").status_code == 204
    assert recruiter_client.post(f"/alerts/{app_id}/dismiss").status_code == 204


def test_alert_reappears_after_stage_change_and_restall(recruiter_client, db_session):
    """
    The core requirement: dismissing an alert must only suppress that one
    stall episode. Advancing the candidate resets the clock; if they stall
    AGAIN in the new stage, a fresh alert must appear despite the earlier
    dismissal.
    """
    app_id = _create_job_and_app(recruiter_client)
    _backdate(db_session, app_id, 15)
    recruiter_client.post(f"/alerts/{app_id}/dismiss")
    assert recruiter_client.get("/alerts").json()["count"] == 0

    # Advance to a new stage - this resets stage_entered_at to "now"
    advance_resp = recruiter_client.post(f"/applications/{app_id}/advance", json={})
    assert advance_resp.json()["current_stage"] == "Screening"

    # Immediately after advancing, not stalled yet
    assert recruiter_client.get("/alerts").json()["count"] == 0

    # Backdate again to simulate stalling in the NEW stage
    _backdate(db_session, app_id, 12)

    alerts = recruiter_client.get("/alerts").json()
    assert alerts["count"] == 1
    assert alerts["alerts"][0]["current_stage"] == "Screening"


def test_hired_application_never_alerts_even_when_old(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    for _ in range(4):
        recruiter_client.post(f"/applications/{app_id}/advance", json={})  # -> Hired
    _backdate(db_session, app_id, 60)
    assert recruiter_client.get("/alerts").json()["count"] == 0


def test_rejected_application_never_alerts_even_when_old(recruiter_client, db_session):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    _backdate(db_session, app_id, 60)
    assert recruiter_client.get("/alerts").json()["count"] == 0


def test_interviewer_cannot_view_alerts(interviewer_client):
    resp = interviewer_client.get("/alerts")
    assert resp.status_code == 403


def test_interviewer_cannot_dismiss_alerts(interviewer_client):
    resp = interviewer_client.post("/alerts/1/dismiss")
    assert resp.status_code == 403
