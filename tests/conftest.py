from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool

from src.database import Base, get_db
from src.main import app
from src.services.auth_service import hash_password

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/course_registration_test"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    테스트 세션 동안 사용할 비동기 데이터베이스 엔진을 생성합니다.
    테스트 시작 전 테이블을 생성하고, 종료 후 리소스를 정리합니다.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # No connection pooling for tests
        future=True
    )

    # Create all tables once
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    각 테스트 함수마다 새로운 데이터베이스 세션을 생성합니다.
    테스트 종료 후 트랜잭션을 롤백하여 데이터 격리를 보장합니다.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    # Create session bound to this connection
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    # Rollback to undo all test changes
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_department(db_session: AsyncSession):
    """테스트용 학과 데이터를 생성하거나 조회합니다."""
    from src.models import Department
    from sqlalchemy import select

    # Check if department already exists (in case of parallel tests or reused DB)
    result = await db_session.execute(select(Department).where(Department.name == "컴퓨터공학과"))
    dept = result.scalar_one_or_none()

    if not dept:
        dept = Department(name="컴퓨터공학과")
        db_session.add(dept)
        await db_session.flush()
    
    return dept


@pytest_asyncio.fixture
async def test_student(db_session: AsyncSession, test_department):
    """테스트용 학생 데이터를 생성합니다."""
    from src.models import Student

    student = Student(
        name="테스트학생",
        student_number="20240001",
        password_hash=hash_password("password"),
        year=1,
        department_id=test_department.id,
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest_asyncio.fixture
async def test_course(db_session: AsyncSession, test_department):
    """테스트용 강좌(교수, 시간표 포함) 데이터를 생성합니다."""
    from src.models import Course, CourseSchedule, Professor

    prof = Professor(name="김교수", employee_number="P0001", department_id=test_department.id)
    db_session.add(prof)
    await db_session.flush()

    course = Course(
        name="자료구조",
        course_code="CS101",
        credits=3,
        capacity=30,
        enrolled=0,
        department_id=test_department.id,
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
    await db_session.flush()
    return course


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_student, db_session: AsyncSession):
    """테스트 학생으로 로그인하여 인증 헤더를 반환합니다."""
    # 로그인 요청은 별도의 세션을 사용하므로, 테스트 학생 데이터를 커밋해야 조회가 가능합니다.
    await db_session.commit()
    
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "20240001", "password": "password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
