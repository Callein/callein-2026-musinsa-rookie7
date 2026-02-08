from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.student import Student
from src.services.auth_service import decode_access_token

security = HTTPBearer()


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Student:
    """
    현재 로그인한 학생 정보를 조회하는 의존성 함수입니다.

    Header의 Bearer Token을 파싱하여 학생을 식별합니다.

    Args:
        credentials (HTTPAuthorizationCredentials): Authorization 헤더 정보
        db (AsyncSession): 데이터베이스 세션

    Returns:
        Student: 인증된 학생 객체

    Raises:
        HTTPException(401): 토큰이 유효하지 않거나 학생을 찾을 수 없는 경우
    """

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        student_id = int(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
        )

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="해당 학생을 찾을 수 없습니다.",
        )
    return student
