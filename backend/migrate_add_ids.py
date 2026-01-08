"""
Database migration script to add identity columns to users table.
"""
import asyncio
from sqlalchemy import text
from src.config.database import engine

async def add_identity_columns():
    """Add employee_id, freelancer_id, and employment_type columns."""
    async with engine.begin() as conn:
        try:
            # List of columns to check/add
            columns = {
                'employment_type': 'VARCHAR(50)',
                'employee_id': 'VARCHAR(50)',
                'freelancer_id': 'VARCHAR(50)'
            }
            
            for col_name, col_type in columns.items():
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='{col_name}'
                """)
                result = await conn.execute(check_query)
                exists = result.fetchone()
                
                if exists:
                    print(f"✅ Column '{col_name}' already exists")
                else:
                    alter_query = text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    await conn.execute(alter_query)
                    print(f"✅ Added '{col_name}' column to users table")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("Running database migration...")
    asyncio.run(add_identity_columns())
    print("Migration complete!")
