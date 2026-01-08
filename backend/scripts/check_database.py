"""
Database Connection and Schema Verification Script
This script checks database connection and ensures all tables are created
"""
import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config.database import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    engine, Base, init_postgres_db
)
from sqlalchemy import text, inspect
from models import resume, jd_analysis, user_db, token_blacklist

async def check_connection():
    """Test database connection"""
    print("=" * 60)
    print("DATABASE CONNECTION CHECK")
    print("=" * 60)
    print(f"Host: {POSTGRES_HOST}")
    print(f"Port: {POSTGRES_PORT}")
    print(f"Database: {POSTGRES_DB}")
    print(f"User: {POSTGRES_USER}")
    print(f"Password: {'*' * len(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else 'NOT SET'}")
    print()
    
    # First, try to create database if it doesn't exist
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
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
            print(f"[OK] Created database '{POSTGRES_DB}'")
        else:
            print(f"[OK] Database '{POSTGRES_DB}' already exists")
        
        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Cannot connect to PostgreSQL server!")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. If using Docker: docker-compose up -d postgres")
        print("3. Check .env file has correct credentials")
        return False
    except Exception as e:
        print(f"[WARNING] Could not create database: {e}")
    
    # Now test async connection
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"[OK] Database connection successful!")
            print(f"   PostgreSQL version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed!")
        print(f"   Error: {e}")
        return False

async def check_database_exists():
    """Check if database exists"""
    print("\n" + "=" * 60)
    print("DATABASE EXISTENCE CHECK")
    print("=" * 60)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
            )
            exists = result.scalar()
            if exists:
                print(f"[OK] Database '{POSTGRES_DB}' exists")
                return True
            else:
                print(f"[WARNING] Database '{POSTGRES_DB}' does not exist (will be created)")
                return False
    except Exception as e:
        print(f"[ERROR] Error checking database: {e}")
        return False

async def check_tables():
    """Check if all required tables exist"""
    print("\n" + "=" * 60)
    print("TABLE EXISTENCE CHECK")
    print("=" * 60)
    
    required_tables = [
        'users',
        'resumes',
        'jd_analysis',
        'match_results',
        'token_blacklist'
    ]
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            existing_tables = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(existing_tables)} tables in database:")
            for table in existing_tables:
                print(f"  - {table}")
            
            print("\nRequired tables:")
            missing_tables = []
            for table in required_tables:
                if table in existing_tables:
                    print(f"  [OK] {table}")
                else:
                    print(f"  [MISSING] {table}")
                    missing_tables.append(table)
            
            return len(missing_tables) == 0, missing_tables
    except Exception as e:
        print(f"[ERROR] Error checking tables: {e}")
        return False, required_tables

async def check_indexes():
    """Check if indexes exist"""
    print("\n" + "=" * 60)
    print("INDEX CHECK")
    print("=" * 60)
    
    required_indexes = [
        'idx_resumes_skills',
        'idx_resumes_uploaded_at',
        'idx_resumes_source_type',
        'idx_match_results_job_id',
        'idx_match_results_score',
        'idx_users_email',
        'idx_token_blacklist_token'
    ]
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY indexname;
            """))
            existing_indexes = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(existing_indexes)} indexes")
            for idx in existing_indexes:
                if any(req_idx in idx for req_idx in required_indexes):
                    print(f"  [OK] {idx}")
            
            missing_indexes = []
            for idx in required_indexes:
                if idx in existing_indexes:
                    print(f"  [OK] {idx}")
                else:
                    print(f"  [WILL CREATE] {idx}")
                    missing_indexes.append(idx)
            
            return len(missing_indexes) == 0
    except Exception as e:
        print(f"[ERROR] Error checking indexes: {e}")
        return False

async def build_schema():
    """Build database schema"""
    print("\n" + "=" * 60)
    print("BUILDING DATABASE SCHEMA")
    print("=" * 60)
    
    try:
        # Initialize database (creates tables and indexes)
        await init_postgres_db()
        print("[OK] Schema initialization completed!")
        return True
    except Exception as e:
        print(f"[ERROR] Error building schema: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("TECHBANK.AI DATABASE SETUP & VERIFICATION")
    print("=" * 60)
    print()
    
    # Step 1: Check connection (this also creates database if needed)
    if not await check_connection():
        print("\n[ERROR] Cannot proceed - database connection failed!")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running:")
        print("   - If using Docker: docker-compose up -d postgres")
        print("   - If using local PostgreSQL: Start PostgreSQL service")
        print("2. Check .env file has correct credentials")
        print("3. Verify PostgreSQL is accessible on localhost:5432")
        return False
    
    # Step 2: Check database exists
    if not await check_database_exists():
        print("\n[WARNING] Database does not exist. It will be created automatically.")
    
    # Step 3: Build schema
    print("\n" + "=" * 60)
    print("INITIALIZING SCHEMA")
    print("=" * 60)
    schema_built = await build_schema()
    
    if not schema_built:
        print("\n❌ Schema build failed!")
        return False
    
    # Step 4: Verify tables
    all_tables_exist, missing = await check_tables()
    
    # Step 5: Check indexes
    all_indexes_exist = await check_indexes()
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if all_tables_exist and all_indexes_exist:
        print("[OK] Database is fully configured and ready!")
        print("\nYou can now start the backend server:")
        print("  python app.py")
    else:
        if missing:
            print(f"[WARNING] Missing tables: {', '.join(missing)}")
        if not all_indexes_exist:
            print("[WARNING] Some indexes may need to be created")
        print("\nRun this script again to ensure all tables are created.")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

