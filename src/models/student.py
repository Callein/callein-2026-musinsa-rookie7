from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Student(Base):
    """
    학생 정보를 저장하는 모델입니다.
    """

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    student_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # 학년 1~4
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    department = relationship("Department", back_populates="students")
    enrollments = relationship("Enrollment", back_populates="student")
