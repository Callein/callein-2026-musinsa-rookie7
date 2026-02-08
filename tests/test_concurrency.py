import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.database import get_db
from src.models import Course, Student, Enrollment, Department, Professor
from src.services.auth_service import hash_password

@pytest.mark.asyncio
async def test_enrollment_concurrency(
    test_engine, test_course, test_student, test_department
):
    """
    Test 100 concurrent enrollment requests for a course with capacity 1.
    Only 1 should succeed, 99 should fail.
    """
    
    # 1. Setup: Create 100 students and get their tokens
    password = "password"
    hashed = hash_password(password)
    
    students = []
    tokens = []
    
    # 별도의 세션을 사용하여 테스트 데이터를 생성을 확실하게 커밋합니다.
    # (다른 세션에서 조회 가능하도록)
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        # Create Dept (if not check) - relying on unique constraint might fail if parallel.
        # Just create a new unique dept for this test to be safe.
        dept = Department(name="ConcurrencyDept")
        session.add(dept)
        await session.flush()
        
        prof = Professor(name="ConProf", employee_number="CP01", department_id=dept.id)
        session.add(prof)
        await session.flush()
        
        target_course = Course(
            name="HotCourse",
            course_code="HOT001",
            credits=3,
            capacity=1, # Key: Capacity 1
            enrolled=0,
            department_id=dept.id,
            professor_id=prof.id
        )
        session.add(target_course)
        await session.flush()
        
        # Create 100 students
        created_students = []
        for i in range(100):
            s = Student(
                name=f"ConUser{i}",
                student_number=f"9999{i:04d}",
                password_hash=hashed,
                year=1,
                department_id=dept.id
            )
            session.add(s)
            created_students.append(s)
            
        await session.commit()
        
        target_course_id = target_course.id
        student_numbers = [s.student_number for s in created_students]

    # 2. Login to get tokens
    # Note: We use a separate engine with a connection pool for the concurrent requests
    # to avoid "TooManyConnectionsError" (Postgres max defaults to ~100).
    # This simulates a real production server which would have a connection pool.
    from sqlalchemy.ext.asyncio import create_async_engine
    # Use same URL as conftest
    TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/course_registration_test"
    
    # Pool size 20, max overflow 10. Request 31+ will wait.
    concurrent_engine = create_async_engine(TEST_DB_URL, echo=False, pool_size=20, max_overflow=20)

    async def get_test_db_override():
        async with AsyncSession(concurrent_engine, expire_on_commit=False) as s:
            yield s
            
    app.dependency_overrides[get_db] = get_test_db_override
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for s_num in student_numbers:
            resp = await ac.post("/api/auth/login", json={
                "student_number": s_num,
                "password": password
            })
            assert resp.status_code == 200, f"Login failed for {s_num}"
            tokens.append(resp.json()["access_token"])

    # 3. Concurrent Enrollment Requests
    async def request_enroll(token):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await ac.post(
                "/api/enrollments",
                json={"course_id": target_course_id},
                headers={"Authorization": f"Bearer {token}"}
            )

    # Launch all at once
    responses = await asyncio.gather(*[request_enroll(t) for t in tokens])
    
    # 4. Cleanup Overrides and Engine
    app.dependency_overrides.clear()
    await concurrent_engine.dispose()
    
    # 5. Assertions
    success_count = sum(1 for r in responses if r.status_code == 201)
    conflict_count = sum(1 for r in responses if r.status_code == 409)
    other_count = sum(1 for r in responses if r.status_code not in (201, 409))
    
    # Diagnose if failed
    if success_count != 1:
        # Check reasons
        print(f"Successes: {success_count}, Conflicts: {conflict_count}, Others: {other_count}")
        # If 0 success, maybe something else failed?
        if success_count == 0:
            print("First response:", responses[0].json())

    assert success_count == 1
    assert conflict_count == 99
    assert other_count == 0

    # 6. Verify DB State
    async with AsyncSession(test_engine) as session:
        # Check enrolled count on Course
        c = await session.get(Course, target_course_id)
        assert c.enrolled == 1
        
        # Check actual Enrollment rows
        count = await session.scalar(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == target_course_id)
        )
        assert count == 1
        
    # 7. Cleanup Data (Optional but good practice since we committed)
    async with AsyncSession(test_engine) as session:
        await session.execute(
            select(Enrollment).where(Enrollment.course_id == target_course_id)
        )
        pass
