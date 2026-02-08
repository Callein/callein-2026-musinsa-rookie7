from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.database import engine, Base
import src.models  # noqa: F401 - ensure models are registered with Base
from src.routers import auth, courses, enrollments, health, professors, students


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기를 관리합니다.

    - 시작 시: 데이터베이스 테이블 생성 (개발용) 및 초기 데이터 시딩
    - 종료 시: 데이터베이스 연결 종료
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from src.services.seed_service import seed_data
    await seed_data()

    yield

    await engine.dispose()


app = FastAPI(
    title="대학교 수강신청 시스템",
    description="Course Registration System API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(professors.router)
app.include_router(enrollments.router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
