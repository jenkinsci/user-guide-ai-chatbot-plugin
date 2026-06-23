from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from manage_env import get_env
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = get_env("POSTGRES_URL")

db_engine = create_async_engine(POSTGRES_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=db_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_database_session():
    """
    Yields an active database session and ensures it is closed after the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
