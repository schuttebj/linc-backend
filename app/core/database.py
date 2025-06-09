"""
LINC Database Configuration
Single-country database setup with simplified connection management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import structlog
from contextlib import contextmanager

from app.core.config import settings

logger = structlog.get_logger()

# Metadata and Base for all models
metadata = MetaData()
Base = declarative_base(metadata=metadata)


def create_database_engine():
    """Create database engine with connection pooling"""
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before use
        echo=False  # Set to True for SQL debugging
    )
    
    logger.info(f"Created database engine for {settings.COUNTRY_NAME} ({settings.COUNTRY_CODE})")
    return engine


# Create single database engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_session() -> Generator[Session, None, None]:
    """
    Get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db_context() as db:
            # Use db session
            person = db.query(Person).first()
    """
    db_gen = get_database_session()
    db = next(db_gen)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


class DatabaseManager:
    """Database manager for single-country operations"""
    
    @staticmethod
    def create_all_tables():
        """Create all tables in the database"""
        Base.metadata.create_all(bind=engine)
        logger.info(f"Created tables for {settings.COUNTRY_NAME}")
    
    @staticmethod
    def drop_all_tables():
        """Drop all tables in the database (use with caution!)"""
        Base.metadata.drop_all(bind=engine)
        logger.warning(f"Dropped all tables for {settings.COUNTRY_NAME}")
    
    @staticmethod
    def test_connection() -> bool:
        """Test database connection"""
        try:
            with get_db_context() as db:
                db.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Dependency for FastAPI endpoints
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from get_database_session() 