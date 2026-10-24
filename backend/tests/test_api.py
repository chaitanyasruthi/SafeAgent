import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine

Base.metadata.drop_all(engine)
client = TestClient(app)
GOOD = {"run_id": "r1", "sandbox_name": "sbx-abcd1234", "problem_id": "csv",
        "state": "created", "execution_target": "celesto_sandbox"}


def test_health():
    with TestClient(app) as c:
        r = c.get("/health")
        assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_create_and_list():
    with TestClient(app) as c:
        assert c.post("/api/runs", json=GOOD).status_code == 201
        names = [x["sandbox_name"] for x in c.get("/api/runs").json()]
        assert "sbx-abcd1234" in names


def test_duplicate_conflict():
    with TestClient(app) as c:
        assert c.post("/api/runs", json=GOOD).status_code == 409


def test_bad_target_400():
    with TestClient(app) as c:
        assert c.post("/api/runs", json={**GOOD, "run_id": "r2", "sandbox_name": "sbx-zzzz9999", "execution_target": "host"}).status_code == 400


def test_bad_state_400():
    with TestClient(app) as c:
        assert c.post("/api/runs", json={**GOOD, "run_id": "r3", "sandbox_name": "sbx-yyyy9999", "state": "bogus"}).status_code == 400


def test_bad_name_400():
    with TestClient(app) as c:
        for bad in ["sbx-SHORT", "sbx-abc", "box-abcd1234", "sbx-ABCD1234"]:
            assert c.post("/api/runs", json={**GOOD, "run_id": "r4", "sandbox_name": bad}).status_code == 400


def test_missing_field_400():
    with TestClient(app) as c:
        assert c.post("/api/runs", json={"run_id": "x"}).status_code == 400
