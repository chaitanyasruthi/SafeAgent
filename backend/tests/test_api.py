import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient

from app.main import app
from app.db import Base, engine


TOKEN = os.environ.get(
    "SAFEAGENT_API_TOKEN",
    "safeagent-local-test-token",
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
}

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

client = TestClient(app)

GOOD = {
    "run_id": "r1",
    "sandbox_name": "sbx-abcd1234",
    "problem_id": "csv",
    "state": "created",
    "execution_target": "celesto_sandbox",
}


def test_health():
    with TestClient(app) as c:
        response = c.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_create_and_list():
    with TestClient(app) as c:
        response = c.post(
            "/api/runs",
            json=GOOD,
            headers=HEADERS,
        )

        assert response.status_code == 201

        response = c.get(
            "/api/runs",
            headers=HEADERS,
        )

        assert response.status_code == 200

        names = [
            item["sandbox_name"]
            for item in response.json()
        ]

        assert "sbx-abcd1234" in names


def test_duplicate_conflict():
    with TestClient(app) as c:
        first = c.post(
            "/api/runs",
            json=GOOD,
            headers=HEADERS,
        )

        assert first.status_code in (201, 409)

        duplicate = c.post(
            "/api/runs",
            json=GOOD,
            headers=HEADERS,
        )

        assert duplicate.status_code == 409


def test_bad_target_400():
    with TestClient(app) as c:
        response = c.post(
            "/api/runs",
            json={
                **GOOD,
                "run_id": "r2",
                "sandbox_name": "sbx-zzzz9999",
                "execution_target": "host",
            },
            headers=HEADERS,
        )

        assert response.status_code == 400


def test_bad_state_400():
    with TestClient(app) as c:
        response = c.post(
            "/api/runs",
            json={
                **GOOD,
                "run_id": "r3",
                "sandbox_name": "sbx-yyyy9999",
                "state": "bogus",
            },
            headers=HEADERS,
        )

        assert response.status_code == 400


def test_bad_name_400():
    with TestClient(app) as c:
        for index, bad_name in enumerate(
            ["sbx-SHORT", "sbx-abc", "box-abcd1234", "sbx-ABCD1234"],
            start=1,
        ):
            response = c.post(
                "/api/runs",
                json={
                    **GOOD,
                    "run_id": f"bad-name-{index}",
                    "sandbox_name": bad_name,
                },
                headers=HEADERS,
            )

            assert response.status_code == 400


def test_missing_field_400():
    with TestClient(app) as c:
        response = c.post(
            "/api/runs",
            json={"run_id": "x"},
            headers=HEADERS,
        )

        assert response.status_code == 400


def test_missing_token_is_rejected():
    with TestClient(app) as c:
        response = c.get("/api/runs")

        assert response.status_code == 401
