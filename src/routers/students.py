import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.database import get_db
from src.models.student import Student
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.student import StudentDetailResponse, StudentResponse

router = APIRouter(prefix="/api/students", tags=["학생"])


@router.get("", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    department_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Student).options(selectinload(Student.department))
    count_query = select(func.count()).select_from(Student)

    if department_id is not None:
        query = query.where(Student.department_id == department_id)
        count_query = count_query.where(Student.department_id == department_id)

    total = await db.scalar(count_query)
    total = total or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    students = result.scalars().all()

    data = [
        StudentResponse(
            id=s.id,
            name=s.name,
            student_number=s.student_number,
            year=s.year,
            department_id=s.department_id,
            department_name=s.department.name if s.department else None,
        )
        for s in students
    ]

    return PaginatedResponse(
        data=data,
        meta=PaginationMeta(
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit) if total > 0 else 0,
        ),
    )


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.department))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 학생을 찾을 수 없습니다.",
        )
    return StudentDetailResponse(
        id=student.id,
        name=student.name,
        student_number=student.student_number,
        year=student.year,
        department_id=student.department_id,
        department_name=student.department.name if student.department else None,
    )
