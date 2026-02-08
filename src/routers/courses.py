import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.database import get_db
from src.models.course import Course
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.course import CourseDetailResponse, CourseResponse, ScheduleResponse

router = APIRouter(prefix="/api/courses", tags=["강좌"])


def _course_to_response(c: Course) -> CourseResponse:
    return CourseResponse(
        id=c.id,
        name=c.name,
        course_code=c.course_code,
        credits=c.credits,
        capacity=c.capacity,
        enrolled=c.enrolled,
        department_id=c.department_id,
        department_name=c.department.name if c.department else None,
        professor_name=c.professor.name if c.professor else None,
        schedule=[
            ScheduleResponse(
                day_of_week=s.day_of_week,
                start_time=s.start_time,
                end_time=s.end_time,
            )
            for s in c.schedules
        ],
    )


@router.get("", response_model=PaginatedResponse[CourseResponse])
async def list_courses(
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    department_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Course).options(
        selectinload(Course.department),
        selectinload(Course.professor),
        selectinload(Course.schedules),
    )
    count_query = select(func.count()).select_from(Course)

    if department_id is not None:
        query = query.where(Course.department_id == department_id)
        count_query = count_query.where(Course.department_id == department_id)

    total = await db.scalar(count_query)
    total = total or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().unique().all()

    return PaginatedResponse(
        data=[_course_to_response(c) for c in courses],
        meta=PaginationMeta(
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if total > 0 else 0,
        ),
    )


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.department),
            selectinload(Course.professor),
            selectinload(Course.schedules),
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 강좌를 찾을 수 없습니다.",
        )
    return _course_to_response(course)
