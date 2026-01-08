"""Database configuration and connection management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from typing import AsyncGenerator

from src.config.settings import settings

def create_database_if_not_exists():
    """Create the database if it doesn't exist (sync operation for startup)."""
    target_db = settings._clean_postgres_db  # Use cleaned DB name from settings
    
    try:
        # Parse the sync URL to get connection details
        # The URL contains encoded credentials, make_url decodes them for us
        url = make_url(settings.sync_database_url)
        
        # Connect to PostgreSQL server (default 'postgres' database) to check/create target DB
        conn = psycopg2.connect(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists (parameterized query)
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database (use identifier quoting for safety)
            # Note: CREATE DATABASE doesn't support parameterization, so we validate the name
            if not target_db.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid database name: {target_db}")
            cursor.execute(f'CREATE DATABASE "{target_db}"')
            print(f"✅ Created database '{target_db}'")
        else:
            print(f"✅ Database '{target_db}' already exists")
        
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"❌ PostgreSQL password authentication failed!")
            print(f"Please check your .env file or DATABASE_URL.")
        else:
            print(f"❌ Error creating database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error creating database: {e}")
        return False


# SQLAlchemy Async Setup
# Use the centralized async URL from settings (which handles encoding and whitespace)
engine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_postgres_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_postgres_db():
    """Initialize PostgreSQL tables (async)."""
    target_db = settings._clean_postgres_db
    try:
        # Create database if it doesn't exist (sync operation)
        print(f"Checking if database '{target_db}' exists...")
        if not create_database_if_not_exists():
            print("Warning: Could not create database. Continuing anyway...")
        
        # Test connection first
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Import all models to ensure they're registered with Base
        from src.models import resume, jd_analysis, user_db, token_blacklist
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create indexes
        try:
            async with engine.begin() as conn:
                # Resume indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN (skills);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_uploaded_at ON resumes (uploaded_at DESC);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_source_type ON resumes (source_type);"))
                
                # JD Analysis indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_id ON jd_analysis (job_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_submitted_at ON jd_analysis (submitted_at DESC);"))
                
                # Match Results indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_job_id ON match_results (job_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_resume_id ON match_results (resume_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_score ON match_results (match_score DESC);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_source_type ON match_results (source_type);"))
                
                # User indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);"))
                
                # Token blacklist indexes
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_token_blacklist_token ON token_blacklist (token);"))
            print("PostgreSQL tables and indexes initialized")
        except Exception as e:
            print(f"PostgreSQL index initialization warning: {e}")
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"ERROR: PostgreSQL password authentication failed!")
            print(f"Please check your .env file or DATABASE_URL")
        elif "does not exist" in error_msg.lower() and "database" in error_msg.lower():
            print(f"ERROR: Database '{target_db}' does not exist!")
            print(f"Attempting to create database...")
            # Try to create database again
            if create_database_if_not_exists():
                print(f"Database created successfully. Please restart the backend.")
            else:
                print(f"Failed to create database. Please create it manually.")
        else:
            print(f"Error connecting to PostgreSQL: {e}")
        # Don't raise - allow app to start without PostgreSQL for now
        print("Warning: Continuing without PostgreSQL connection. Some features may not work.")
