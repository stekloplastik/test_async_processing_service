import time
import uuid

import httpx

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"X-API-Key": "secret_api_key_123", "Content-Type": "application/json"}


def test_auth_failure():
    response = httpx.post(
        f"{API_URL}/payments",
        headers={"X-API-Key": "invalid_key", "Idempotency-Key": str(uuid.uuid4())},
        json={
            "amount": 100.0,
            "currency": "USD",
            "description": "Test",
            "metadata": {},
            "webhook_url": "http://localhost:8000/api/v1/webhook-receiver",
        },
    )
    assert response.status_code == 401


def test_payment_creation_and_idempotency():
    idem_key = str(uuid.uuid4())
    payload = {
        "amount": 150.0,
        "currency": "USD",
        "description": "Idempotency Test",
        "metadata": {"user_id": 42},
        "webhook_url": "http://api:8000/api/v1/webhook-receiver",
    }

    response = httpx.post(f"{API_URL}/payments", headers={**HEADERS, "Idempotency-Key": idem_key}, json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "payment_id" in data
    assert data["status"] == "pending"
    payment_id = data["payment_id"]

    response2 = httpx.post(f"{API_URL}/payments", headers={**HEADERS, "Idempotency-Key": idem_key}, json=payload)
    assert response2.status_code == 202
    assert response2.json()["payment_id"] == payment_id

    payload_diff = payload.copy()
    payload_diff["amount"] = 200.0
    response3 = httpx.post(f"{API_URL}/payments", headers={**HEADERS, "Idempotency-Key": idem_key}, json=payload_diff)
    assert response3.status_code == 409


def test_payment_processing_flow():
    idem_key = str(uuid.uuid4())
    payload = {
        "amount": 50.0,
        "currency": "EUR",
        "description": "Processing Flow Test",
        "metadata": {},
        "webhook_url": "http://api:8000/api/v1/webhook-receiver",
    }

    response = httpx.post(f"{API_URL}/payments", headers={**HEADERS, "Idempotency-Key": idem_key}, json=payload)
    assert response.status_code == 202
    payment_id = response.json()["payment_id"]

    status = "pending"
    for _ in range(10):
        time.sleep(1)
        get_resp = httpx.get(f"{API_URL}/payments/{payment_id}", headers=HEADERS)
        assert get_resp.status_code == 200
        status = get_resp.json()["status"]
        if status in ["succeeded", "failed"]:
            break

    assert status in ["succeeded", "failed"]


def test_dlq_routing():
    initial_deliver = 0
    try:
        mq_resp = httpx.get("http://localhost:15672/api/queues/%2F/payments.new.dlq", auth=("guest", "guest"))
        if mq_resp.status_code == 200:
            initial_deliver = mq_resp.json().get("message_stats", {}).get("deliver", 0)
    except Exception:
        pass

    idem_key = str(uuid.uuid4())
    payload = {
        "amount": 99.99,
        "currency": "RUB",
        "description": "DLQ Test",
        "metadata": {},
        "webhook_url": "http://localhost:9999/fail",
    }

    response = httpx.post(f"{API_URL}/payments", headers={**HEADERS, "Idempotency-Key": idem_key}, json=payload)
    assert response.status_code == 202

    dlq_received_message = False
    for _ in range(40):
        time.sleep(1)
        try:
            mq_resp = httpx.get("http://localhost:15672/api/queues/%2F/payments.new.dlq", auth=("guest", "guest"))
            if mq_resp.status_code == 200:
                q_data = mq_resp.json()
                current_deliver = q_data.get("message_stats", {}).get("deliver", 0)
                if q_data.get("messages", 0) > 0 or current_deliver > initial_deliver:
                    dlq_received_message = True
                    break
        except Exception:
            pass

    assert dlq_received_message is True


def test_validation_errors():
    response = httpx.post(
        f"{API_URL}/payments",
        headers={**HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        json={"amount": -10.0, "currency": "USD", "webhook_url": "http://api:8000/api/v1/webhook-receiver"},
    )
    assert response.status_code == 422

    response = httpx.post(
        f"{API_URL}/payments",
        headers={**HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        json={"amount": 100.0, "currency": "GBP", "webhook_url": "http://api:8000/api/v1/webhook-receiver"},
    )
    assert response.status_code == 422

    response = httpx.post(
        f"{API_URL}/payments",
        headers={**HEADERS, "Idempotency-Key": str(uuid.uuid4())},
        json={"amount": 100.0, "currency": "USD", "webhook_url": "ftp://invalid-scheme"},
    )
    assert response.status_code == 422

    response = httpx.post(
        f"{API_URL}/payments",
        headers={"X-API-Key": "secret_api_key_123"},
        json={"amount": 100.0, "currency": "USD", "webhook_url": "http://api:8000/api/v1/webhook-receiver"},
    )
    assert response.status_code == 422


def test_payment_not_found():
    response = httpx.get(f"{API_URL}/payments/{uuid.uuid4()}", headers=HEADERS)
    assert response.status_code == 404

    response = httpx.get(f"{API_URL}/payments/not-a-valid-uuid", headers=HEADERS)
    assert response.status_code == 422
