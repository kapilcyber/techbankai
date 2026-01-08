from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "techbank")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

def create_database_if_not_exists():
    """Create the database if it doesn't exist (sync operation for startup)"""
    try:
        # Connect to PostgreSQL server (without specifying database)
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database="postgres"  # Connect to default 'postgres' database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f'CREATE DATABASE "{POSTGRES_DB}"')
            print(f"✅ Created database '{POSTGRES_DB}'")
        else:
            print(f"✅ Database '{POSTGRES_DB}' already exists")
        
        cursor.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"❌ PostgreSQL password authentication failed!")
            print(f"Please check your .env file - POSTGRES_PASSWORD should match your PostgreSQL password")
            print(f"Current connection: postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}")
        else:
            print(f"❌ Error creating database: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error creating database: {e}")
        return False

# Async PostgreSQL URL (using asyncpg driver)
POSTGRES_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy Async Setup
engine = create_async_engine(
    POSTGRES_URL,
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
    """Async database session dependency"""
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
    """Initialize PostgreSQL tables (async)"""
    try:
        # Create database if it doesn't exist (sync operation)
        print(f"Checking if database '{POSTGRES_DB}' exists...")
        if not create_database_if_not_exists():
            print("Warning: Could not create database. Continuing anyway...")
        
        # Test connection first
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Import all models to ensure they're registered with Base
        from models import resume, jd_analysis, user_db, token_blacklist
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create indexes
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN (skills);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_uploaded_at ON resumes (uploaded_at DESC);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_resumes_source_type ON resumes (source_type);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_job_id ON match_results (job_id);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_score ON match_results (match_score DESC);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_token_blacklist_token ON token_blacklist (token);"))
            print("PostgreSQL tables and indexes initialized")
        except Exception as e:
            print(f"PostgreSQL index initialization warning: {e}")
    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            print(f"ERROR: PostgreSQL password authentication failed!")
            print(f"Please check your .env file - POSTGRES_PASSWORD should match your PostgreSQL password")
            print(f"Current connection: postgresql+asyncpg://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
            print(f"\nTo fix:")
            print(f"1. If using Docker: POSTGRES_PASSWORD=postgres")
            print(f"2. If using local PostgreSQL: Use your actual PostgreSQL password")
            print(f"3. Update backend/.env file")
        elif "does not exist" in error_msg.lower() and "database" in error_msg.lower():
            print(f"ERROR: Database '{POSTGRES_DB}' does not exist!")
            print(f"Attempting to create database...")
            # Try to create database again
            if create_database_if_not_exists():
                print(f"Database created successfully. Please restart the backend.")
            else:
                print(f"Failed to create database. Please create it manually:")
                print(f"  psql -U postgres -c 'CREATE DATABASE {POSTGRES_DB};'")
        else:
            print(f"Error connecting to PostgreSQL: {e}")
        # Don't raise - allow app to start without PostgreSQL for now
        print("Warning: Continuing without PostgreSQL connection. Some features may not work.")
