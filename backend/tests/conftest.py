import os

# Mock bearer tokens are an explicit test fixture, never a development or
# production authentication path. Set these before importing the application
# settings singleton.
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("ALLOW_TEST_TOKENS", "true")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.main import app
from app.modules import Base
from app.db.session import get_db
import uuid

# Use in-memory SQLite with StaticPool and expire_on_commit=False
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=test_engine, class_=AsyncSession)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def async_client(db: AsyncSession):
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def seed_department_a(db: AsyncSession):
    from app.modules.iam.models import Department
    dept = Department(id=uuid.uuid4(), name="Engineering")
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def seed_department_b(db: AsyncSession):
    from app.modules.iam.models import Department
    dept = Department(id=uuid.uuid4(), name="Operations")
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def seed_user_a(db: AsyncSession, seed_department_a):
    from app.modules.iam.models import User
    from app.core.security import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="usera@example.com",
        first_name="User",
        last_name="A",
        hashed_password=get_password_hash("password123"),
        department_id=seed_department_a.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def token_user_a(seed_user_a):
    from app.core.security import create_access_token
    return create_access_token(subject=str(seed_user_a.id))

@pytest_asyncio.fixture
async def seed_user_b(db: AsyncSession, seed_department_b):
    from app.modules.iam.models import User
    from app.core.security import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="userb@example.com",
        first_name="User",
        last_name="B",
        hashed_password=get_password_hash("password123"),
        department_id=seed_department_b.id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def token_user_b(seed_user_b):
    from app.core.security import create_access_token
    return create_access_token(subject=str(seed_user_b.id))

@pytest_asyncio.fixture
async def seed_admin_user(db: AsyncSession, seed_department_a):
    from app.modules.iam.models import User
    from app.core.security import get_password_hash
    user = User(
        id=uuid.uuid4(),
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("password123"),
        department_id=seed_department_a.id,
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_token(seed_admin_user):
    from app.core.security import create_access_token
    return create_access_token(subject=str(seed_admin_user.id))

@pytest_asyncio.fixture
async def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest_asyncio.fixture
async def mock_user_token():
    return "mock.jwt.token"
