import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

logger = logging.getLogger("dearly.database")

engine_kwargs = {
    "pool_pre_ping": True, # Test stale connections before executing queries
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling settings
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_connection() -> dict:
    """Verifies live database connectivity and returns dialect/version info."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;")).scalar()
            dialect = engine.dialect.name
            version_str = "unknown"
            if dialect == "postgresql":
                ver = conn.execute(text("SELECT version();")).fetchone()
                version_str = ver[0] if ver else "postgresql"
            elif dialect == "sqlite":
                ver = conn.execute(text("SELECT sqlite_version();")).fetchone()
                version_str = f"SQLite {ver[0]}" if ver else "sqlite"
            return {
                "connected": True,
                "dialect": dialect,
                "version": version_str
            }
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {
            "connected": False,
            "error": str(e)
        }
