def _create_job_and_app(recruiter_client, name="Alice", email="a@x.com"):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"})
    job_id = job.json()["id"]
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job_id, "candidate_name": name, "candidate_email": email}
    )
    return app_.json()["id"]


def test_bulk_advance_mixed_results_do_not_fail_whole_batch(recruiter_client):
    a = _create_job_and_app(recruiter_client, "A", "a@x.com")
    b = _create_job_and_app(recruiter_client, "B", "b@x.com")
    # Advance b all the way to Hired so it can't advance further
    for _ in range(4):
        recruiter_client.post(f"/applications/{b}/advance", json={})

    resp = recruiter_client.post("/applications/bulk/advance", json={"application_ids": [a, b, 999999]})
    assert resp.status_code == 200
    results = {r["application_id"]: r for r in resp.json()["results"]}

    assert results[a]["success"] is True
    assert results[a]["new_stage"] == "Screening"

    assert results[b]["success"] is False
    assert "Hired" in results[b]["reason"]

    assert results[999999]["success"] is False
    assert results[999999]["reason"] == "Application not found"


def test_bulk_reject(recruiter_client):
    a = _create_job_and_app(recruiter_client, "A", "a@x.com")
    b = _create_job_and_app(recruiter_client, "B", "b@x.com")
    resp = recruiter_client.post("/applications/bulk/reject", json={"application_ids": [a, b]})
    results = {r["application_id"]: r for r in resp.json()["results"]}
    assert results[a]["success"] is True
    assert results[a]["new_stage"] == "Rejected"
    assert results[b]["success"] is True


def test_bulk_advance_requires_recruiter(interviewer_client):
    resp = interviewer_client.post("/applications/bulk/advance", json={"application_ids": [1]})
    assert resp.status_code == 403


def test_csv_export_recruiter_only(recruiter_client, interviewer_client):
    assert recruiter_client.get("/applications/export").status_code == 200
    assert interviewer_client.get("/applications/export").status_code == 403


def test_csv_export_contains_expected_headers(recruiter_client):
    _create_job_and_app(recruiter_client)
    resp = recruiter_client.get("/applications/export")
    assert "Candidate Name" in resp.text
    assert "Current Stage" in resp.text
    assert "Alice" in resp.text


# --- History immutability ---


def test_history_created_on_application_creation(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    history = recruiter_client.get(f"/applications/{app_id}/history").json()
    assert len(history) == 1
    assert history[0]["event_type"] == "CREATED"


def test_history_grows_with_stage_changes(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    recruiter_client.post(f"/applications/{app_id}/advance", json={})
    recruiter_client.post(f"/applications/{app_id}/reject", json={"note": "test"})
    recruiter_client.post(f"/applications/{app_id}/reinstate", json={})

    history = recruiter_client.get(f"/applications/{app_id}/history").json()
    event_types = [h["event_type"] for h in history]
    assert event_types == ["CREATED", "STAGE_CHANGE", "REJECTED", "REINSTATED"]


def test_no_update_or_delete_route_exists_for_history(recruiter_client):
    app_id = _create_job_and_app(recruiter_client)
    history = recruiter_client.get(f"/applications/{app_id}/history").json()
    history_id = history[0]["id"]
    # There is deliberately no PATCH/DELETE /applications/{id}/history/{event_id}
    # route anywhere in the app - confirm the app-level route table has none.
    from app.main import app as fastapi_app

    history_mutation_routes = [
        r for r in fastapi_app.routes
        if "/history" in getattr(r, "path", "") and any(m in getattr(r, "methods", set()) for m in ("PATCH", "DELETE", "PUT"))
    ]
    assert history_mutation_routes == []
