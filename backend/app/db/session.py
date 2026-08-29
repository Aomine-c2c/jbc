from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

SessionLocal = async_session_factory

async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

class Base(DeclarativeBase):
    pass
