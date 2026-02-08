import logging
import random

from sqlalchemy import func, select

from src.database import async_session
from src.models import Course, CourseSchedule, Department, Enrollment, Professor, Student
from src.utils.seed_data import (
    COURSES_BY_DEPARTMENT,
    DAYS_OF_WEEK,
    DEPARTMENTS,
    FIRST_NAMES,
    LAST_NAMES,
    TIME_SLOTS,
)

logger = logging.getLogger(__name__)

from src.services.auth_service import hash_password

# 테스트 편의성을 위해 모든 사용자의 비밀번호를 "password"로 통일합니다.
DEFAULT_PASSWORD_HASH = hash_password("password")


async def seed_data():
    """서버 시작 시 초기 데이터를 생성합니다. 멱등성 보장."""
    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(Department))
        if count and count > 0:
            logger.info("데이터가 이미 존재합니다. 시드 생성을 스킵합니다.")
            return

        logger.info("초기 데이터 생성을 시작합니다...")
        rng = random.Random(42)

        departments = await _seed_departments(session)
        professors = await _seed_professors(session, departments, rng)
        courses = await _seed_courses(session, departments, professors, rng)
        await _seed_students(session, departments, rng)

        await session.commit()
        logger.info(
            "초기 데이터 생성 완료: 학과 %d, 교수 %d, 강좌 %d",
            len(departments),
            len(professors),
            len(courses),
        )


async def _seed_departments(session) -> list[Department]:
    departments = [Department(name=name) for name in DEPARTMENTS]
    session.add_all(departments)
    await session.flush()
    return departments


async def _seed_professors(
    session, departments: list[Department], rng: random.Random
) -> list[Professor]:
    professors = []
    employee_num = 1000
    used_names: set[str] = set()

    for dept in departments:
        count = rng.randint(8, 12)
        for _ in range(count):
            name = _unique_name(rng, used_names)
            professors.append(
                Professor(
                    name=name,
                    employee_number=f"P{employee_num:04d}",
                    department_id=dept.id,
                )
            )
            employee_num += 1

    session.add_all(professors)
    await session.flush()
    return professors


async def _seed_courses(
    session,
    departments: list[Department],
    professors: list[Professor],
    rng: random.Random,
) -> list[Course]:
    courses = []
    schedules = []
    course_num = 1

    dept_professors: dict[int, list[Professor]] = {}
    for prof in professors:
        dept_professors.setdefault(prof.department_id, []).append(prof)

    used_slots_by_prof: dict[int, set[tuple[str, str, str]]] = {}

    for dept in departments:
        dept_name = dept.name
        course_names = COURSES_BY_DEPARTMENT.get(dept_name, [])
        profs = dept_professors.get(dept.id, [])
        if not profs:
            continue

        sections_per_course = max(1, 500 // (len(DEPARTMENTS) * len(course_names)))

        for cname in course_names:
            for section in range(1, sections_per_course + 1):
                credits = rng.choice([2, 3, 3, 3])
                capacity = rng.randint(30, 50)
                prof = rng.choice(profs)

                code = f"{dept_name[:2]}{course_num:04d}"
                display_name = cname if section == 1 else f"{cname} ({section}분반)"

                course = Course(
                    name=display_name,
                    course_code=code,
                    credits=credits,
                    capacity=capacity,
                    enrolled=0,
                    department_id=dept.id,
                    professor_id=prof.id,
                )
                courses.append(course)
                course_num += 1

    session.add_all(courses)
    await session.flush()

    for course in courses:
        num_sessions = 2 if course.credits == 3 else 1
        prof_slots = used_slots_by_prof.setdefault(course.professor_id, set())

        assigned = 0
        attempts = 0
        while assigned < num_sessions and attempts < 50:
            day = rng.choice(DAYS_OF_WEEK)
            start, end = rng.choice(TIME_SLOTS)
            slot_key = (day, start, end)
            attempts += 1

            if slot_key not in prof_slots:
                prof_slots.add(slot_key)
                schedules.append(
                    CourseSchedule(
                        course_id=course.id,
                        day_of_week=day,
                        start_time=start,
                        end_time=end,
                    )
                )
                assigned += 1

    session.add_all(schedules)
    await session.flush()
    return courses


async def _seed_students(
    session, departments: list[Department], rng: random.Random
) -> list[Student]:
    students = []
    student_num = 20210001
    used_numbers: set[str] = set()

    for i in range(10000):
        dept = rng.choice(departments)
        year = rng.randint(1, 4)
        last = rng.choice(LAST_NAMES)
        first = rng.choice(FIRST_NAMES)
        name = f"{last}{first}"
        snum = f"{student_num + i}"

        students.append(
            Student(
                name=name,
                student_number=snum,
                password_hash=DEFAULT_PASSWORD_HASH,
                year=year,
                department_id=dept.id,
            )
        )

    # batch insert for performance
    batch_size = 1000
    for i in range(0, len(students), batch_size):
        session.add_all(students[i : i + batch_size])
        await session.flush()

    return students


def _unique_name(rng: random.Random, used: set[str]) -> str:
    for _ in range(100):
        name = f"{rng.choice(LAST_NAMES)}{rng.choice(FIRST_NAMES)}"
        if name not in used:
            used.add(name)
            return name
    return f"{rng.choice(LAST_NAMES)}{rng.choice(FIRST_NAMES)}{rng.randint(1, 99)}"
