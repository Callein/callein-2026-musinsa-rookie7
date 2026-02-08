from sqlalchemy import ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(3), nullable=False)  # 월,화,수,목,금
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)   # "09:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)     # "10:30"

    course = relationship("Course", back_populates="schedules")
