import pytest
from httpx import AsyncClient

# Note: In a real test environment, we would use a test database fixture 
# and factory_boy to spawn these users, roles, and permissions dynamically.
# Due to environment limitations, this suite acts as a structural implementation 
# of the RBAC scenarios requested by the user.

@pytest.mark.asyncio
async def test_allowed_access(async_client: AsyncClient):
    """Verifies that an authorized role mapping successfully grants access."""
    # Assuming 'mock_admin_token' maps to a user with 'users:manage'
    headers = {"Authorization": "Bearer mock_admin_token"}
    response = await async_client.post("/api/v1/iam/users", headers=headers, json={
        "email": "new@test.com",
        "first_name": "New",
        "last_name": "User",
        "password": "Password123!"
    })
    # We expect a success or validation error, but NOT 403 Forbidden
    assert response.status_code != 403

@pytest.mark.asyncio
async def test_denied_access(async_client: AsyncClient):
    """Verifies the deny-by-default block on missing permissions."""
    # Assuming 'mock_viewer_token' maps to a user without 'users:manage'
    headers = {"Authorization": "Bearer mock_viewer_token"}
    response = await async_client.post("/api/v1/iam/users", headers=headers, json={
        "email": "hacked@test.com",
        "first_name": "Hacked",
        "last_name": "User",
        "password": "Password123!"
    })
    # We explicitly expect 403 Forbidden due to deny-by-default AuthzGuard
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_cross_department_access():
    """Verifies AuthzGuard blocks cross-department requests without global privileges."""
    from app.core.authz import AuthzGuard
    from app.modules.iam.models import User
    import uuid
    
    my_dept = uuid.uuid4()
    other_dept = uuid.uuid4()
    user = User(id=uuid.uuid4(), department_id=my_dept)
    
    # Standard user trying to access other department with DEPARTMENT scope
    result = AuthzGuard.check_permission(user, "jobs:read", {"jobs:read": ["DEPARTMENT"]}, resource_dept_id=other_dept)
    assert result == False
    
    # User with GLOBAL scope -> Should Pass
    result = AuthzGuard.check_permission(user, "jobs:read", {"jobs:read": ["GLOBAL"]}, resource_dept_id=other_dept)
    assert result == True

@pytest.mark.asyncio
async def test_resource_ownership():
    """Verifies Job Card creator constraints (Resource Ownership)."""
    from app.core.authz import AuthzGuard
    from app.modules.iam.models import User
    import uuid
    
    me = uuid.uuid4()
    someone_else = uuid.uuid4()
    user = User(id=me)
    
    # Standard user trying to edit someone else's resource with OWN scope
    result = AuthzGuard.check_permission(user, "jobs:update", {"jobs:update": ["OWN"]}, resource_owner_id=someone_else)
    assert result == False
    
    # SysAdmin with global override -> Should Pass
    result = AuthzGuard.check_permission(user, "jobs:update", {"global_override": []}, resource_owner_id=someone_else)
    assert result == True

@pytest.mark.asyncio
async def test_workflow_permissions():
    """Verifies separation of duties block."""
    from app.core.authz import AuthzGuard
    from app.modules.iam.models import User
    import uuid
    from fastapi import HTTPException
    
    user = User(id=uuid.uuid4())
    
    with pytest.raises(HTTPException) as excinfo:
        AuthzGuard.check_permission(user, "jobs:approve", {"jobs:approve": ["GLOBAL"]}, resource_owner_id=user.id)
    assert excinfo.value.status_code == 409
