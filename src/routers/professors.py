import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from src.database import get_db
from src.models.professor import Professor
from src.schemas.common import PaginatedResponse, PaginationMeta
from src.schemas.professor import ProfessorDetailResponse, ProfessorResponse

router = APIRouter(prefix="/api/professors", tags=["교수"])


@router.get("", response_model=PaginatedResponse[ProfessorResponse])
async def list_professors(
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    department_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Professor).options(selectinload(Professor.department))
    count_query = select(func.count()).select_from(Professor)

    if department_id is not None:
        query = query.where(Professor.department_id == department_id)
        count_query = count_query.where(Professor.department_id == department_id)

    total = await db.scalar(count_query)
    total = total or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    professors = result.scalars().all()

    data = [
        ProfessorResponse(
            id=p.id,
            name=p.name,
            employee_number=p.employee_number,
            department_id=p.department_id,
            department_name=p.department.name if p.department else None,
        )
        for p in professors
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


@router.get("/{professor_id}", response_model=ProfessorDetailResponse)
async def get_professor(professor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Professor)
        .options(selectinload(Professor.department))
        .where(Professor.id == professor_id)
    )
    professor = result.scalar_one_or_none()
    if professor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 교수를 찾을 수 없습니다.",
        )
    return ProfessorDetailResponse(
        id=professor.id,
        name=professor.name,
        employee_number=professor.employee_number,
        department_id=professor.department_id,
        department_name=professor.department.name if professor.department else None,
    )
