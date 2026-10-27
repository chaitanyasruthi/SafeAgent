import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


TOKEN = os.environ.get(
    "SAFEAGENT_API_TOKEN",
    "safeagent-local-test-token",
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
}

client = TestClient(app)


def test_unsafe_command_is_rejected():
    response = client.post(
        "/api/runs/execute",
        json={
            "run_id": "unsafe-test-001",
            "sandbox_name": "sbx-unsafe1234",
            "problem_id": "safety-test",
            "command": "rm -rf /",
            "timeout": 10,
        },
        headers=HEADERS,
    )

    assert response.status_code == 400
    assert "Blocked by safety policy" in response.json()["detail"]


@patch("app.api.runs.execute_in_sandbox")
def test_allowed_command_saves_successful_run(mock_execute):
    mock_execute.return_value = {
        "state": "succeeded",
        "exit_code": 0,
        "stdout": "SafeAgent-test",
        "stderr": "",
        "error_details": None,
        "wall_clock_s": 0.2,
        "cleanup_status": "deleted",
    }

    response = client.post(
        "/api/runs/execute",
        json={
            "run_id": "mock-success-20261022-01",
            "sandbox_name": "sbx-mock2026102201",
            "problem_id": "safety-test",
            "command": "echo SafeAgent-test",
            "timeout": 10,
        },
        headers=HEADERS,
    )

    assert response.status_code == 201
    assert response.json()["state"] == "succeeded"
    assert response.json()["cleanup_status"] == "deleted"

    mock_execute.assert_called_once()
