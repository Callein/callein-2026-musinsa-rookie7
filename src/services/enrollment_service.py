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
    """
    수강신청을 처리합니다.

    `SELECT ... FOR UPDATE`를 사용하여 강좌 레코드에 비관적 락(Pessimistic Lock)을 걸고,
    동시성 이슈(경쟁 조건)를 방지하며 수강신청을 수행합니다.

    검증 항목:
    1. 강좌 존재 여부
    2. 중복 수강 신청 여부
    3. 정원 초과 여부
    4. 최대 학점 초과 여부
    5. 시간표 충돌 여부

    Args:
        student_id (int): 신청하는 학생의 ID
        course_id (int): 신청할 강좌의 ID
        db (AsyncSession): 데이터베이스 세션

    Returns:
        Enrollment: 생성된 수강신청 내역 객체

    Raises:
        HTTPException(404): 강좌를 찾을 수 없는 경우
        HTTPException(409): 비즈니스 규칙 위반 (정원, 학점, 시간 등)
    """


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
    """
    수강신청을 취소합니다.

    수강 내역을 삭제하고, 해당 강좌의 현재 수강 인원을 1 감소시킵니다.
    본인의 수강 신청 내역만 취소할 수 있습니다.

    Args:
        enrollment_id (int): 취소할 수강신청 내역 ID
        student_id (int): 요청하는 학생의 ID
        db (AsyncSession): 데이터베이스 세션

    Raises:
        HTTPException(404): 수강 신청 내역이 없는 경우
        HTTPException(403): 본인의 수강 신청이 아닌 경우
    """


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
    """
    신청하려는 강좌가 기존 수강 강좌와 시간이 겹치는지 확인합니다.

    Args:
        db (AsyncSession): 데이터베이스 세션
        student_id (int): 학생 ID
        new_course_id (int): 신청하려는 강좌 ID

    Raises:
        HTTPException(409): 시간표가 충돌하는 경우
    """


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
