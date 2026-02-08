from pydantic import BaseModel, ConfigDict


class StudentResponse(BaseModel):
    """학생 정보 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    student_number: str
    year: int
    department_id: int
    department_name: str | None = None


class StudentDetailResponse(StudentResponse):
    pass
