from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import MAX_CREDITS_PER_SEMESTER
from src.models.course import Course
from src.models.course_schedule import CourseSchedule
from src.models.enrollment import Enrollment


async def enroll(
    student_id: int, course_id: int, db: AsyncSession
) -> Enrollment:
    """수강신청을 처리합니다. SELECT FOR UPDATE로 동시성 제어."""

    course = await db.execute(
        select(Course).where(Course.id == course_id).with_for_update()
    )
    course = course.scalar_one_or_none()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 강좌를 찾을 수 없습니다.",
        )

    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 수강 신청한 강좌입니다.",
        )

    if course.enrolled >= course.capacity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="해당 강좌의 정원이 초과되었습니다.",
        )

    current_credits = await db.scalar(
        select(func.coalesce(func.sum(Course.credits), 0))
        .join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.student_id == student_id)
    )
    if current_credits + course.credits > MAX_CREDITS_PER_SEMESTER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"최대 수강 학점({MAX_CREDITS_PER_SEMESTER}학점)을 초과합니다. "
            f"현재 {current_credits}학점, 신청 강좌 {course.credits}학점.",
        )

    await _check_schedule_conflict(db, student_id, course_id)

    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.add(enrollment)
    course.enrolled = course.enrolled + 1

    await db.flush()
    return enrollment


async def drop(
    enrollment_id: int, student_id: int, db: AsyncSession
) -> None:
    """수강취소를 처리합니다."""

    result = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 수강 신청 내역을 찾을 수 없습니다.",
        )

    if enrollment.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 수강 신청만 취소할 수 있습니다.",
        )

    course = await db.execute(
        select(Course).where(Course.id == enrollment.course_id).with_for_update()
    )
    course = course.scalar_one()
    course.enrolled = max(0, course.enrolled - 1)

    await db.delete(enrollment)
    await db.flush()


async def _check_schedule_conflict(
    db: AsyncSession, student_id: int, new_course_id: int
) -> None:
    """기존 수강 강좌와 시간표 충돌을 확인합니다."""

    new_schedules = await db.execute(
        select(CourseSchedule).where(CourseSchedule.course_id == new_course_id)
    )
    new_slots = new_schedules.scalars().all()

    if not new_slots:
        return

    enrolled_course_ids = await db.execute(
        select(Enrollment.course_id).where(Enrollment.student_id == student_id)
    )
    enrolled_ids = [row[0] for row in enrolled_course_ids.all()]

    if not enrolled_ids:
        return

    existing_schedules = await db.execute(
        select(CourseSchedule).where(CourseSchedule.course_id.in_(enrolled_ids))
    )
    existing_slots = existing_schedules.scalars().all()

    for new_slot in new_slots:
        for existing_slot in existing_slots:
            if (
                new_slot.day_of_week == existing_slot.day_of_week
                and new_slot.start_time < existing_slot.end_time
                and existing_slot.start_time < new_slot.end_time
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"기존 수강 강좌와 시간이 충돌합니다. "
                    f"({existing_slot.day_of_week} {existing_slot.start_time}-{existing_slot.end_time})",
                )
