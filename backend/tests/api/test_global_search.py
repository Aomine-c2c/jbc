import uuid

import pytest
from httpx import AsyncClient

from app.modules.assets.models import Asset
from app.modules.jobs.models import JobCard
from app.modules.requests.models import OperationalRequest


@pytest.mark.asyncio
async def test_global_search_returns_only_authorized_records(async_client: AsyncClient, db, seed_user_a, seed_department_a, seed_department_b, seed_user_b):
    other_job = JobCard(
        id=uuid.uuid4(),
        title="Unapproved shutdown",
        description="Should stay hidden",
        status="ASSIGNED",
        priority=2,
        department_id=seed_department_b.id,
        creator_id=seed_user_b.id,
        job_number="JC-2026-9999",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
    )
    visible_job = JobCard(
        id=uuid.uuid4(),
        title="Generator outage",
        description="Visible search result",
        status="ASSIGNED",
        priority=1,
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-0001",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
    )
    db.add_all([other_job, visible_job])
    await db.commit()

    headers = {"Authorization": f"Bearer {pytest.importorskip('app.core.security').create_access_token(subject=str(seed_user_a.id))}"}
    response = await async_client.get("/api/v1/search?q=outage", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["groups"]
    assert not any(item["entity"] == "job_cards" and item["reference"] == "JC-2026-9999" for group in payload["groups"] for item in group["items"])
    assert any(item["reference"] == "JC-2026-0001" for group in payload["groups"] for item in group["items"])


@pytest.mark.asyncio
async def test_global_search_supports_partial_and_exact_matches(async_client: AsyncClient, db, seed_user_a, seed_department_a):
    job = JobCard(
        id=uuid.uuid4(),
        title="Crusher lubrication review",
        description="Confined to the crusher area",
        status="IN_PROGRESS",
        priority=3,
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-0042",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
    )
    db.add(job)
    await db.commit()

    headers = {"Authorization": f"Bearer {pytest.importorskip('app.core.security').create_access_token(subject=str(seed_user_a.id))}"}
    partial = await async_client.get("/api/v1/search?q=crusher", headers=headers)
    exact = await async_client.get("/api/v1/search?q=JC-2026-0042", headers=headers)

    assert partial.status_code == 200
    assert exact.status_code == 200
    partial_items = [item for group in partial.json()["groups"] for item in group["items"]]
    exact_items = [item for group in exact.json()["groups"] for item in group["items"]]
    assert any(item["reference"] == "JC-2026-0042" for item in partial_items)
    assert any(item["reference"] == "JC-2026-0042" for item in exact_items)


@pytest.mark.asyncio
async def test_global_search_includes_reference_numbers_and_asset_tags(async_client: AsyncClient, db, seed_user_a, seed_department_a):
    asset = Asset(
        id=uuid.uuid4(),
        asset_tag="AST-2026-0007",
        name="Primary Crusher Motor",
        asset_type="MACHINE",
        department_id=seed_department_a.id,
        status="IN_USE",
        criticality="HIGH",
        category="Crushing",
    )
    req = OperationalRequest(
        id=uuid.uuid4(),
        request_number="RQ-2026-0011",
        title="Motor replacement",
        purpose="Replace the motor assembly",
        requester_id=seed_user_a.id,
        department_id=seed_department_a.id,
        status="APPROVED",
        fulfillment_status="UNALLOCATED",
        priority=2,
        request_type="MACHINE_REQUEST",
    )
    db.add_all([asset, req])
    await db.commit()

    headers = {"Authorization": f"Bearer {pytest.importorskip('app.core.security').create_access_token(subject=str(seed_user_a.id))}"}
    response = await async_client.get("/api/v1/search?q=AST-2026-0007 OR RQ-2026-0011", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    items = [item for group in payload["groups"] for item in group["items"]]
    refs = {item["reference"] for item in items}
    assert "AST-2026-0007" in refs
    assert "RQ-2026-0011" in refs


@pytest.mark.asyncio
async def test_global_search_excludes_archived_and_deleted_records(async_client: AsyncClient, db, seed_user_a, seed_department_a):
    deleted_job = JobCard(
        id=uuid.uuid4(),
        title="Archived shutdown",
        description="Archived content should not be visible",
        status="CANCELLED",
        priority=1,
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-0177",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
        is_deleted=True,
    )
    active_job = JobCard(
        id=uuid.uuid4(),
        title="Live shutdown",
        description="Current content",
        status="ASSIGNED",
        priority=1,
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-0178",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
    )
    asset = Asset(
        id=uuid.uuid4(),
        asset_tag="AST-2026-0999",
        name="Archived conveyor",
        asset_type="MACHINE",
        department_id=seed_department_a.id,
        status="IN_USE",
        criticality="MEDIUM",
        category="Materials",
        is_archived=True,
    )
    db.add_all([deleted_job, active_job, asset])
    await db.commit()

    headers = {"Authorization": f"Bearer {pytest.importorskip('app.core.security').create_access_token(subject=str(seed_user_a.id))}"}
    response = await async_client.get("/api/v1/search?q=shutdown", headers=headers)
    assert response.status_code == 200
    items = [item for group in response.json()["groups"] for item in group["items"]]
    refs = {item["reference"] for item in items}
    assert "JC-2026-0178" in refs
    assert "JC-2026-0177" not in refs
