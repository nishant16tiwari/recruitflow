def _create_job_and_app(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"})
    job_id = job.json()["id"]
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job_id, "candidate_name": "Alice", "candidate_email": "a@x.com"}
    )
    return app_.json()["id"]


def test_assign_valid_interviewer(recruiter_client, interviewer):
    app_id = _create_job_and_app(recruiter_client)
    resp = recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    assert resp.status_code == 201


def test_cannot_assign_duplicate(recruiter_client, interviewer):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    resp = recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    assert resp.status_code == 400


def test_removed_interviewer_loses_access_immediately(recruiter_client, interviewer_client, interviewer):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    assert interviewer_client.get(f"/applications/{app_id}").status_code == 200

    remove = recruiter_client.delete(f"/applications/{app_id}/interviewers/{interviewer.id}")
    assert remove.status_code == 204

    assert interviewer_client.get(f"/applications/{app_id}").status_code == 403


def test_assigned_interviewer_can_submit_feedback(recruiter_client, interviewer_client, interviewer):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})
    resp = interviewer_client.post(f"/applications/{app_id}/feedback", json={"content": "Great candidate"})
    assert resp.status_code == 201


def test_my_applications_scoped_correctly(recruiter_client, interviewer_client, interviewer, interviewer2):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/interviewers", json={"interviewer_id": interviewer.id})

    mine = interviewer_client.get("/applications/my").json()
    assert len(mine) == 1
    assert mine[0]["id"] == app_id


def test_my_applications_empty_for_unassigned_interviewer(recruiter_client, interviewer_client, interviewer2):
    _create_job_and_app(recruiter_client)  # created but interviewer2 never assigned
    mine = interviewer_client.get("/applications/my").json()
    assert mine == []
