import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_student):
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
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "20240001", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_student(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"student_number": "99999999", "password": "password"},
    )
    assert response.status_code == 401
