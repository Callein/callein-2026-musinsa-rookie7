import os


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/course_registration",
)

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

MAX_CREDITS_PER_SEMESTER = 18
