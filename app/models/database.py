"""
Database initialization and utilities
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(
        self,
        db_url: str = "sqlite:///causelist_ocr.db",
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 40
    ):
        """Initialize database config.
        
        Args:
            db_url: Database URL (SQLite, PostgreSQL, MySQL)
            echo: Whether to log SQL statements
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        self.db_url = db_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self):
        """Initialize database engine and session factory."""
        # SQLite doesn't use pool parameters
        if self.db_url.startswith("sqlite:"):
            self.engine = create_engine(
                self.db_url,
                echo=self.echo,
                connect_args={"check_same_thread": False}
            )
        else:
            # PostgreSQL, MySQL, etc.
            self.engine = create_engine(
                self.db_url,
                echo=self.echo,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow
            )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Database initialized: {self.db_url}")
    
    def create_tables(self):
        """Create all tables in database."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables in database (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        if not self.SessionLocal:
            self.initialize()
        return self.SessionLocal()


# Global database configuration
db_config = DatabaseConfig()


def init_db(db_url: str = "sqlite:///causelist_ocr.db"):
    """Initialize database with default config.
    
    Args:
        db_url: Database URL
    """
    db_config.db_url = db_url
    db_config.initialize()
    db_config.create_tables()


def get_db() -> Session:
    """Get database session (for use in applications).
    
    Returns:
        Database session
    """
    return db_config.get_session()
