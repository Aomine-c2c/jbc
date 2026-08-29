import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_storage_upload_and_download(async_client: AsyncClient, token_user_a):
    file_content = b"Sample industrial maintenance attachment report"
    files = {"file": ("inspection_report.txt", io.BytesIO(file_content), "text/plain")}
    data = {"category": "reports"}

    # Upload
    headers = {"Authorization": f"Bearer {token_user_a}"}
    upload_res = await async_client.post("/api/v1/storage/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert "file" in upload_data
    stored_filename = upload_data["file"]["stored_filename"]
    assert stored_filename.endswith("inspection_report.txt")

    # Download
    download_res = await async_client.get(f"/api/v1/storage/download/reports/{stored_filename}", headers=headers)
    assert download_res.status_code == 200
    assert download_res.content == file_content

    # Delete
    delete_res = await async_client.delete(f"/api/v1/storage/reports/{stored_filename}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_storage_invalid_category(async_client: AsyncClient, token_user_a):
    files = {"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    data = {"category": "invalid_cat"}
    res = await async_client.post(
        "/api/v1/storage/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_storage_requires_authentication(async_client: AsyncClient):
    files = {"file": ("test.txt", io.BytesIO(b"data"), "text/plain")}
    res = await async_client.post("/api/v1/storage/upload", files=files, data={"category": "reports"})
    assert res.status_code == 401
