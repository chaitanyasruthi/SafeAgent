import { useEffect, useState } from "react";
import "./App.css";

const API = (
  import.meta.env.VITE_API_URL || "http://localhost:8081"
).replace(/\/+$/, "");

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

    // Scroll after React updates the active page.
    requestAnimationFrame(() => {
      document.getElementById("sandbox-runs")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });

    // Refresh the latest records from the deployed API.
    loadRuns();
  }

  function openOverview() {
    setActivePage("overview");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function openApiExplorer() {
    window.open(`${API}/docs`, "_blank", "noopener,noreferrer");
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

  const succeeded = runs.filter((run) => run.state === "succeeded").length;
  const failed = runs.filter((run) => run.state === "failed").length;
  const running = runs.filter((run) => run.state === "running").length;

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
          className={`nav-item ${activePage === "overview" ? "active" : ""}`}
          onClick={openOverview}
        >
          ▦ &nbsp; Overview
        </button>

        <button
          className={`nav-item ${activePage === "runs" ? "active" : ""}`}
          onClick={openSandboxRuns}
        >
          ◷ &nbsp; Sandbox Runs
        </button>

        <button className="nav-item" onClick={openApiExplorer}>
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
              {activePage === "runs" ? "Sandbox Runs" : "Overview"}
            </span>
          </div>

          <div className="top-right">
            <span className="live-dot" />
            <span>Live data</span>
            <div className="avatar">SA</div>
          </div>
        </header>

        <section className="content">
          <div className="welcome-row">
            <div>
              <p className="eyebrow">SECURE AI EXECUTION PLATFORM</p>

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
              {loading ? "Loading..." : "↻  Refresh data"}
            </button>
          </div>

          {error && <div className="error-banner">⚠ {error}</div>}

          <div className="info-banner">
            <span className="info-icon">i</span>

            <div>
              <strong>
                {error ? "SafeAgent API connection failed" : "SafeAgent API"}
              </strong>

              <p>
                Metrics below are calculated from records returned by your
                deployed backend.
              </p>
            </div>

            <span className="connection-status">
              {error ? "Disconnected" : loading ? "Connecting..." : "API checked"}
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

            <span className="count-badge">{runs.length} records</span>
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
                        Unable to load runs. Check your API connection and try
                        refreshing.
                      </td>
                    </tr>
                  ) : runs.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="empty-state">
                        <div className="empty-icon">▦</div>
                        <strong>No runs recorded yet</strong>
                        <p>
                          Create a run using the backend API to see it here.
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
                        <td className="run-id">{run.run_id || "—"}</td>
                        <td>{run.sandbox_name || "—"}</td>
                        <td>{run.problem_id || "—"}</td>

                        <td>
                          <span
                            className={`state-badge ${run.state || "unknown"}`}
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
                Containment reports become available after genuine sandbox
                tests are completed.
              </p>

              <button
                className="text-button"
                onClick={openApiExplorer}
              >
                Explore API ↗
              </button>
            </div>

            <div className="panel">
              <h3>Reliability Evaluation</h3>

              <p>
                Execution metrics should be based on fresh sandbox runs, not
                sample data.
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
      </main>
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

