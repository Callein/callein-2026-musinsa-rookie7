from pydantic import BaseModel


class LoginRequest(BaseModel):
    student_number: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
