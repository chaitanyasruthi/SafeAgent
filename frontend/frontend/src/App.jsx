import { useEffect, useState } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8081";

function App() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadRuns() {
    try {
      const response = await fetch(`${API}/api/runs`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      setRuns(Array.isArray(data) ? data : data.runs || []);
      setError("");
    } catch {
      setError("Backend connection failed. Is FastAPI running on port 8000?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRuns();
  }, []);

  const succeeded = runs.filter((r) => r.state === "succeeded").length;
  const failed = runs.filter((r) => r.state === "failed").length;
  const running = runs.filter((r) => r.state === "running").length;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">S</span>
          <span>SafeAgent</span>
        </div>

        <p className="menu-label">WORKSPACE</p>
        <button className="nav-item active">▦ &nbsp; Overview</button>
        <button className="nav-item" onClick={loadRuns}>
          ◷ &nbsp; Sandbox Runs
        </button>
        <button className="nav-item" onClick={() => window.open(`${API}/docs`, "_blank")}>
          ⌘ &nbsp; API Explorer
        </button>

        <p className="menu-label security-label">SECURITY</p>
        <button className="nav-item" onClick={() => window.open(`${API}/api/reports/containment`, "_blank")}>
          ◈ &nbsp; Containment
        </button>
        <button className="nav-item" onClick={() => window.open(`${API}/api/reports/reliability`, "_blank")}>
          ↗ &nbsp; Evaluations
        </button>
        <button className="nav-item" onClick={() => window.open(`${API}/api/reports/failure_policy`, "_blank")}>
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
            <span>Overview</span>
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
              <h1>Sandbox Overview</h1>
              <p className="subtitle">
                Monitor agent executions, reliability, and security.
              </p>
            </div>

            <button className="refresh-button" onClick={loadRuns}>
              ↻ &nbsp; Refresh data
            </button>
          </div>

          {error && <div className="error-banner">⚠ {error}</div>}

          <div className="info-banner">
            <span className="info-icon">i</span>
            <div>
              <strong>Connected to SafeAgent API</strong>
              <p>Metrics below are calculated from records returned by your backend.</p>
            </div>
            <span className="connection-status">
              {error ? "Disconnected" : loading ? "Connecting..." : "API checked"}
            </span>
          </div>

          <div className="stats-grid">
            <StatCard title="Total Runs" value={loading ? "—" : runs.length} icon="▦" color="purple" detail="Recorded API runs" />
            <StatCard title="Successful" value={loading ? "—" : succeeded} icon="✓" color="green" detail="State: succeeded" />
            <StatCard title="Failed Runs" value={loading ? "—" : failed} icon="!" color="red" detail="State: failed" />
            <StatCard title="Currently Running" value={loading ? "—" : running} icon="◷" color="blue" detail="State: running" />
          </div>

          <div className="section-heading">
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
                    <tr><td colSpan="5" className="empty-state">Loading runs...</td></tr>
                  ) : runs.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="empty-state">
                        <div className="empty-icon">▦</div>
                        <strong>No runs recorded yet</strong>
                        <p>Create a run using the backend API to see it here.</p>
                        <button className="small-button" onClick={() => window.open(`${API}/docs`, "_blank")}>
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
                          <span className={`state-badge ${run.state || "unknown"}`}>
                            <span /> {run.state || "unknown"}
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
              <h3>Security & Isolation</h3>
              <p>Containment reports become available after genuine sandbox tests are completed.</p>
              <button className="text-button" onClick={() => window.open(`${API}/docs`, "_blank")}>
                Explore API ↗
              </button>
            </div>
            <div className="panel">
              <h3>Reliability Evaluation</h3>
              <p>Execution metrics should be based on fresh sandbox runs, not sample data.</p>
              <button className="text-button" onClick={() => window.open(`${API}/api/reports/reliability`, "_blank")}>
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
