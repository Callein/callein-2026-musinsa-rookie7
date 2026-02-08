from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from src.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY


def hash_password(plain_password: str) -> str:
    """
    비밀번호를 해싱합니다.

    Args:
        plain_password (str): 평문 비밀번호

    Returns:
        str: 해싱된 비밀번호 문자열
    """

    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호가 일치하는지 확인합니다.

    Args:
        plain_password (str): 평문 비밀번호
        hashed_password (str): 저장된 해싱된 비밀번호

    Returns:
        bool: 일치 여부
    """

    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(student_id: int, student_number: str) -> str:
    """
    JWT 액세스 토큰을 생성합니다.

    Args:
        student_id (int): 학생 ID (DB PK)
        student_number (str): 학번

    Returns:
        str: 생성된 JWT 토큰
    """

    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(student_id),
        "student_number": student_number,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    JWT 액세스 토큰을 디코딩하고 검증합니다.

    Args:
        token (str): JWT 토큰

    Returns:
        dict: 디코딩된 페이로드 (Claims)

    Raises:
        jwt.PyJWTError: 토큰이 유효하지 않거나 만료된 경우
    """

    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
