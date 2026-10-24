import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import Base, engine
from app.models import run as _run  # noqa: F401  (register model)
from app.api import runs, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # no-op if seeds/01_runs.sql already created it
    yield


app = FastAPI(title="SafeAgent Run Ledger", version="0.1.0", lifespan=lifespan)

origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
async def validation_to_400(request: Request, exc: RequestValidationError):
    # Assignment requires HTTP 400 (not FastAPI's default 422) for invalid input.
    msgs = [f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": msgs})


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(runs.router)
app.include_router(reports.router)
