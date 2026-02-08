from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentRequest(BaseModel):
    course_id: int


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    course_name: str | None = None
    credits: int | None = None
    enrolled_at: datetime


class ScheduleItemResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    credits: int
    professor_name: str | None = None
    day_of_week: str
    start_time: str
    end_time: str
