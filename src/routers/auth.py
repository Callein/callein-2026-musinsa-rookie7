from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.student import Student
from src.schemas.auth import LoginRequest, LoginResponse
from src.services.auth_service import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["인증"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student).where(Student.student_number == body.student_number)
    )
    student = result.scalar_one_or_none()

    if student is None or not verify_password(body.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="학번 또는 비밀번호가 올바르지 않습니다.",
        )

    token = create_access_token(student.id, student.student_number)
    return LoginResponse(access_token=token)
