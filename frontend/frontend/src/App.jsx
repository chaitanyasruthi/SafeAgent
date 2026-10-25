import { useEffect, useState } from "react";
import "./App.css";

const API = (
  import.meta.env.VITE_API_URL ||
  "https://safeagent-api-qc8c.onrender.com"
).replace(/\/+$/, "");

const ENDPOINTS = [
  {
    method: "GET",
    path: "/health",
    description: "Check whether the SafeAgent API is running.",
    safe: true,
  },
  {
    method: "GET",
    path: "/api/runs",
    description: "Retrieve recorded sandbox runs.",
    safe: true,
  },
  {
    method: "POST",
    path: "/api/runs",
    description: "Create a sandbox run record.",
    safe: false,
    body: {
      run_id: "run-demo-001",
      sandbox_name: "sbx-demo123",
      problem_id: "problem-demo-001",
      state: "created",
      execution_target: "celesto_sandbox",
      task_description: "Demo run record",
    },
  },
  {
    method: "GET",
    path: "/api/reports/containment",
    description: "Retrieve the containment report.",
    safe: true,
  },
];

function App() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState("overview");

  async function loadRuns() {
    setLoading(true);

    try {
      const response = await fetch(`${API}/api/runs`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      setRuns(Array.isArray(data) ? data : data.runs || []);
      setError("");
    } catch (err) {
      console.error("Failed to load SafeAgent runs:", err);
      setError(
        "Backend connection failed. Please check the deployed SafeAgent API."
      );
    } finally {
      setLoading(false);
    }
  }

  function openSandboxRuns() {
    setActivePage("runs");
    loadRuns();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openOverview() {
    setActivePage("overview");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openApiExplorer() {
    setActivePage("api");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function openReport(name) {
    window.open(
      `${API}/api/reports/${encodeURIComponent(name)}`,
      "_blank",
      "noopener,noreferrer"
    );
  }

  useEffect(() => {
    loadRuns();
  }, []);

  const succeeded = runs.filter(
    (run) => run.state === "succeeded"
  ).length;

  const failed = runs.filter(
    (run) => run.state === "failed"
  ).length;

  const running = runs.filter(
    (run) => run.state === "running"
  ).length;

  return (
    <div className="app">
      <aside className="sidebar">
        <div
          className="brand"
          role="button"
          tabIndex={0}
          onClick={openOverview}
          onKeyDown={(event) => {
            if (event.key === "Enter") openOverview();
          }}
        >
          <span className="brand-icon">S</span>
          <span>SafeAgent</span>
        </div>

        <p className="menu-label">WORKSPACE</p>

        <button
          className={`nav-item ${
            activePage === "overview" ? "active" : ""
          }`}
          onClick={openOverview}
        >
          ▦ &nbsp; Overview
        </button>

        <button
          className={`nav-item ${
            activePage === "runs" ? "active" : ""
          }`}
          onClick={openSandboxRuns}
        >
          ◷ &nbsp; Sandbox Runs
        </button>

        <button
          className={`nav-item ${
            activePage === "api" ? "active" : ""
          }`}
          onClick={openApiExplorer}
        >
          ⌘ &nbsp; API Explorer
        </button>

        <p className="menu-label security-label">SECURITY</p>

        <button
          className="nav-item"
          onClick={() => openReport("containment")}
        >
          ◈ &nbsp; Containment
        </button>

        <button
          className="nav-item"
          onClick={() => openReport("reliability")}
        >
          ↗ &nbsp; Evaluations
        </button>

        <button
          className="nav-item"
          onClick={() => openReport("failure_policy")}
        >
          ⟳ &nbsp; Recovery Policy
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <span>SafeAgent Workspace</span>
          <small>v1.0</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace / </span>
            <span>
              {activePage === "api"
                ? "API Explorer"
                : activePage === "runs"
                  ? "Sandbox Runs"
                  : "Overview"}
            </span>
          </div>

          <div className="top-right">
            <span className="live-dot" />
            <span>Live data</span>
            <div className="avatar">SA</div>
          </div>
        </header>

        {activePage === "api" ? (
          <section className="content">
            <ApiExplorer apiUrl={API} />
          </section>
        ) : (
          <section className="content">
            <div className="welcome-row">
              <div>
                <p className="eyebrow">
                  SECURE AI EXECUTION PLATFORM
                </p>

                <h1>
                  {activePage === "runs"
                    ? "Sandbox Runs"
                    : "Sandbox Overview"}
                </h1>

                <p className="subtitle">
                  Monitor agent executions, reliability, and security.
                </p>
              </div>

              <button
                className="refresh-button"
                onClick={loadRuns}
                disabled={loading}
              >
                {loading ? "Loading..." : "↻ Refresh data"}
              </button>
            </div>

            {error && (
              <div className="error-banner">⚠ {error}</div>
            )}

            <div className="info-banner">
              <span className="info-icon">i</span>

              <div>
                <strong>
                  {error
                    ? "SafeAgent API connection failed"
                    : "SafeAgent API"}
                </strong>

                <p>
                  Metrics below are calculated from records returned
                  by your deployed backend.
                </p>
              </div>

              <span className="connection-status">
                {error
                  ? "Disconnected"
                  : loading
                    ? "Connecting..."
                    : "API checked"}
              </span>
            </div>

            <div className="stats-grid">
              <StatCard
                title="Total Runs"
                value={loading ? "—" : runs.length}
                icon="▦"
                color="purple"
                detail="Recorded API runs"
              />

              <StatCard
                title="Successful"
                value={loading ? "—" : succeeded}
                icon="✓"
                color="green"
                detail="State: succeeded"
              />

              <StatCard
                title="Failed Runs"
                value={loading ? "—" : failed}
                icon="!"
                color="red"
                detail="State: failed"
              />

              <StatCard
                title="Currently Running"
                value={loading ? "—" : running}
                icon="◷"
                color="blue"
                detail="State: running"
              />
            </div>

            <div className="section-heading" id="sandbox-runs">
              <div>
                <h2>Execution History</h2>
                <p>Sandbox runs recorded by the backend</p>
              </div>

              <span className="count-badge">
                {runs.length} records
              </span>
            </div>

            <div className="table-card">
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>RUN ID</th>
                      <th>SANDBOX</th>
                      <th>PROBLEM</th>
                      <th>STATE</th>
                      <th>TARGET</th>
                    </tr>
                  </thead>

                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="5" className="empty-state">
                          Loading runs...
                        </td>
                      </tr>
                    ) : error ? (
                      <tr>
                        <td colSpan="5" className="empty-state">
                          Unable to load runs. Check your API
                          connection and try refreshing.
                        </td>
                      </tr>
                    ) : runs.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="empty-state">
                          <div className="empty-icon">▦</div>
                          <strong>No runs recorded yet</strong>
                          <p>
                            Create a run using the backend API to
                            see it here.
                          </p>

                          <button
                            className="small-button"
                            onClick={openApiExplorer}
                          >
                            Open API Explorer
                          </button>
                        </td>
                      </tr>
                    ) : (
                      runs.map((run, index) => (
                        <tr key={run.run_id || index}>
                          <td className="run-id">
                            {run.run_id || "—"}
                          </td>
                          <td>{run.sandbox_name || "—"}</td>
                          <td>{run.problem_id || "—"}</td>

                          <td>
                            <span
                              className={`state-badge ${
                                run.state || "unknown"
                              }`}
                            >
                              <span />
                              {run.state || "unknown"}
                            </span>
                          </td>

                          <td>{run.execution_target || "—"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <div className="table-footer">
                <span>Showing {runs.length} recorded runs</span>
                <span>Source: SafeAgent backend</span>
              </div>
            </div>

            <div className="bottom-grid">
              <div className="panel">
                <h3>Security &amp; Isolation</h3>

                <p>
                  Containment reports become available after genuine
                  sandbox tests are completed.
                </p>

                <button
                  className="text-button"
                  onClick={() => openReport("containment")}
                >
                  View containment report ↗
                </button>
              </div>

              <div className="panel">
                <h3>Reliability Evaluation</h3>

                <p>
                  Execution metrics should be based on fresh sandbox
                  runs, not sample data.
                </p>

                <button
                  className="text-button"
                  onClick={() => openReport("reliability")}
                >
                  View report ↗
                </button>
              </div>
            </div>

            <footer>
              <span>SafeAgent · Secure AI agent execution</span>
              <span>Real backend records · No fabricated metrics</span>
            </footer>
          </section>
        )}
      </main>
    </div>
  );
}

function ApiExplorer({ apiUrl }) {
  const [selected, setSelected] = useState(ENDPOINTS[0]);
  const [requestBody, setRequestBody] = useState("");
  const [responseData, setResponseData] = useState(null);
  const [status, setStatus] = useState(null);
  const [requestError, setRequestError] = useState("");
  const [requestLoading, setRequestLoading] = useState(false);
  const [confirmWrite, setConfirmWrite] = useState(false);

  useEffect(() => {
    setRequestBody(
      ENDPOINTS[0].body
        ? JSON.stringify(ENDPOINTS[0].body, null, 2)
        : ""
    );
  }, []);

  function selectEndpoint(endpoint) {
    setSelected(endpoint);
    setRequestBody(
      endpoint.body
        ? JSON.stringify(endpoint.body, null, 2)
        : ""
    );
    setResponseData(null);
    setStatus(null);
    setRequestError("");
    setConfirmWrite(false);
  }

  async function sendRequest() {
    if (selected.method === "POST" && !confirmWrite) {
      setRequestError(
        "Confirm that you understand this request may create a record."
      );
      return;
    }

    setRequestLoading(true);
    setRequestError("");
    setResponseData(null);
    setStatus(null);

    try {
      const options = {
        method: selected.method,
        headers: {
          Accept: "application/json",
        },
      };

      if (selected.method === "POST") {
        let parsedBody;

        try {
          parsedBody = JSON.parse(requestBody);
        } catch {
          throw new Error("The request body is not valid JSON.");
        }

        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(parsedBody);
      }

      const response = await fetch(
        `${apiUrl}${selected.path}`,
        options
      );

      const text = await response.text();
      let data = text;

      try {
        data = text ? JSON.parse(text) : null;
      } catch {
        // Keep non-JSON responses as plain text.
      }

      setStatus(response.status);
      setResponseData(data);
    } catch (err) {
      setRequestError(
        err.message ||
          "Could not connect to the API. Check the backend URL and CORS configuration."
      );
    } finally {
      setRequestLoading(false);
    }
  }

  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      setRequestError(
        "Clipboard access failed. Please copy the text manually."
      );
    }
  }

  return (
    <div className="api-explorer">
      <div className="api-hero">
        <p className="eyebrow">DEVELOPER WORKSPACE</p>
        <h1>API Explorer</h1>
        <p className="subtitle">
          Inspect endpoints, send requests, and review backend responses.
        </p>

        <div className="api-base-url">
          <span>BASE URL</span>
          <code>{apiUrl}</code>

          <button
            className="small-button"
            onClick={() => copyText(apiUrl)}
          >
            Copy URL
          </button>
        </div>
      </div>

      <div className="api-layout">
        <div className="panel api-endpoints">
          <h3>Endpoints</h3>
          <p className="api-muted">
            Select an endpoint to inspect it.
          </p>

          {ENDPOINTS.map((endpoint) => (
            <button
              key={`${endpoint.method}-${endpoint.path}`}
              className={`endpoint-item ${
                selected.path === endpoint.path &&
                selected.method === endpoint.method
                  ? "selected"
                  : ""
              }`}
              onClick={() => selectEndpoint(endpoint)}
            >
              <span
                className={`method-badge ${endpoint.method.toLowerCase()}`}
              >
                {endpoint.method}
              </span>

              <span className="endpoint-info">
                <strong>{endpoint.path}</strong>
                <small>{endpoint.description}</small>
              </span>
            </button>
          ))}
        </div>

        <div className="panel api-request">
          <h3>Request Builder</h3>
          <p className="api-muted">
            Send a request to your deployed SafeAgent backend.
          </p>

          <div className="selected-endpoint">
            <span
              className={`method-badge ${selected.method.toLowerCase()}`}
            >
              {selected.method}
            </span>
            <code>{selected.path}</code>
          </div>

          <p className="api-description">
            {selected.description}
          </p>

          {selected.method === "POST" && (
            <>
              <label className="api-label" htmlFor="request-body">
                JSON Request Body
              </label>

              <textarea
                id="request-body"
                className="api-json-editor"
                value={requestBody}
                onChange={(event) =>
                  setRequestBody(event.target.value)
                }
                spellCheck="false"
              />

              <label className="api-confirm">
                <input
                  type="checkbox"
                  checked={confirmWrite}
                  onChange={(event) =>
                    setConfirmWrite(event.target.checked)
                  }
                />
                I understand this request may create a database record.
              </label>
            </>
          )}

          <button
            className="api-send-button"
            onClick={sendRequest}
            disabled={
              requestLoading ||
              (selected.method === "POST" && !confirmWrite)
            }
          >
            {requestLoading ? "Sending..." : "▶ Send Request"}
          </button>

          <p className="api-warning">
            Cloud sandbox execution is intentionally excluded to
            avoid accidental cloud charges. POST requests can modify
            backend data.
          </p>

          <div className="api-response">
            <div className="api-response-heading">
              <h3>Response</h3>

              {status !== null && (
                <span
                  className={`response-status ${
                    status >= 200 && status < 300
                      ? "success"
                      : "failure"
                  }`}
                >
                  HTTP {status}
                </span>
              )}
            </div>

            {requestError && (
              <div className="error-banner">{requestError}</div>
            )}

            {responseData !== null && (
              <pre className="api-response-code">
                {typeof responseData === "string"
                  ? responseData
                  : JSON.stringify(responseData, null, 2)}
              </pre>
            )}

            {responseData === null &&
              !requestError &&
              status === null && (
                <div className="api-response-empty">
                  Select an endpoint and send a request to see
                  the response.
                </div>
              )}
          </div>
        </div>
      </div>

      <footer>
        <span>SafeAgent · API Explorer</span>
        <button
          className="text-button"
          onClick={() => copyText(`${apiUrl}/docs`)}
        >
          Copy Swagger URL ↗
        </button>
      </footer>
    </div>
  );
}

function StatCard({ title, value, icon, color, detail }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <p>{title}</p>
      <h2>{value}</h2>
      <span className="stat-detail">{detail}</span>
    </div>
  );
}

export default App;

