from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.dependencies import get_current_student
from src.models.course import Course
from src.models.course_schedule import CourseSchedule
from src.models.enrollment import Enrollment
from src.models.student import Student
from src.schemas.common import SingleResponse
from src.schemas.enrollment import (
    EnrollmentRequest,
    EnrollmentResponse,
    ScheduleItemResponse,
)
from src.services import enrollment_service

router = APIRouter(prefix="/api/enrollments", tags=["수강신청"])


@router.post(
    "",
    response_model=SingleResponse[EnrollmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_enrollment(
    body: EnrollmentRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    enrollment = await enrollment_service.enroll(student.id, body.course_id, db)
    await db.commit()
    await db.refresh(enrollment)

    course = await db.execute(
        select(Course).where(Course.id == enrollment.course_id)
    )
    course = course.scalar_one()

    return SingleResponse(
        data=EnrollmentResponse(
            id=enrollment.id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
            course_name=course.name,
            credits=course.credits,
            enrolled_at=enrollment.enrolled_at,
        )
    )


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_enrollment(
    enrollment_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    await enrollment_service.drop(enrollment_id, student.id, db)
    await db.commit()


@router.get("/me/schedule", response_model=SingleResponse[list[ScheduleItemResponse]])
async def get_my_schedule(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.course).selectinload(Course.schedules),
            selectinload(Enrollment.course).selectinload(Course.professor),
        )
        .where(Enrollment.student_id == student.id)
    )
    enrollments = result.scalars().unique().all()

    schedule_items = []
    for enrollment in enrollments:
        course = enrollment.course
        for sched in course.schedules:
            schedule_items.append(
                ScheduleItemResponse(
                    course_id=course.id,
                    course_name=course.name,
                    course_code=course.course_code,
                    credits=course.credits,
                    professor_name=course.professor.name if course.professor else None,
                    day_of_week=sched.day_of_week,
                    start_time=sched.start_time,
                    end_time=sched.end_time,
                )
            )

    schedule_items.sort(key=lambda x: (
        ["월", "화", "수", "목", "금"].index(x.day_of_week)
        if x.day_of_week in ["월", "화", "수", "목", "금"] else 99,
        x.start_time,
    ))

    return SingleResponse(data=schedule_items)
