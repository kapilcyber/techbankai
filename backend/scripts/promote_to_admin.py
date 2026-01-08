import asyncio
import sys
from sqlalchemy import select
from src.models.user_db import User
from src.config.database import get_postgres_db

async def promote(email):
    async for session in get_postgres_db():
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.mode = "admin"
            await session.commit()
            print(f"Successfully promoted {email} to admin.")
        else:
            print(f"User {email} not found.")
        break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_to_admin.py <email>")
    else:
        asyncio.run(promote(sys.argv[1]))
