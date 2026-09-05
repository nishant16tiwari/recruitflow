def _create_job_and_app(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"})
    job_id = job.json()["id"]
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job_id, "candidate_name": "Alice", "candidate_email": "a@x.com"}
    )
    return app_.json()["id"]


def test_valid_full_pipeline_walkthrough(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)

    for expected_new_stage in ["Screening", "Interview", "Offer", "Hired"]:
        resp = recruiter_client.post(f"/applications/{app_id}/advance", json={})
        assert resp.status_code == 200, resp.text
        assert resp.json()["current_stage"] == expected_new_stage

    # Hired cannot advance further
    resp = recruiter_client.post(f"/applications/{app_id}/advance", json={})
    assert resp.status_code == 400


def test_invalid_jump_applied_to_interview(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    resp = recruiter_client.post(f"/applications/{app_id}/advance", json={"to_stage": "Interview"})
    assert resp.status_code == 400
    assert "Screening" in resp.json()["detail"]


def test_invalid_jump_applied_to_offer(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    resp = recruiter_client.post(f"/applications/{app_id}/advance", json={"to_stage": "Offer"})
    assert resp.status_code == 400


def test_invalid_jump_screening_to_hired(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/advance", json={})  # -> Screening
    resp = recruiter_client.post(f"/applications/{app_id}/advance", json={"to_stage": "Hired"})
    assert resp.status_code == 400


def test_rejection_from_every_stage(recruiter_client):
    stages_to_reach = [0, 1, 2, 3]  # Applied, Screening, Interview, Offer
    for n in stages_to_reach:
        app_id = _create_job_and_app(recruiter_client)
        for _ in range(n):
            recruiter_client.post(f"/applications/{app_id}/advance", json={})
        resp = recruiter_client.post(f"/applications/{app_id}/reject", json={"note": "no"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["current_stage"] == "Rejected"


def test_hired_cannot_be_rejected(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    for _ in range(4):
        recruiter_client.post(f"/applications/{app_id}/advance", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/reject", json={})
    assert resp.status_code == 400


def test_already_rejected_cannot_be_rejected_again(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/reject", json={})
    assert resp.status_code == 400


def test_reinstate_from_screening_returns_to_screening(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/advance", json={})  # -> Screening
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/reinstate", json={})
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "Screening"


def test_reinstate_from_interview_returns_to_interview_not_applied(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/advance", json={})  # Screening
    recruiter_client.post(f"/applications/{app_id}/advance", json={})  # Interview
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/reinstate", json={})
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "Interview"


def test_reinstate_from_offer_returns_to_offer(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    for _ in range(3):
        recruiter_client.post(f"/applications/{app_id}/advance", json={})  # -> Offer
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/reinstate", json={})
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "Offer"


def test_cannot_reinstate_non_rejected_application(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    resp = recruiter_client.post(f"/applications/{app_id}/reinstate", json={})
    assert resp.status_code == 400


def test_cannot_advance_rejected_application(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/reject", json={})
    resp = recruiter_client.post(f"/applications/{app_id}/advance", json={})
    assert resp.status_code == 400
