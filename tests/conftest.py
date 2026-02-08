import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.main import app
from src.services.auth_service import hash_password

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/course_registration_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_student(db_session: AsyncSession):
    from src.models import Department, Student

    dept = Department(name="컴퓨터공학과")
    db_session.add(dept)
    await db_session.flush()

    student = Student(
        name="테스트학생",
        student_number="20240001",
        password_hash=hash_password("password"),
        year=1,
        department_id=dept.id,
    )
    db_session.add(student)
    await db_session.commit()
    return student


@pytest_asyncio.fixture
async def test_course(db_session: AsyncSession):
    from src.models import Course, CourseSchedule, Department, Professor

    dept = Department(name="컴퓨터공학과")
    db_session.add(dept)
    await db_session.flush()

    prof = Professor(name="김교수", employee_number="P0001", department_id=dept.id)
    db_session.add(prof)
    await db_session.flush()

    course = Course(
        name="자료구조",
        course_code="CS101",
        credits=3,
        capacity=30,
        enrolled=0,
        department_id=dept.id,
        professor_id=prof.id,
    )
    db_session.add(course)
    await db_session.flush()

    schedule = CourseSchedule(
        course_id=course.id,
        day_of_week="월",
        start_time="09:00",
        end_time="10:15",
    )
    db_session.add(schedule)
    await db_session.commit()
    return course


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_student):
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "20240001", "password": "password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
