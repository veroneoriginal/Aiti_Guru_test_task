# app/infrastructure/db/session.py

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # True — выводит SQL в консоль
    pool_pre_ping=True,  # проверяет соединение перед использованием
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты остаются доступны после commit()
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимости для FastAPI.
    Открывает сессию, отдаёт её в роутер, закрывает после ответа.
    """
    async with AsyncSessionFactory() as session:
        yield session
