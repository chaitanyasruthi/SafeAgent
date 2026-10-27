
"""Execute safety-approved commands in ephemeral Celesto cloud sandboxes."""

import os
import time

from celesto import Computer

from app.services.safety import redact, truncate_output, validate_command


def execute_in_sandbox(command: str, timeout: int = 30) -> dict:
    """Execute an approved command and report execution and cleanup outcomes."""

    decision = validate_command(command, timeout)
    if not decision.allow:
        return {
            "state": "failed",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_details": f"Blocked by safety policy: {decision.reason}",
            "wall_clock_s": 0.0,
            "cleanup_status": "not_started",
        }

    if not os.environ.get("CELESTO_API_KEY"):
        return {
            "state": "failed",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error_details": "CELESTO_API_KEY is not configured",
            "wall_clock_s": 0.0,
            "cleanup_status": "not_started",
        }

    started = time.monotonic()
    stdout = ""
    stderr = ""
    exit_code = None
    error_details = None
    cleanup_status = "not_started"
    state = "failed"
    computer = None
    entered = False

    try:
        computer = Computer(
            provider="cloud",
            vcpus=1,
            ram_mb=2048,
            disk_size_mb=20480,
        )
        computer.__enter__()
        entered = True
        cleanup_status = "pending"

        result = computer.run(command, timeout=timeout)
        exit_code = result.exit_code
        stdout = truncate_output(redact(result.stdout or ""))
        stderr = truncate_output(redact(result.stderr or ""))
        state = "succeeded" if exit_code == 0 else "failed"

    except Exception as exc:
        message = redact(" ".join(str(exc).split()))
        message = message[:500] if message else "No provider error message"

        diagnostic_parts = [
            f"Celesto execution error: {type(exc).__name__}: {message}"
        ]

        for field in (
            "status_code",
            "code",
            "operation",
            "request_id",
            "recovery_action",
            "side_effects",
            "running_limit",
            "validation_errors",
        ):
            value = getattr(exc, field, None)
            if value is not None:
                safe_value = redact(str(value))[:200]
                diagnostic_parts.append(f"{field}={safe_value}")

        error_details = "; ".join(diagnostic_parts)
        state = "failed"

    except BaseException:
        # Preserve interruption semantics while attempting cleanup.
        state = "interrupted"
        error_details = "Execution interrupted"

        if entered and computer is not None:
            try:
                computer.__exit__(None, None, None)
                cleanup_status = "cleanup_requested"
            except Exception as cleanup_exc:
                cleanup_status = "failed"
                error_details += (
                    f"; cleanup error: {type(cleanup_exc).__name__}"
                )
        raise

    finally:
        if entered and computer is not None and cleanup_status == "pending":
            try:
                computer.__exit__(None, None, None)
                cleanup_status = "cleanup_requested"
            except Exception as cleanup_exc:
                cleanup_status = "failed"
                cleanup_error = (
                    f"Celesto cleanup error: {type(cleanup_exc).__name__}"
                )
                error_details = (
                    f"{error_details}; {cleanup_error}"
                    if error_details
                    else cleanup_error
                )
                state = "failed"

    return {
        "state": state,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "error_details": error_details,
        "wall_clock_s": round(time.monotonic() - started, 3),
        "cleanup_status": cleanup_status,
    }

