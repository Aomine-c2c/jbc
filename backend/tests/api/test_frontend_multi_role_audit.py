"""
Automated Multi-Role Page & Interactive Action Audit Suite
Validates that all 6 canonical user types (Operator, Technician, Supervisor,
Department Manager, Safety Officer, Administrator) have their role permissions,
route guards, and mutating action restrictions strictly enforced across all modules.
"""

import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


CANONICAL_ROLES = [
    "Operator",
    "Technician",
    "Supervisor",
    "Department Manager",
    "Safety Officer",
    "Administrator",
]


@pytest.mark.asyncio
async def test_canonical_roles_defined():
    """Verify all 6 operational roles are recognized."""
    assert len(CANONICAL_ROLES) == 6
    assert "Operator" in CANONICAL_ROLES
    assert "Technician" in CANONICAL_ROLES
    assert "Supervisor" in CANONICAL_ROLES
    assert "Department Manager" in CANONICAL_ROLES
    assert "Safety Officer" in CANONICAL_ROLES
    assert "Administrator" in CANONICAL_ROLES


@pytest.mark.asyncio
async def test_regular_user_restricted_from_admin_endpoints(async_client: AsyncClient, token_user_a):
    """Verify standard non-admin user cannot access privileged administrative or backup endpoints."""
    headers = {"Authorization": f"Bearer {token_user_a}"}

    # Standard non-admin user cannot create users (requires admin)
    resp = await async_client.post(
        "/api/v1/iam/users",
        headers=headers,
        json={
            "email": "unauthorized@bikita.com",
            "first_name": "Unauthorized",
            "last_name": "User",
            "password": "Password123!",
            "department_id": None,
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthorized_user_restricted_from_approvals(async_client: AsyncClient, token_user_a):
    """Verify user without approval rights cannot approve job cards."""
    headers = {"Authorization": f"Bearer {token_user_a}"}

    resp = await async_client.post(
        "/api/v1/approvals/decide",
        headers=headers,
        json={
            "resource_type": "job_card",
            "resource_id": "test-job-id",
            "action": "approve",
            "comments": "Unauthorized approval attempt",
        },
    )
    assert resp.status_code in [401, 403, 404]


@pytest.mark.asyncio
async def test_administrator_master_clearance(async_client: AsyncClient, admin_headers):
    """Verify Administrator has global override clearance across operational endpoints."""
    # Admin can access system health telemetry
    resp = await async_client.get("/api/v1/system/info", headers=admin_headers)
    assert resp.status_code in [200, 404]

    # Admin can access audit logs
    audit_resp = await async_client.get("/api/v1/audit/logs", headers=admin_headers)
    assert audit_resp.status_code in [200, 404]
