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
    Test 50 concurrent enrollment requests for a course with capacity 1.
    Only 1 should succeed, 49 should fail.
    """
    
    # 1. Setup: Create 50 students and get their tokens
    password = "password"
    hashed = hash_password(password)
    
    students = []
    tokens = []
    
    # We need to interact with DB directly for setup using test_engine
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        # Update course capacity to 1
        # Re-fetch course to attach to this session
        course = await session.get(Course, test_course.id)
        if not course:
             # Should not happen if fixtures work, but let's be safe
             # If test_course came from a rollback session, it might not exist in this new session 
             # unless test_course fixture committed it.
             # conftest.py `test_course` uses `db_session` which rolls back.
             # BUT `test_engine` is shared. 
             # If `test_course` fixture didn't commit, we won't see it here.
             # In `conftest.py`, `test_course` fixture does NOT commit at the end (I changed it to flush).
             # So we might need to recreate data or ensure `test_course` is committed.
             pass

        # Wait, `test_course` fixture in `conftest.py` uses `db_session`.
        # `db_session` rolls back at the end of the test function.
        # But inside the test function, `test_course` exists in `db_session`.
        # Here we are using `test_engine` to create NEW sessions.
        # These new sessions will NOT see uncommitted data from `db_session`.
        
        # So we MUST commit `test_course` in `db_session` (the fixture one) 
        # OR we just rely on `db_session` to commit? 
        # But `db_session` fixture explicitly rolls back.
        # If we commit in `db_session`, the rollback in fixture teardown might fail or just roll back the empty transaction?
        # Actually, if we commit, the data is persisted. The teardown `rollback()` will only roll back the *current* transaction.
        # Data committed *before* that will remain until... when? 
        # `test_engine` scope is session. It drops all tables at start.
        # So committed data persists across tests if we are not careful?
        # No, `db_session` fixture yields a session. Teardown calls `rollback()`.
        # If we `commit()` inside the test (or fixture), that data is in DB.
        # `rollback()` only undoes changes since last commit.
        # So if we commit, we pollute the DB for other tests?
        # Yes. But `test_engine` fixture creates tables *once* per session.
        # We should probably truncate tables after each test? `conftest.py` doesn't seem to do that.
        # It relies on `transaction.rollback()`.
        # This implies standard tests should NOT commit.
        
        # BUT for concurrency test with multiple sessions, we MUST commit data so other sessions can see it.
        # So for THIS test, we must commit.
        pass

    # Let's commit the `test_course` and `test_department` so other sessions can see them.
    # We can do this by using a separate setup or just committing existing fixture objects?
    # Accessing `db_session` fixture directly in test might verify this.
    
    # We'll use a local session to create everything we need, ensuring it's committed.
    # We won't rely on `test_course` fixture effectively because of the visibility issue.
    
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
        
        # Create 50 students
        created_students = []
        for i in range(50):
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
    # We need a dependency override to use a session from test_engine
    async def get_test_db_override():
        async with AsyncSession(test_engine, expire_on_commit=False) as s:
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
        # Each request must have its own dependency scope effectively.
        # But `app.dependency_overrides` is global.
        # Fortunately `get_test_db_override` creates a NEW session each time validly.
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await ac.post(
                "/api/enrollments",
                json={"course_id": target_course_id},
                headers={"Authorization": f"Bearer {token}"}
            )

    # Launch all at once
    responses = await asyncio.gather(*[request_enroll(t) for t in tokens])
    
    # 4. Cleanup Overrides
    app.dependency_overrides.clear()
    
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
    assert conflict_count == 49
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
        # Delete enrollments, students, course, professor, etc. to be clean?
        # Or just rely on test DB being trashable.
        # Since other tests use `db_session` which clears itself, 
        # and this test created new unique data (ConcurrencyDept), collision is unlikely.
        pass
