import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Course, CourseSchedule, Enrollment


@pytest.mark.asyncio
async def test_enroll_success(
    client: AsyncClient, auth_headers: dict, test_student, test_course, db_session: AsyncSession
):
    response = await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["course_id"] == test_course.id
    assert data["data"]["student_id"] == test_student.id

    await db_session.refresh(test_course)
    assert test_course.enrolled == 1


@pytest.mark.asyncio
async def test_enroll_duplicate(
    client: AsyncClient, auth_headers: dict, test_student, test_course
):
    await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert "이미 수강 신청" in response.json()["detail"]


@pytest.mark.asyncio
async def test_enroll_capacity_full(
    client: AsyncClient, auth_headers: dict, test_student, test_course, db_session: AsyncSession
):
    test_course.enrolled = test_course.capacity
    await db_session.commit()

    response = await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert "정원이 초과" in response.json()["detail"]


@pytest.mark.asyncio
async def test_enroll_credit_limit(
    client: AsyncClient, auth_headers: dict, test_student, db_session: AsyncSession
):
    from src.models import Department, Professor

    dept = await db_session.get(Department, test_student.department_id)
    prof = Professor(name="김교수", employee_number="P9999", department_id=dept.id)
    db_session.add(prof)
    await db_session.flush()

    for i in range(6):
        course = Course(
            name=f"과목{i}",
            course_code=f"C{i:03d}",
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
            day_of_week=["월", "화", "수", "목", "금"][i % 5],
            start_time=f"{9 + i}:00",
            end_time=f"{10 + i}:15",
        )
        db_session.add(schedule)

        enrollment = Enrollment(student_id=test_student.id, course_id=course.id)
        db_session.add(enrollment)
        course.enrolled += 1

    await db_session.commit()

    new_course = Course(
        name="추가과목",
        course_code="CEXTRA",
        credits=3,
        capacity=30,
        enrolled=0,
        department_id=dept.id,
        professor_id=prof.id,
    )
    db_session.add(new_course)
    await db_session.commit()

    response = await client.post(
        "/api/enrollments",
        json={"course_id": new_course.id},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert "최대 수강 학점" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancel_enrollment(
    client: AsyncClient, auth_headers: dict, test_student, test_course, db_session: AsyncSession
):
    enroll_resp = await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )
    enrollment_id = enroll_resp.json()["data"]["id"]

    response = await client.delete(
        f"/api/enrollments/{enrollment_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    await db_session.refresh(test_course)
    assert test_course.enrolled == 0


@pytest.mark.asyncio
async def test_get_my_schedule(
    client: AsyncClient, auth_headers: dict, test_student, test_course
):
    await client.post(
        "/api/enrollments",
        json={"course_id": test_course.id},
        headers=auth_headers,
    )

    response = await client.get(
        "/api/enrollments/me/schedule",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["course_id"] == test_course.id
    assert data["data"][0]["day_of_week"] == "월"
