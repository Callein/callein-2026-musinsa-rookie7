from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class CourseSchedule(Base):
    """
    강좌의 시간표 정보를 저장하는 모델입니다.

    요일(day_of_week)과 시작/종료 시간을 저장하여 시간표 충돌 확인에 사용됩니다.
    """

    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(3), nullable=False)  # 월,화,수,목,금
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)   # "09:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)     # "10:30"

    course = relationship("Course", back_populates="schedules")
