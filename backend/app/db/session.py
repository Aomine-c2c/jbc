from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": 1800,
    })

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
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
