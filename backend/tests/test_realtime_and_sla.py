import pytest
import uuid
import io
import csv

from app.core.events import EventBroker
from app.modules.notifications.push import push_manager, PushNotificationMessage
from app.modules.notifications.worker import DEPARTMENT_SLA_HOURS


@pytest.mark.asyncio
async def test_event_broker_pub_sub():
    broker = EventBroker()
    sub_id, queue = await broker.register_subscriber(user_id="user-123", department_id="dept-1", is_admin=False)
    
    assert queue.qsize() == 0
    
    # Publish matching event
    event = await broker.publish(
        event_type="job_card.created",
        payload={"title": "Fix Crusher Belt"},
        department_id="dept-1",
        channel="jobs"
    )
    
    assert event.event_type == "job_card.created"
    assert queue.qsize() == 1
    
    msg = queue.get_nowait()
    assert msg.event_type == "job_card.created"
    assert msg.payload["title"] == "Fix Crusher Belt"
    assert "event: job_card.created" in msg.to_sse_message()
    
    await broker.remove_subscriber(sub_id)


@pytest.mark.asyncio
async def test_web_push_manager():
    user_id = str(uuid.uuid4())
    payload = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
        "keys": {"p256dh": "dummy-p256dh-key", "auth": "dummy-auth-key"},
    }
    
    sub = push_manager.add_subscription(user_id, payload)
    assert sub["endpoint"] == payload["endpoint"]
    assert len(push_manager.list_user_subscriptions(user_id)) == 1
    
    # Send test push notification
    dispatched = await push_manager.send_push_notification(
        user_id=user_id,
        message=PushNotificationMessage(
            title="Urgent Approval Required",
            body="Job Card JC-2026-001 requires approval",
            url="/approvals"
        )
    )
    assert dispatched == 1
    
    # Unsubscribe
    removed = push_manager.remove_subscription(user_id, payload["endpoint"])
    assert removed is True
    assert len(push_manager.list_user_subscriptions(user_id)) == 0


@pytest.mark.asyncio
async def test_push_api_endpoints(async_client, admin_headers):
    # 1. Get VAPID Public Key
    res = await async_client.get("/api/v1/notifications/push/vapid-public-key")
    assert res.status_code == 200
    assert "vapid_public_key" in res.json()
    
    # 2. Subscribe endpoint
    sub_payload = {
        "endpoint": "https://push.example.com/sub/test-client",
        "keys": {"p256dh": "test-key", "auth": "test-auth"},
        "user_agent": "Mozilla/5.0 TestBrowser",
    }
    sub_res = await async_client.post("/api/v1/notifications/push/subscribe", json=sub_payload, headers=admin_headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "subscribed"
    
    # 3. Test push notification trigger
    test_res = await async_client.post("/api/v1/notifications/push/test", headers=admin_headers)
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "dispatched"


@pytest.mark.asyncio
async def test_department_sla_configuration():
    assert "Safety" in DEPARTMENT_SLA_HOURS
    assert DEPARTMENT_SLA_HOURS["Safety"] == 1
    assert DEPARTMENT_SLA_HOURS["Instrumentation"] == 2
    assert DEPARTMENT_SLA_HOURS["Mechanical"] == 8
    assert DEPARTMENT_SLA_HOURS["IT"] == 24


@pytest.mark.asyncio
async def test_operational_export_job_cards(async_client, admin_headers):
    res = await async_client.get("/api/v1/export/job-cards", headers=admin_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=dwrms_job_cards_" in res.headers["content-disposition"]
    
    csv_text = res.text
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 1
    headers_row = rows[0]
    assert "Job Number" in headers_row
    assert "Estimated Cost (USD)" in headers_row
    assert "Cost Variance (USD)" in headers_row


@pytest.mark.asyncio
async def test_operational_export_audit_logs(async_client, admin_headers):
    res = await async_client.get("/api/v1/export/audit-logs", headers=admin_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=dwrms_audit_trail_" in res.headers["content-disposition"]
    
    csv_text = res.text
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 1
    assert "Log ID" in rows[0]
    assert "Actor Name" in rows[0]
