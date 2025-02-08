from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Create SQLite engine
engine = create_engine("sqlite:///./policypal.db")

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
