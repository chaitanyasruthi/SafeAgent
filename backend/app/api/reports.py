import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api")
REPORTS = Path("/app/reports")
ALLOWED = {"problem", "capabilities", "lifecycle", "reliability", "containment",
           "failure_policy", "concurrency"}


@router.get("/reports/{name}")
def get_report(name: str):
    """Serve a report file that was produced by a real run. 404 if not yet produced."""
    if name not in ALLOWED:
        raise HTTPException(status_code=404, detail="unknown report")
    path = REPORTS / f"{name}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="report not generated yet")
    return json.loads(path.read_text(encoding="utf-8"))
