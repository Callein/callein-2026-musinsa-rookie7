from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    course_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    enrolled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professors.id"), nullable=False)

    department = relationship("Department", back_populates="courses")
    professor = relationship("Professor", back_populates="courses")
    schedules = relationship("CourseSchedule", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course")
