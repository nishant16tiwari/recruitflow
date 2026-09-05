def test_list_interviewers_recruiter_only(recruiter_client, interviewer_client, interviewer):
    resp = recruiter_client.get("/users/interviewers")
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert interviewer.email in emails

    assert interviewer_client.get("/users/interviewers").status_code == 403
