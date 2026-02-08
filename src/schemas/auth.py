from pydantic import BaseModel


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    student_number: str
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 스키마 (JWT 토큰)"""
    access_token: str
    token_type: str = "bearer"
