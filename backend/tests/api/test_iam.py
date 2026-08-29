import pytest
from httpx import AsyncClient
from app.modules.iam.models import User
from app.core.security import verify_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_create_user_unauthorized(async_client: AsyncClient):
    response = await async_client.post("/api/v1/iam/users", json={
        "email": "test@test.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "department_id": None
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_users_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/iam/users")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_secure_login_and_password_hashing(async_client: AsyncClient, seed_user_a, db: AsyncSession):
    # Test that the password in the DB is hashed and not plaintext
    stmt = select(User).where(User.email == seed_user_a.email)
    res = await db.execute(stmt)
    db_user = res.scalars().first()
    
    assert db_user.hashed_password != "password123"
    assert verify_password("password123", db_user.hashed_password) == True
    
    # Test valid login
    response = await async_client.post(
        "/api/v1/iam/auth/login",
        json={"username": seed_user_a.email, "password": "password123"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient, seed_user_a):
    response = await async_client.post(
        "/api/v1/iam/auth/login",
        json={"username": seed_user_a.email, "password": "wrongpassword"},
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_expired_authentication_validation(async_client: AsyncClient):
    from jose import jwt as pyjwt
    from app.core.config import settings
    from datetime import datetime, timedelta
    
    # Generate an expired token
    expire = datetime.utcnow() - timedelta(minutes=15)
    to_encode = {"sub": "123e4567-e89b-12d3-a456-426614174000", "exp": expire}
    expired_token = pyjwt.encode(to_encode, settings.get_secret_key, algorithm=settings.ALGORITHM)
    
    response = await async_client.get("/api/v1/iam/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
