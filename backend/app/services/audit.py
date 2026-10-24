import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_lock = Lock()


def log_command(sandbox_name: str, command: str, decision: str) -> None:
    """Append an audit record for every requested command."""
    project_root = Path(__file__).resolve().parents[3]
    default_path = project_root / "logs" / "commands.jsonl"
    log_path = Path(os.environ.get("COMMAND_LOG_PATH", str(default_path)))

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "sandbox_name": sandbox_name,
        "command": command,
        "decision": decision,
        "execution_target": "celesto_sandbox",
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record) + "\n")
