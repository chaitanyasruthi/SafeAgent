-- Idempotent: safe to run more than once. Demonstration record only,
-- NOT an evaluation result (it is not counted in reports/reliability.json).
CREATE TABLE IF NOT EXISTS runs (
    run_id            VARCHAR(64) PRIMARY KEY,
    sandbox_name      VARCHAR(64) NOT NULL UNIQUE,
    problem_id        VARCHAR(64) NOT NULL,
    state             VARCHAR(16) NOT NULL,
    execution_target  VARCHAR(32) NOT NULL,
    task_description  TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at        TIMESTAMPTZ,
    ended_at          TIMESTAMPTZ,
    wall_clock_s      DOUBLE PRECISION,
    boot_to_ready_s   DOUBLE PRECISION,
    cost_usd          DOUBLE PRECISION,
    result_summary    TEXT,
    error_details     TEXT,
    cleanup_status    VARCHAR(32)
);

INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target, task_description, result_summary, cleanup_status)
VALUES ('run-seeddemo1', 'sbx-seeddemo1', 'csv-analysis', 'deleted', 'celesto_sandbox',
        'Seeded demonstration record', 'Seed row for demonstration; not a real execution.', 'not_applicable')
ON CONFLICT (sandbox_name) DO NOTHING;
