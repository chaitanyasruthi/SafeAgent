import os
from unittest.mock import patch

from app.services.celesto_runner import execute_in_sandbox


@patch.dict(os.environ, {"CELESTO_API_KEY": "dummy-test-key"})
@patch("app.services.celesto_runner.Computer")
def test_provider_error_redacts_credentials(mock_computer):
    mock_computer.side_effect = RuntimeError(
        "Provider failed: CELESTO_API_KEY=example-secret-value"
    )

    result = execute_in_sandbox("echo safe-test", timeout=10)

    assert result["state"] == "failed"
    assert result["exit_code"] is None
    assert "[REDACTED]" in result["error_details"]
    assert "example-secret-value" not in result["error_details"]
    assert result["cleanup_status"] == "not_started"
    mock_computer.assert_called_once()


@patch.dict(os.environ, {"CELESTO_API_KEY": "dummy-test-key"})
@patch("app.services.celesto_runner.Computer")
def test_provider_error_preserves_useful_diagnostic(mock_computer):
    mock_computer.side_effect = RuntimeError(
        "HTTP 429: provider temporarily unavailable"
    )

    result = execute_in_sandbox("echo safe-test", timeout=10)

    assert result["state"] == "failed"
    assert "RuntimeError" in result["error_details"]
    assert "HTTP 429" in result["error_details"]
    assert "temporarily unavailable" in result["error_details"]
    assert result["cleanup_status"] == "not_started"
    mock_computer.assert_called_once()
