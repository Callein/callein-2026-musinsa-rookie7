from pydantic import BaseModel, ConfigDict


class ProfessorResponse(BaseModel):
    """교수 정보 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    employee_number: str
    department_id: int
    department_name: str | None = None


class ProfessorDetailResponse(ProfessorResponse):
    pass
