import pytest

from app.services.recovery import recover_from_step_failure


def test_step_7_failure_pauses_without_retry():
    result = recover_from_step_failure(
        total_steps=10,
        failed_step=7,
        completed_steps=6,
    )

    assert result.state == "paused"
    assert result.completed_steps == 6
    assert result.next_step == 7
    assert result.retry_allowed is False


def test_retryable_failure_retries_only_failed_step():
    result = recover_from_step_failure(
        total_steps=10,
        failed_step=7,
        completed_steps=6,
        retryable=True,
    )

    assert result.state == "retry_pending"
    assert result.completed_steps == 6
    assert result.next_step == 7
    assert result.retry_allowed is True


def test_invalid_failed_step_is_rejected():
    with pytest.raises(ValueError):
        recover_from_step_failure(
            total_steps=10,
            failed_step=11,
            completed_steps=10,
        )
