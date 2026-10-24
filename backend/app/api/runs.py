import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.run import Run
from app.schemas import RunCreate, RunOut, ExecuteRequest
from app.services.celesto_runner import execute_in_sandbox
from app.services.safety import validate_command
from app.services.audit import log_command

router = APIRouter(prefix="/api")


@router.get("/runs", response_model=list[RunOut])
def list_runs(state: str | None = None, db: Session = Depends(get_db)):
    try:
        q = select(Run).order_by(Run.created_at.desc())
        if state:
            q = q.where(Run.state == state)
        return list(db.scalars(q))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")


@router.post("/runs", response_model=RunOut, status_code=201)
def create_run(body: RunCreate, db: Session = Depends(get_db)):
    run = Run(**body.model_dump())
    try:
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="run_id or sandbox_name already exists",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="database error")


@router.post("/runs/execute", response_model=RunOut, status_code=201)
def execute_run(body: ExecuteRequest, db: Session = Depends(get_db)):
    # Audit every requested command, including commands blocked by policy.
    decision = validate_command(body.command, body.timeout)
    log_command(
        sandbox_name=body.sandbox_name,
        command=body.command,
        decision="allow" if decision.allow else "block",
    )

    # Never execute a command rejected by the safety policy.
    if not decision.allow:
        raise HTTPException(
            status_code=400,
            detail=f"Blocked by safety policy: {decision.reason}",
        )

    now = datetime.now(timezone.utc)

    run = Run(
        run_id=body.run_id,
        sandbox_name=body.sandbox_name,
        problem_id=body.problem_id,
        state="running",
        execution_target="celesto_sandbox",
        task_description=body.command,
        started_at=now,
    )

    # Persist the attempt before contacting Celesto.
    try:
        db.add(run)
        db.commit()
        db.refresh(run)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="run_id or sandbox_name already exists",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="database error")

    result = execute_in_sandbox(body.command, body.timeout)

    run.state = result["state"]
    run.ended_at = datetime.now(timezone.utc)
    run.wall_clock_s = result["wall_clock_s"]
    run.cleanup_status = result["cleanup_status"]
    run.error_details = result["error_details"]

    # Preserve actual command output and exit code in the existing summary field.
    run.result_summary = json.dumps(
        {
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }
    )

    try:
        db.commit()
        db.refresh(run)
        return run
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="execution finished, but saving its result failed",
        )