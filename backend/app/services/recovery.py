"""Local, deterministic recovery policy for multi-step tasks."""

from dataclasses import dataclass


@dataclass
class RecoveryResult:
    state: str
    completed_steps: int
    next_step: int
    retry_allowed: bool
    message: str


def recover_from_step_failure(
    total_steps: int,
    failed_step: int,
    completed_steps: int,
    retryable: bool = False,
) -> RecoveryResult:
    """Resume from the failed step without repeating completed steps."""

    if total_steps < 1:
        raise ValueError("total_steps must be at least 1")

    if not 1 <= failed_step <= total_steps:
        raise ValueError("failed_step is outside the task range")

    if not 0 <= completed_steps < total_steps:
        raise ValueError("completed_steps is outside the valid range")

    if completed_steps != failed_step - 1:
        raise ValueError("completed_steps must precede failed_step")

    if retryable:
        return RecoveryResult(
            state="retry_pending",
            completed_steps=completed_steps,
            next_step=failed_step,
            retry_allowed=True,
            message="Retry the failed step only after confirming it is safe.",
        )

    return RecoveryResult(
        state="paused",
        completed_steps=completed_steps,
        next_step=failed_step,
        retry_allowed=False,
        message="Task paused; investigate the failure before resuming.",
    )
