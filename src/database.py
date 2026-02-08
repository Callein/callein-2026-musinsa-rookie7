from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """
    비동기 데이터베이스 세션을 생성하여 반환하는 의존성 함수입니다.

    Yields:
        AsyncSession: SQLAlchemy 비동기 세션
    """

    async with async_session() as session:
        yield session
