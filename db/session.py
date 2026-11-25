from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from db.models import Base

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_session():
    return SessionLocal()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
