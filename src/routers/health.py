from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """서버 상태를 확인합니다 (Health Check)."""
    return {"status": "ok"}
