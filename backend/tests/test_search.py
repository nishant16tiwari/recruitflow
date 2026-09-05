def _setup(recruiter_client):
    job = recruiter_client.post("/jobs", json={"title": "Eng", "department": "Eng"})
    job_id = job.json()["id"]
    for name, email in [("Alice Adams", "alice@x.com"), ("Bob Baker", "bob@x.com"), ("Cara Cole", "cara@x.com")]:
        recruiter_client.post(
            "/applications", json={"job_id": job_id, "candidate_name": name, "candidate_email": email}
        )
    return job_id


def test_search_by_name(recruiter_client):
    _setup(recruiter_client)
    resp = recruiter_client.get("/applications?search=Alice")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["candidate_name"] == "Alice Adams"


def test_search_by_email(recruiter_client):
    _setup(recruiter_client)
    resp = recruiter_client.get("/applications?search=bob@x.com")
    assert resp.json()["total"] == 1


def test_search_no_match(recruiter_client):
    _setup(recruiter_client)
    resp = recruiter_client.get("/applications?search=Zzzz")
    assert resp.json()["total"] == 0


def test_pagination_math(recruiter_client):
    _setup(recruiter_client)
    resp = recruiter_client.get("/applications?page=1&page_size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2


def test_filter_by_stage(recruiter_client):
    job_id = _setup(recruiter_client)
    all_apps = recruiter_client.get("/applications?page_size=100").json()["items"]
    recruiter_client.post(f"/applications/{all_apps[0]['id']}/advance", json={})

    resp = recruiter_client.get("/applications?stage=Screening")
    assert resp.json()["total"] == 1

    resp = recruiter_client.get("/applications?stage=Applied")
    assert resp.json()["total"] == 2


def test_interviewer_search_scoped_to_assigned(recruiter_client, interviewer_client, interviewer):
    job_id = _setup(recruiter_client)
    all_apps = recruiter_client.get("/applications?page_size=100").json()["items"]
    recruiter_client.post(
        f"/applications/{all_apps[0]['id']}/interviewers", json={"interviewer_id": interviewer.id}
    )

    resp = interviewer_client.get("/applications")
    assert resp.json()["total"] == 1
