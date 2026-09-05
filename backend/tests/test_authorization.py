def _create_job(recruiter_client):
    resp = recruiter_client.post(
        "/jobs", json={"title": "Engineer", "department": "Engineering", "description": "desc"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_application(recruiter_client, job_id, name="Alice", email="alice@x.com"):
    resp = recruiter_client.post(
        "/applications", json={"job_id": job_id, "candidate_name": name, "candidate_email": email}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_recruiter_can_create_job(recruiter_client):
    resp = recruiter_client.post("/jobs", json={"title": "X", "department": "Y", "description": ""})
    assert resp.status_code == 201


def test_interviewer_cannot_create_job(interviewer_client):
    resp = interviewer_client.post("/jobs", json={"title": "X", "department": "Y"})
    assert resp.status_code == 403


def test_interviewer_cannot_advance_stage(recruiter_client, interviewer_client):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    resp = interviewer_client.post(f"/applications/{app_id}/advance", json={})
    assert resp.status_code == 403


def test_interviewer_cannot_reject(recruiter_client, interviewer_client):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    resp = interviewer_client.post(f"/applications/{app_id}/reject", json={})
    assert resp.status_code == 403


def test_interviewer_cannot_access_unrelated_application(recruiter_client, interviewer_client):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    # interviewer was never assigned to this application's panel
    resp = interviewer_client.get(f"/applications/{app_id}")
    assert resp.status_code == 403


def test_interviewer_can_access_assigned_application(recruiter_client, interviewer_client, interviewer):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    assign = recruiter_client.post(
        f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id}
    )
    assert assign.status_code == 201
    resp = interviewer_client.get(f"/applications/{app_id}")
    assert resp.status_code == 200


def test_recruiter_cannot_be_assigned_as_interviewer(recruiter_client, recruiter2):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    resp = recruiter_client.post(
        f"/applications/{app_id}/interviewers", json={"interviewer_id": recruiter2.id}
    )
    assert resp.status_code == 400


def test_unassigned_interviewer_cannot_submit_feedback(recruiter_client, interviewer_client):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    resp = interviewer_client.post(f"/applications/{app_id}/feedback", json={"content": "sneaky"})
    assert resp.status_code == 403


def test_recruiter_cannot_submit_feedback(recruiter_client, interviewer_client, interviewer):
    job_id = _create_job(recruiter_client)
    app_id = _create_application(recruiter_client, job_id)
    recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    resp = recruiter_client.post(f"/applications/{app_id}/feedback", json={"content": "trying"})
    assert resp.status_code == 403


def test_no_auth_cookie_rejected(client):
    resp = client.get("/applications/1")
    assert resp.status_code == 401
