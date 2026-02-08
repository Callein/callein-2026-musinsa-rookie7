import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_student):
    """올바른 학번과 비밀번호로 로그인 성공 시 토큰을 반환해야 합니다."""
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "20240001", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_student):
    """비밀번호가 틀리면 401 Unauthorized 에러를 반환해야 합니다."""
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "20240001", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_student(client: AsyncClient):
    """존재하지 않는 학생이면 401 Unauthorized 에러를 반환해야 합니다."""
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "99999999", "password": "password"},
    )
    assert response.status_code == 401
