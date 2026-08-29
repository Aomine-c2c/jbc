import uuid
import pytest
from fastapi import HTTPException
from app.core.authz import AuthzGuard
from app.modules.iam.models import User, Scope

def test_authz_guard_global_override():
    user = User(id=uuid.uuid4())
    permissions = {"global_override": []}
    assert AuthzGuard.check_permission(user, "job_card:read", permissions) is True

def test_authz_guard_global_scope():
    user = User(id=uuid.uuid4())
    permissions = {"job_card:read": [Scope.GLOBAL]}
    assert AuthzGuard.check_permission(user, "job_card:read", permissions) is True

def test_authz_guard_department_scope_success():
    dept_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), department_id=dept_id)
    permissions = {"job_card:read": [Scope.DEPARTMENT]}
    
    # Should succeed because resource_dept_id matches user.department_id
    assert AuthzGuard.check_permission(user, "job_card:read", permissions, resource_dept_id=dept_id) is True
    
    # Should succeed for creating in their own dept (no resource_dept_id passed in some cases, or matched)
    assert AuthzGuard.check_permission(user, "job_card:read", permissions) is True

def test_authz_guard_department_scope_fail():
    dept_id = uuid.uuid4()
    other_dept_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), department_id=dept_id)
    permissions = {"job_card:read": [Scope.DEPARTMENT]}
    
    # Should fail because resource_dept_id does not match
    assert AuthzGuard.check_permission(user, "job_card:read", permissions, resource_dept_id=other_dept_id) is False

def test_authz_guard_own_scope_success():
    user_id = uuid.uuid4()
    user = User(id=user_id)
    permissions = {"job_card:update": [Scope.OWN]}
    
    assert AuthzGuard.check_permission(user, "job_card:update", permissions, resource_owner_id=user_id) is True
    # Can create own resource
    assert AuthzGuard.check_permission(user, "job_card:update", permissions) is True

def test_authz_guard_own_scope_fail():
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    user = User(id=user_id)
    permissions = {"job_card:update": [Scope.OWN]}
    
    assert AuthzGuard.check_permission(user, "job_card:update", permissions, resource_owner_id=other_id) is False

def test_authz_guard_assigned_scope_success():
    user_id = uuid.uuid4()
    user = User(id=user_id)
    permissions = {"job_card:update": [Scope.ASSIGNED]}
    
    assert AuthzGuard.check_permission(user, "job_card:update", permissions, assigned_user_id=user_id) is True

def test_authz_guard_assigned_scope_fail():
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    user = User(id=user_id)
    permissions = {"job_card:update": [Scope.ASSIGNED]}
    
    assert AuthzGuard.check_permission(user, "job_card:update", permissions, assigned_user_id=other_id) is False

def test_authz_guard_self_approval_prevention():
    user_id = uuid.uuid4()
    user = User(id=user_id)
    permissions = {"job_card:approve": [Scope.GLOBAL]}
    
    with pytest.raises(HTTPException) as excinfo:
        AuthzGuard.check_permission(user, "job_card:approve", permissions, resource_owner_id=user_id)
    
    assert excinfo.value.status_code == 409
    assert "cannot approve your own request" in excinfo.value.detail

def test_authz_guard_no_permission():
    user = User(id=uuid.uuid4())
    permissions = {"job_card:read": [Scope.GLOBAL]}
    
    # Trying to update but only has read
    assert AuthzGuard.check_permission(user, "job_card:update", permissions) is False
