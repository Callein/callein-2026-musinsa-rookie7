from pydantic import BaseModel, ConfigDict


class ProfessorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    employee_number: str
    department_id: int
    department_name: str | None = None


class ProfessorDetailResponse(ProfessorResponse):
    pass
