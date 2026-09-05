import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.core.security import hash_password
from app.models.user import User

# WHY a separate database rather than reusing the dev DB: tests wipe all
# data before every test for isolation. Pointing that at the same database
# used for manual dev/demo work would destroy the seeded demo data every
# time the suite runs.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg2://recruitflow:recruitflow@localhost:5432/recruitflow_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """
    Runs before every single test: truncates every table so each test
    starts from a genuinely empty database. WHY truncate rather than the
    more common "wrap each test in a rolled-back transaction" pattern:
    our service layer calls db.commit() directly (not just flush()) in
    several places, which would break a naive outer-transaction-rollback
    setup unless every session in the app were rebound to a SAVEPOINT-aware
    factory. Truncating is slightly slower but works correctly with the
    application code exactly as written, with zero special-casing.
    """
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    yield


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = TestSessionLocal()
    yield db
    db.close()


def _make_user(db_session, email, name, role, password="testpass123"):
    user = User(email=email, name=name, role=role, password_hash=hash_password(password))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def recruiter(db_session):
    return _make_user(db_session, "recruiter@test.com", "Test Recruiter", UserRole.RECRUITER)


@pytest.fixture
def recruiter2(db_session):
    return _make_user(db_session, "recruiter2@test.com", "Second Recruiter", UserRole.RECRUITER)


@pytest.fixture
def interviewer(db_session):
    return _make_user(db_session, "interviewer@test.com", "Test Interviewer", UserRole.INTERVIEWER)


@pytest.fixture
def interviewer2(db_session):
    return _make_user(db_session, "interviewer2@test.com", "Second Interviewer", UserRole.INTERVIEWER)


def login(client, email, password="testpass123"):
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return client


@pytest.fixture
def recruiter_client(recruiter):
    """
    A fresh TestClient per role - NOT sharing the `client` fixture -
    because TestClient keeps a cookie jar, and if a test needs both a
    recruiter_client and an interviewer_client simultaneously (as the
    cross-role authorization tests below do), sharing one instance would
    mean the second login's cookie silently overwrites the first.
    """
    with TestClient(app) as c:
        yield login(c, recruiter.email)


@pytest.fixture
def interviewer_client(interviewer):
    with TestClient(app) as c:
        yield login(c, interviewer.email)
