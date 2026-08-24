import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8001";

function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const handleFile = (event) => {
    const selected = event.target.files?.[0];

    if (!selected) return;

    setFile(selected);
    setData(null);
    setStatus("Ready to process");
  };

  const processMeeting = async () => {
    if (!file) {
      setStatus("Please select an audio file first.");
      return;
    }

    setLoading(true);
    setStatus("Transcribing and analyzing your meeting...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/summarize`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Meeting processing failed.");
      }

      setData(result);
      setStatus("Meeting processed successfully");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✦</div>
          <div>
            <strong>MeetingAI</strong>
            <span>Smart Meeting Platform</span>
          </div>
        </div>

        <nav>
          <a className="nav-item active" href="#">
            <span>⌂</span>
            Dashboard
          </a>

          <a className="nav-item" href="#recording">
            <span>◉</span>
            New Meeting
          </a>

          <a className="nav-item" href="#results">
            <span>▤</span>
            Meeting Results
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="ai-status">
            <span className="status-dot"></span>
            <div>
              <strong>AI Engine Online</strong>
              <small>Llama 3.2 · Whisper</small>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">

        {/* Header */}
        <header className="topbar">
          <div>
            <p className="eyebrow">AI MEETING ASSISTANT</p>
            <h1>Meeting Dashboard</h1>
          </div>

          <div className="top-status">
            <span className="status-dot"></span>
            System ready
          </div>
        </header>

        {/* Hero */}
        <section className="hero-card">
          <div className="hero-content">
            <div className="hero-badge">✦ AI-POWERED</div>

            <h2>
              Turn meetings into
              <span> actionable insights.</span>
            </h2>

            <p>
              Upload a meeting recording and let AI automatically
              transcribe, summarize, and identify important decisions
              and action items.
            </p>
          </div>

          <div className="hero-orb">
            <div className="orb-inner">AI</div>
          </div>
        </section>

        {/* Upload */}
        <section className="section" id="recording">
          <div className="section-heading">
            <div>
              <p className="eyebrow">STEP 01</p>
              <h2>Meeting recording</h2>
            </div>
            <span className="supported">
              MP3 · WAV · M4A · MP4 · WebM
            </span>
          </div>

          <div className="upload-card">
            <input
              id="audio-upload"
              type="file"
              accept=".mp3,.wav,.m4a,.mp4,.webm,.mpeg,.mpga"
              onChange={handleFile}
              hidden
            />

            <label htmlFor="audio-upload" className="upload-area">
              <div className="upload-icon">↑</div>

              <h3>
                {file ? file.name : "Drop your meeting recording here"}
              </h3>

              <p>
                {file
                  ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
                  : "or click to browse your computer"}
              </p>
            </label>

            <div className="upload-footer">
              <span className="file-info">
                {file ? "✓ File selected" : "No file selected"}
              </span>

              <button
                className="primary-button"
                onClick={processMeeting}
                disabled={loading || !file}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Processing...
                  </>
                ) : (
                  <>
                    ✦ Process Meeting
                  </>
                )}
              </button>
            </div>
          </div>

          {status && (
            <div
              className={`status-message ${
                status.includes("successfully")
                  ? "success"
                  : status.includes("failed") ||
                    status.includes("Please") ||
                    status.includes("not running")
                  ? "error"
                  : ""
              }`}
            >
              <span>{loading ? "◌" : "●"}</span>
              {status}
            </div>
          )}
        </section>

        {/* Results */}
        {data && (
          <section className="section results" id="results">

            <div className="section-heading">
              <div>
                <p className="eyebrow">STEP 02</p>
                <h2>Meeting intelligence</h2>
              </div>

              <div className="processed-badge">
                ✓ Processed
              </div>
            </div>

            {/* Summary */}
            <div className="summary-card">
              <div className="card-icon purple">✦</div>

              <div>
                <p className="card-label">AI SUMMARY</p>
                <h3>Meeting Overview</h3>

                <p className="summary-text">
                  {data.summary}
                </p>
              </div>
            </div>

            <div className="result-grid">

              {/* Transcript */}
              <div className="result-card transcript-card">
                <div className="card-header">
                  <div>
                    <p className="card-label">TRANSCRIPT</p>
                    <h3>Meeting Transcript</h3>
                  </div>

                  <span className="count-badge">
                    {data.transcript?.split(" ").length || 0} words
                  </span>
                </div>

                <div className="transcript">
                  {data.transcript}
                </div>
              </div>

              {/* Decisions */}
              <div className="result-card">
                <div className="card-header">
                  <div>
                    <p className="card-label">DECISIONS</p>
                    <h3>Key Decisions</h3>
                  </div>

                  <span className="number-badge">
                    {data.key_decisions?.length || 0}
                  </span>
                </div>

                {data.key_decisions?.length ? (
                  <div className="decision-list">
                    {data.key_decisions.map((decision, index) => (
                      <div className="decision" key={index}>
                        <span>✓</span>
                        <p>{decision}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty">
                    No decisions detected.
                  </div>
                )}
              </div>

            </div>

            {/* Action Items */}
            <div className="result-card action-card">
              <div className="card-header">
                <div>
                  <p className="card-label">ACTION ITEMS</p>
                  <h3>Tasks & Responsibilities</h3>
                </div>

                <span className="number-badge">
                  {data.action_items?.length || 0}
                </span>
              </div>

              {data.action_items?.length ? (
                <div className="action-table">
                  <div className="table-header">
                    <span>Task</span>
                    <span>Assignee</span>
                    <span>Deadline</span>
                  </div>

                  {data.action_items.map((item, index) => (
                    <div className="table-row" key={index}>
                      <div className="task">
                        <span className="task-check">○</span>
                        {item.task}
                      </div>

                      <span className="assignee">
                        {item.assignee}
                      </span>

                      <span className="deadline">
                        {item.deadline}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty">
                  No action items detected.
                </div>
              )}
            </div>

          </section>
        )}

        <footer>
          <span>MeetingAI</span>
          <span>Powered by Faster-Whisper + Llama 3.2</span>
        </footer>

      </main>
    </div>
  );
}

export default App;