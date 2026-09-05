def test_dashboard_requires_recruiter(interviewer_client):
    assert interviewer_client.get("/dashboard").status_code == 403


def test_open_positions_count(recruiter_client):
    recruiter_client.post("/jobs", json={"title": "A", "department": "Eng"})
    recruiter_client.post("/jobs", json={"title": "B", "department": "Eng"})
    archived = recruiter_client.post("/jobs", json={"title": "C", "department": "Eng"}).json()
    recruiter_client.post(f"/jobs/{archived['id']}/archive")

    data = recruiter_client.get("/dashboard").json()
    assert data["open_positions"] == 2


def test_active_applications_excludes_hired_and_rejected(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "A", "department": "Eng"}).json()

    recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Active", "candidate_email": "act@x.com"}
    ).json()

    hired_app = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Hired", "candidate_email": "hir@x.com"}
    ).json()
    for _ in range(4):
        recruiter_client.post(f"/applications/{hired_app['id']}/advance", json={})

    rejected_app = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Rejected", "candidate_email": "rej@x.com"}
    ).json()
    recruiter_client.post(f"/applications/{rejected_app['id']}/reject", json={})

    data = recruiter_client.get("/dashboard").json()
    assert data["active_applications"] == 1


def test_hires_this_month_from_history_not_current_state(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "A", "department": "Eng"}).json()
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Hired", "candidate_email": "h@x.com"}
    ).json()
    for _ in range(4):
        recruiter_client.post(f"/applications/{app_['id']}/advance", json={})

    data = recruiter_client.get("/dashboard").json()
    assert data["hires_this_month"] == 1


def test_by_stage_breakdown_includes_rejected(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "A", "department": "Eng"}).json()
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "R", "candidate_email": "r@x.com"}
    ).json()
    recruiter_client.post(f"/applications/{app_['id']}/reject", json={})

    data = recruiter_client.get("/dashboard").json()
    stage_names = [s["stage"] for s in data["by_stage"]]
    assert "Rejected" in stage_names
    rejected_entry = next(s for s in data["by_stage"] if s["stage"] == "Rejected")
    assert rejected_entry["count"] == 1


def test_weekly_applications_zero_filled(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "A", "department": "Eng"}).json()
    recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "X", "candidate_email": "x@x.com"}
    )
    data = recruiter_client.get("/dashboard").json()
    assert len(data["weekly_applications"]) == 13
    assert sum(w["count"] for w in data["weekly_applications"]) == 1
