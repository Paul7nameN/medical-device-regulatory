import uuid
from datetime import datetime
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.dialects.postgresql import UUID

from app.config import settings


sync_engine = create_engine(settings.database_url, echo=settings.debug)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

async_engine = create_async_engine(settings.database_url_async, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


class Base(DeclarativeBase):
    pass


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=text("TIMEZONE('utc', NOW())"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=text("TIMEZONE('utc', NOW())"),
        onupdate=datetime.utcnow,
        server_onupdate=text("TIMEZONE('utc', NOW())"),
    )


def get_db() -> Generator[SyncSessionLocal, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
