import asyncio
from sqlalchemy import select
from src.models.user_db import User
from src.config.database import get_postgres_db

async def main():
    async for session in get_postgres_db():
        query = select(User)
        result = await session.execute(query)
        users = result.scalars().all()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Mode: {user.mode}")
        break

if __name__ == "__main__":
    asyncio.run(main())
