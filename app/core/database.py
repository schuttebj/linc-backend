"""
LINC Database Configuration
Multi-tenant database setup with country-specific database separation
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Dict, Generator
import structlog
from contextlib import contextmanager

from app.core.config import settings

logger = structlog.get_logger()

# Database engines for each country (multi-tenant)
engines: Dict[str, any] = {}
SessionLocals: Dict[str, sessionmaker] = {}

# Metadata and Base for all models
metadata = MetaData()
Base = declarative_base(metadata=metadata)


def create_database_engine(database_url: str, country_code: str = None):
    """Create database engine with connection pooling"""
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before use
        echo=False  # Set to True for SQL debugging
    )
    
    if country_code:
        logger.info(f"Created database engine for country: {country_code}")
    else:
        logger.info("Created default database engine")
    
    return engine


def initialize_databases():
    """Initialize database engines for all supported countries"""
    global engines, SessionLocals
    
    # Create engines for each country
    for country_code in settings.SUPPORTED_COUNTRIES:
        database_url = settings.get_database_url(country_code)
        
        try:
            engine = create_database_engine(database_url, country_code)
            engines[country_code] = engine
            
            # Create session factory for this country
            SessionLocals[country_code] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            
            logger.info(f"Database initialized for country: {country_code}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database for {country_code}: {e}")
            raise
    
    # Create default engine
    default_engine = create_database_engine(settings.DATABASE_URL)
    engines["default"] = default_engine
    SessionLocals["default"] = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=default_engine
    )


def get_database_session(country_code: str = None) -> Generator[Session, None, None]:
    """
    Get database session for specific country
    
    Args:
        country_code: Country code to get session for (defaults to default country)
    
    Yields:
        Database session
    """
    if not country_code:
        country_code = settings.DEFAULT_COUNTRY_CODE
    
    country_code = country_code.upper()
    
    if country_code not in SessionLocals:
        logger.error(f"No database session available for country: {country_code}")
        # Fall back to default if country not found
        country_code = "default"
    
    SessionLocal = SessionLocals[country_code]
    db = SessionLocal()
    
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error for {country_code}: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context(country_code: str = None) -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db_context("ZA") as db:
            # Use db session
            person = db.query(Person).first()
    """
    db_gen = get_database_session(country_code)
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


def get_engine(country_code: str = None):
    """Get database engine for specific country"""
    if not country_code:
        country_code = settings.DEFAULT_COUNTRY_CODE
    
    country_code = country_code.upper()
    
    if country_code not in engines:
        logger.error(f"No database engine available for country: {country_code}")
        return engines.get("default")
    
    return engines[country_code]


class DatabaseManager:
    """Database manager for multi-tenant operations"""
    
    @staticmethod
    def create_tables_for_country(country_code: str):
        """Create all tables for a specific country database"""
        engine = get_engine(country_code)
        if engine:
            Base.metadata.create_all(bind=engine)
            logger.info(f"Created tables for country: {country_code}")
        else:
            logger.error(f"No engine found for country: {country_code}")
    
    @staticmethod
    def create_all_tables():
        """Create tables for all countries"""
        for country_code in settings.SUPPORTED_COUNTRIES:
            DatabaseManager.create_tables_for_country(country_code)
    
    @staticmethod
    def drop_tables_for_country(country_code: str):
        """Drop all tables for a specific country database (use with caution!)"""
        engine = get_engine(country_code)
        if engine:
            Base.metadata.drop_all(bind=engine)
            logger.warning(f"Dropped tables for country: {country_code}")
    
    @staticmethod
    def test_connection(country_code: str = None) -> bool:
        """Test database connection for a country"""
        try:
            with get_db_context(country_code) as db:
                db.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed for {country_code}: {e}")
            return False


# Initialize databases on module import
try:
    initialize_databases()
except Exception as e:
    logger.error(f"Failed to initialize databases: {e}")
    # In development, this might fail if PostgreSQL is not running
    # In production, this should be a critical error

# Default engine for Alembic and general use
engine = engines.get(settings.DEFAULT_COUNTRY_CODE, engines.get("default"))

# Default session maker
SessionLocal = SessionLocals.get(settings.DEFAULT_COUNTRY_CODE, SessionLocals.get("default"))


# Dependency for FastAPI endpoints
def get_db(country_code: str = None) -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    yield from get_database_session(country_code) 