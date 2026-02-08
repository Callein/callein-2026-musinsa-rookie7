from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentRequest(BaseModel):
    """수강신청 요청 스키마"""
    course_id: int


class EnrollmentResponse(BaseModel):
    """수강신청 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    course_name: str | None = None
    credits: int | None = None
    enrolled_at: datetime


class ScheduleItemResponse(BaseModel):
    """시간표 아이템 응답 스키마"""
    course_id: int
    course_name: str
    course_code: str
    credits: int
    professor_name: str | None = None
    day_of_week: str
    start_time: str
    end_time: str
