from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = None
SessionLocal = None

def init_engine(dsn: str):
    global engine, SessionLocal
    engine = create_engine(dsn, echo=False, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine

def get_session():
    if SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_engine first.")
    return SessionLocal()
