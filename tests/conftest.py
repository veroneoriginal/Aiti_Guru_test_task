# tests/conftest.py
import uuid
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base, OrderStatus
from app.models.order import Order

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)

TestSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session():
    async with TestSessionFactory() as s:
        yield s


# pylint: disable=redefined-outer-name
@pytest_asyncio.fixture
async def order(session: AsyncSession) -> Order:
    o = Order(
        id=uuid.uuid4(),
        amount=Decimal("1000.00"),
        status=OrderStatus.UNPAID,
    )
    session.add(o)
    await session.commit()
    await session.refresh(o)
    return o
