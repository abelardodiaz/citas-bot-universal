"""GET /webhook handshake tests."""

from fastapi.testclient import TestClient


def test_verify_returns_challenge_when_token_matches(client: TestClient) -> None:
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "1234567890",
            "hub.verify_token": "test-token-abc",
        },
    )
    assert response.status_code == 200
    assert response.text == "1234567890"
    assert response.headers["content-type"].startswith("text/plain")


def test_verify_403_when_token_mismatch(client: TestClient) -> None:
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "1234567890",
            "hub.verify_token": "wrong-token",
        },
    )
    assert response.status_code == 403


def test_verify_403_when_mode_invalid(client: TestClient) -> None:
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "invalid",
            "hub.challenge": "1234567890",
            "hub.verify_token": "test-token-abc",
        },
    )
    assert response.status_code == 403


def test_verify_400_when_no_challenge(client: TestClient) -> None:
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-token-abc",
        },
    )
    assert response.status_code == 400


def test_verify_403_when_no_token(client: TestClient) -> None:
    response = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.challenge": "x"},
    )
    assert response.status_code == 403
