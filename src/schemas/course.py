from pydantic import BaseModel, ConfigDict


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day_of_week: str
    start_time: str
    end_time: str


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    course_code: str
    credits: int
    capacity: int
    enrolled: int
    department_id: int
    department_name: str | None = None
    professor_name: str | None = None
    schedule: list[ScheduleResponse] = []


class CourseDetailResponse(CourseResponse):
    pass
