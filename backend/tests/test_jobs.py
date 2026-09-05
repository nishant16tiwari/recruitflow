def test_create_job(recruiter_client):
    resp = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Engineering"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "OPEN"


def test_archive_hides_from_default_list_but_keeps_applications(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"}).json()
    app_ = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Alice", "candidate_email": "a@x.com"}
    ).json()

    recruiter_client.post(f"/jobs/{job['id']}/archive")

    default_list = recruiter_client.get("/jobs").json()
    assert job["id"] not in [j["id"] for j in default_list]

    full_list = recruiter_client.get("/jobs?include_archived=true").json()
    assert job["id"] in [j["id"] for j in full_list]

    # The critical rule: application must still exist and be fully readable
    still_there = recruiter_client.get(f"/applications/{app_['id']}")
    assert still_there.status_code == 200
    assert still_there.json()["id"] == app_["id"]


def test_cannot_create_application_on_archived_job(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"}).json()
    recruiter_client.post(f"/jobs/{job['id']}/archive")
    resp = recruiter_client.post(
        "/applications", json={"job_id": job["id"], "candidate_name": "Bob", "candidate_email": "b@x.com"}
    )
    assert resp.status_code == 400


def test_restore_makes_job_open_again(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"}).json()
    recruiter_client.post(f"/jobs/{job['id']}/archive")
    resp = recruiter_client.post(f"/jobs/{job['id']}/restore")
    assert resp.json()["status"] == "OPEN"
