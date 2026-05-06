"""POST /webhook signature validation tests."""

from __future__ import annotations

import hmac
import json
from hashlib import sha256

from fastapi.testclient import TestClient

VALID_SECRET = "test-secret-xyz"
SAMPLE_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "1234567890",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "5215555555555"},
                        "messages": [
                            {
                                "from": "5215551234567",
                                "id": "wamid.HBgN...",
                                "timestamp": "1700000000",
                                "text": {"body": "hola"},
                                "type": "text",
                            }
                        ],
                    },
                }
            ],
        }
    ],
}


def _sign(body: bytes, secret: str = VALID_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, sha256).hexdigest()


def test_receive_200_with_valid_signature(client: TestClient) -> None:
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": _sign(body), "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_receive_401_without_signature_header(client: TestClient) -> None:
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_receive_401_with_invalid_signature(client: TestClient) -> None:
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    bad_sig = "sha256=" + "0" * 64
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": bad_sig, "Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_receive_401_with_signature_from_wrong_secret(client: TestClient) -> None:
    body = json.dumps(SAMPLE_PAYLOAD).encode()
    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, secret="wrong-secret"),
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_receive_200_but_ignored_when_payload_unparseable(client: TestClient) -> None:
    body = b"this is not json"
    response = client.post(
        "/webhook",
        content=body,
        headers={"X-Hub-Signature-256": _sign(body), "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}
