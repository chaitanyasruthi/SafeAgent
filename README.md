# SafeAgent: Secure AI Agent with Sandbox Isolation and Failure Recovery

**SafeAgent** is a security-focused command-execution platform designed to help AI agents execute approved commands in isolated environments. It validates commands against a safety policy, records allow/block decisions, routes approved commands to Celesto cloud sandboxes, and stores execution outcomes in a PostgreSQL ledger.

> **Project status:** Local API, PostgreSQL health checks, safety-policy behavior, and backend tests have been verified. Successful Celesto cloud execution, the 20-run reliability benchmark, and the five-job concurrency test remain unverified because a cloud execution attempt returned HTTP 429.

---

## Table of Contents

1. [Problem statement](#problem-statement)
2. [Solution](#solution)
3. [Key features](#key-features)
4. [How I used Celesto](#how-i-used-celesto)
5. [Architecture](#architecture)
6. [Technology stack](#technology-stack)
7. [Project structure](#project-structure)
8. [Setup](#setup)
9. [API endpoints](#api-endpoints)
10. [Security and containment](#security-and-containment)
11. [State and failure design](#state-and-failure-design)
12. [Eval report](#eval-report)
13. [Known limitations](#known-limitations)
14. [Future improvements](#future-improvements)
15. [AI assistants used](#ai-assistants-used)

---

## Problem statement

AI agents can request commands that read files, modify data, install software, or interact with external systems. Executing these commands without appropriate controls can expose the host environment to destructive operations, unauthorized access, and sensitive-data leakage.

The problem is how to allow useful agent-requested command execution while enforcing safety checks, keeping an audit trail, isolating execution, and recording failures.

SafeAgent addresses this problem through a control layer that validates commands, blocks disallowed operations, logs decisions, requests execution through Celesto, and records execution outcomes in a PostgreSQL ledger.

### Target users

* Developers building AI agents.
* Teams experimenting with autonomous coding assistants.
* Engineers who need auditable command execution.
* Researchers investigating safer agent execution and recovery.

### Project goal

Provide a traceable command-execution workflow that separates local safety decisions from execution in an external sandbox environment.

---

## Solution

SafeAgent uses a FastAPI backend as the control plane.

When a command request arrives, the application:

1. Validates the command against its safety policy.
2. Records the allow/block decision in a JSONL audit log.
3. Rejects disallowed commands before invoking the sandbox runner.
4. Persists an approved execution attempt in PostgreSQL.
5. Requests command execution through the Celesto Python SDK.
6. Captures the result, output, error information, and cleanup status.
7. Updates the corresponding database record.

If the Celesto cloud API fails, SafeAgent records the execution failure instead of treating the attempt as successful.

**Current limitation:** A cloud execution attempt returned HTTP 429. The exact cause has not been established, so successful cloud execution and actual cloud-resource cleanup have not been verified.

---

## Key features

### 1. Command safety validation

The safety module checks requested commands against an allowlist and deny rules.

It is designed to reject dangerous operations before they reach the sandbox runner.

Example:

```bash
rm -rf /
```

This destructive command was rejected by the local safety policy.

### 2. Audit logging

SafeAgent records command requests and their policy decisions in:

```text
logs/commands.jsonl
```

Each record contains:

* `ts` — timestamp in ISO-8601 format.
* `sandbox_name` — requested sandbox identifier.
* `command` — requested command.
* `decision` — `allow` or `block`.
* `execution_target` — `celesto_sandbox`.

### 3. PostgreSQL execution ledger

The PostgreSQL ledger stores run information, including:

* Run identifier.
* Sandbox name.
* Problem identifier.
* Execution state.
* Requested execution target.
* Task description.
* Start and end timestamps.
* Execution duration, when available.
* Result summary.
* Error details.
* Cleanup status.

The project includes a seeded demonstration record. This record is sample data, not proof of a real sandbox execution.

### 4. Cloud sandbox execution

The execution layer uses the Celesto Python SDK to request cloud sandbox execution for commands that pass local validation.

Successful cloud execution has not yet been verified because the cloud API returned HTTP 429.

### 5. Failure handling

The execution layer handles ordinary execution exceptions and attempts cleanup after successfully entering the sandbox context.

The local recovery module also implements a deterministic policy for handling a failed step in a multi-step task.

Actual cloud cleanup and cloud-based recovery remain unverified.

### 6. Docker Compose deployment

The application and PostgreSQL ledger run as separate Docker Compose services.

The Compose configuration includes health checks and makes the API wait for PostgreSQL to become healthy.

---

## How I used Celesto

SafeAgent integrates Celesto through its Python SDK.

The intended execution flow is:

1. Receive a command request through FastAPI.
2. Validate the command locally.
3. Reject and audit commands that violate the safety policy.
4. Request an isolated cloud execution environment through Celesto.
5. Execute the approved command through the SDK.
6. Capture output and execution status.
7. Attempt sandbox cleanup and record the cleanup status.

The Celesto execution layer is implemented in:

```text
backend/app/services/celesto_runner.py
```

The API integration is implemented in:

```text
backend/app/api/runs.py
```

### Observed cloud execution issue

A real cloud execution attempt returned HTTP 429.

The available error did not establish the exact cause. Consequently, this project does not claim that the cloud execution workflow completed successfully, that cloud isolation was demonstrated, or that a sandbox was actually deleted.

The local API, command validation, audit logging, and backend tests can be evaluated independently of this unresolved cloud issue.

---

## Architecture

```text
                   Agent / Command Requester
                              |
                              v
                    +-------------------+
                    |    FastAPI API    |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | Safety Validation |
                    +-------------------+
                         /          \
                        /            \
                   BLOCK              ALLOW
                     |                  |
                     v                  v
              +-------------+   +----------------+
              | Audit Log   |   | Celesto SDK    |
              | JSONL       |   +----------------+
              +-------------+           |
                                        v
                              +--------------------+
                              | Celesto Cloud      |
                              | Sandbox             |
                              +--------------------+
                                        |
                                        v
                              +--------------------+
                              | Execution Result   |
                              | Output / Error     |
                              +--------------------+
                                        |
                              +---------+---------+
                              |                   |
                              v                   v
                       +-------------+    +---------------+
                       | PostgreSQL  |    | Audit Log     |
                       | Run Ledger  |    | JSONL         |
                       +-------------+    +---------------+
```

### Component responsibilities

| Component      | Responsibility                                                                |
| -------------- | ----------------------------------------------------------------------------- |
| FastAPI        | Receives requests and exposes the API                                         |
| Safety module  | Validates commands before execution                                           |
| Audit service  | Records allow/block decisions                                                 |
| Celesto runner | Requests cloud sandbox execution and attempts cleanup                         |
| PostgreSQL     | Stores run records and execution outcomes                                     |
| Docker Compose | Starts and connects the API and ledger services                               |
| Frontend       | Provides the project UI; verify the current frontend functionality separately |

The Celesto sandbox is requested through the SDK. It is **not** a Docker Compose service.

---

## Technology stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Celesto Python SDK

### Database

* PostgreSQL
* PostgreSQL health checks through `pg_isready`

### Deployment

* Docker
* Docker Compose

### Frontend

* React
* Vite
* Tailwind CSS
* Recharts

### Testing

* pytest
* FastAPI test client
* Safety-policy unit tests
* Recovery-policy unit tests
* Report validation tests

---

## Project structure

The main project layout is:

```text
SafeAgent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── runs.py
│   │   ├── services/
│   │   │   ├── audit.py
│   │   │   ├── celesto_runner.py
│   │   │   ├── recovery.py
│   │   │   └── safety.py
│   │   ├── db.py
│   │   ├── models/
│   │   └── schemas.py
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_execution_api.py
│   │   ├── test_recovery.py
│   │   └── test_safety.py
│   └── requirements.txt
├── frontend/
├── logs/
│   └── commands.jsonl
├── reports/
│   ├── problem.json
│   ├── capabilities.json
│   ├── lifecycle.json
│   ├── reliability.json
│   ├── containment.json
│   ├── concurrency.json
│   ├── failure_policy.json
│   ├── failure_trace.jsonl
│   ├── postmortem.md
│   └── evidence/
├── seeds/
├── tests/
│   └── test_reports.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Setup

### Prerequisites

Install or configure:

* Docker Desktop with Docker Compose.
* Python 3.12 or another version supported by the backend dependencies.
* A Celesto API key if you want to attempt cloud execution.
* Git, if you intend to version-control the project.

### 1. Configure environment variables

Create a local environment file from the template:

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholders with your own values.

The template includes configuration for:

```dotenv
CELESTO_PROVIDER=cloud
CELESTO_API_KEY=replace-me
CELESTO_BACKEND=firecracker
LLM_BASE_URL=https://example-llm-host/v1
LLM_API_KEY=replace-me
LLM_MODEL=replace-with-a-model-name
DATABASE_URL=postgresql://ledger:ledger@ledger:5432/ledger
API_PORT=8080
CORS_ORIGINS=http://localhost:5173
```

Use real credentials only in your local environment. Never commit `.env` or publish API keys.

### 2. Start the API and database

From the project root:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

Wait until both `api` and `ledger` report healthy status.

### 3. Verify the API

The API is exposed on host port `8081`.

Check health:

```bash
curl http://localhost:8081/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Retrieve run records:

```bash
curl http://localhost:8081/api/runs
```

The response should include the seeded demonstration record `sbx-seeddemo1` if the database has been initialized with the provided seed data.

**Note:** A seeded record is not evidence of an actual cloud execution.

### 4. Open API documentation

With the services running, open:

```text
http://localhost:8081/docs
```

This provides the FastAPI interactive API documentation.

### 5. Run backend tests

Activate your backend Python environment if needed, then run:

```bash
cd backend
python -m pytest -q tests/
```

The backend test suite previously completed with **20 passed and one deprecation warning**.

### 6. Validate evaluation reports

Return to the project root:

```bash
cd ..
python -m pytest -q tests/test_reports.py
```

This validator checks required report fields, evidence paths, JSONL records, reliability metrics, concurrency records, and README headings.

Some report checks remain incomplete until the required execution evidence has been collected.

### 7. Stop the services

When finished:

```bash
docker compose down
```

To remove the PostgreSQL data volume as well, use caution because this deletes persisted database data:

```bash
docker compose down -v
```

---

## API endpoints

### Health check

**Endpoint:** `GET /health`

Purpose: Check whether the API is responding.

Previously observed response:

```json
{
  "status": "ok"
}
```

### List runs

**Endpoint:** `GET /api/runs`

Purpose: Retrieve execution records from the PostgreSQL ledger.

Optional state filtering is supported by the API implementation.

Example:

```bash
curl http://localhost:8081/api/runs
```

### Create a run record

**Endpoint:** `POST /api/runs`

Purpose: Create a run record in the ledger.

The request must conform to the `RunCreate` schema defined by the backend.

### Execute a command

**Endpoint:** `POST /api/runs/execute`

Purpose: Validate and audit a command, then request sandbox execution if the command is approved.

The request must conform to the `ExecuteRequest` schema.

Commands rejected by the safety policy receive an HTTP 400 response before the execution runner is invoked.

Refer to the FastAPI documentation at `/docs` for the current request and response schemas.

---

## Containment test

### Local safety policy

SafeAgent validates commands before passing them to the Celesto execution layer.

A destructive command such as:

```bash
rm -rf /
```

was rejected by the local API policy.

The block decision was recorded in:

```text
logs/commands.jsonl
```

Supporting evidence is stored in:

```text
reports/evidence/containment.log
```

### What this test demonstrates

The observed test demonstrates that the local policy rejected the destructive command before calling the sandbox runner.

It does **not** demonstrate that the command ran inside a cloud guest and was contained there. Because the cloud execution issue remains unresolved, guest-level attack containment has not been verified.

### Security precautions

* Keep API keys outside version control.
* Validate commands before execution.
* Audit both allowed and blocked requests that pass request validation.
* Avoid claiming sandbox isolation without successful execution evidence.
* Treat command output as untrusted input.
* Verify cleanup outcomes rather than assuming that a cleanup request deleted a cloud resource.

---

## State and failure design

SafeAgent stores execution attempts and their results in the PostgreSQL ledger.

The runner distinguishes successful execution from failure and records error information when execution fails.

### Multi-step recovery scenario

The project includes a deterministic recovery function for a task containing ten steps when step seven fails.

The intended behavior is:

1. Preserve the six completed steps.
2. Identify step seven as the next step requiring attention.
3. Pause by default after a non-retryable failure.
4. Allow a retry to be considered only when the failure is explicitly classified as retryable.
5. Avoid automatically repeating already completed steps.

The recovery function has local unit tests.

The report `reports/failure_policy.json` documents the selected policy and the rationale. Actual recovery inside a successfully created Celesto cloud sandbox has not been verified.

---

## Eval report

### Verified results

| Evaluation item              | Observed result              |
| ---------------------------- | ---------------------------- |
| Backend test suite           | 20 passed                    |
| Docker Compose configuration | Validated                    |
| API container                | Healthy                      |
| PostgreSQL container         | Healthy                      |
| API health endpoint          | HTTP 200 observed previously |
| Destructive-command policy   | Blocked locally              |
| Command audit log            | Block decision recorded      |
| Celesto cloud execution      | Failed with HTTP 429         |
| Cloud boot-to-ready time     | Not verified                 |
| Cloud execution cost         | Not verified                 |
| 20-run reliability benchmark | Incomplete                   |
| Five-job cloud concurrency   | Not verified                 |

### Reliability measurements

A valid reliability benchmark must record at least 20 fresh sandbox attempts and calculate its summary from the actual run data.

The benchmark should retain both successful and failed attempts and capture:

* Unique sandbox identifier.
* Whether the sandbox was fresh.
* Success or failure.
* Wall-clock execution duration.
* Boot-to-ready duration.
* Execution cost.

These values must come from real executions. No successful cloud runs, timings, or costs are claimed in this README.

See `reports/reliability.json` and `reports/postmortem.md` for the current benchmark status and observed failure.

### Concurrency measurements

The required concurrency test must use at least five distinct jobs and unique sandbox identifiers. It must record actual start timestamps and any observed breakage.

Because successful cloud execution has not been established, the five-job cloud concurrency benchmark remains incomplete.

See `reports/concurrency.json` for the current status.

---

## Known limitations

1. **Celesto cloud execution:** An execution attempt returned HTTP 429; the exact cause is unknown.
2. **Cloud isolation:** Successful execution inside a fresh cloud sandbox has not been demonstrated.
3. **Cleanup verification:** The runner attempts cleanup after entering the sandbox, but actual cloud-resource deletion has not been verified.
4. **Reliability benchmark:** The required 20-run benchmark has not been completed.
5. **Concurrency benchmark:** Five concurrent cloud jobs have not been verified.
6. **Containment scope:** The destructive-command test proves local policy rejection, not guest-level containment.
7. **Recovery scope:** The recovery function is locally tested, but cloud-based recovery remains unverified.

These limitations are documented to distinguish verified implementation behavior from results that still require real cloud execution.

---

## Future improvements

* Resolve the Celesto HTTP 429 issue and verify successful cloud execution.
* Measure boot-to-ready time and execution cost for fresh sandboxes.
* Complete the 20-run reliability benchmark.
* Run and measure five concurrent jobs.
* Verify cleanup after successful execution, execution failure, and interruption.
* Perform a guest-level containment test in a working sandbox.
* Integrate recovery policy with the actual execution workflow.
* Add automated report generation from measured execution results.
* Expand integration tests for database failures, provider errors, and interrupted requests.
* Improve frontend integration and live execution-status visibility.

---

## AI assistants used

AI assistants supported parts of the implementation and documentation workflow.

The project's claims about testing, cloud execution, cleanup, reliability, and containment should be based on the source code, test results, audit logs, and actual execution evidence.
