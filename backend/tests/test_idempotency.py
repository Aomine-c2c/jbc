import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_idempotency_middleware_prevents_duplicate_creation(async_client: AsyncClient, admin_headers: dict):
    idempotency_key = str(uuid.uuid4())
    headers = {
        **admin_headers,
        "X-Idempotency-Key": idempotency_key,
    }

    payload = {
        "note": "Idempotent Backup Test",
        "include_storage": True,
    }

    # 1. First execution
    res1 = await async_client.post("/api/v1/platform/backups/create", headers=headers, json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "created"
    assert "filename" in data1
    assert "X-Idempotency-Replay" not in res1.headers or res1.headers.get("X-Idempotency-Replay") != "true"

    # 2. Second execution with identical X-Idempotency-Key
    res2 = await async_client.post("/api/v1/platform/backups/create", headers=headers, json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["filename"] == data1["filename"]  # Identical response payload
    assert res2.headers.get("X-Idempotency-Replay") == "true"
    assert res2.headers.get("X-Idempotency-Key") == idempotency_key

    # 3. Third execution with different X-Idempotency-Key
    new_key = str(uuid.uuid4())
    headers_new = {
        **admin_headers,
        "X-Idempotency-Key": new_key,
    }
    res3 = await async_client.post("/api/v1/platform/backups/create", headers=headers_new, json=payload)
    assert res3.status_code == 200
    data3 = res3.json()
    assert res3.headers.get("X-Idempotency-Replay") is None
