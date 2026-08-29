import pytest
from httpx import AsyncClient
from click.testing import CliRunner

from app.core.remote_connectivity import remote_connectivity_manager, RemoteConnectivityManager
from app.cli.main import ops_group


def test_remote_connectivity_manager_defaults():
    mgr = RemoteConnectivityManager()
    status = mgr.get_remote_network_status()

    assert "deployment_mode" in status
    assert "status" in status
    assert "provider" in status
    assert "security_model" in status
    assert status["security_model"]["layer_type"] == "Transport Layer Only"
    assert status["security_model"]["application_auth"] == "JWT Enforced"
    assert status["security_model"]["rbac"] == "Capabilities Enforced"

    # Guarantees zero secret leaks
    assert "secret" not in status
    assert "auth_key" not in status
    assert "token" not in status


@pytest.mark.asyncio
async def test_api_platform_remote_network_endpoint(async_client: AsyncClient, admin_headers: dict):
    # 1. Test dedicated /remote-network endpoint
    res = await async_client.get("/api/v1/platform/remote-network", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "deployment_mode" in data
    assert "status" in data
    assert "provider" in data
    assert "security_model" in data

    # 2. Test status endpoint integration
    status_res = await async_client.get("/api/v1/platform/status", headers=admin_headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "remote_network" in status_data["subsystems"]
    assert status_data["subsystems"]["remote_network"]["security_model"]["application_auth"] == "JWT Enforced"


def test_cli_network_shows_remote_transport():
    runner = CliRunner()
    result = runner.invoke(ops_group, ["network"])
    assert result.exit_code == 0
    assert "Secure Remote Transport Layer" in result.output
    assert "Deployment Mode" in result.output
    assert "Remote Transport Status" in result.output
