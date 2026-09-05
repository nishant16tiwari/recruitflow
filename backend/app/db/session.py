from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a DB session per-request and always
    closes it, even if the request raises an exception. This prevents
    connection leaks under load.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
