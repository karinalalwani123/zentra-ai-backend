import API_URL from "../config";
import { useState, useEffect } from "react";
import axios from "axios";
import { auth } from "../firebase";

export default function ScheduleEmail({ onBack }) {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sendAt, setSendAt] = useState("");
  const [jobs, setJobs] = useState([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const getUserId = () => {
    const user = auth.currentUser;
    return user ? user.uid : "default";
  };

  const fetchJobs = async () => {
    try {
      const uid = getUserId();
      const res = await axios.get(`${API_URL}/scheduled-emails?user_id=${uid}`);
      setJobs(res.data.jobs || []);
    } catch (e) {
      console.error("Failed to fetch jobs:", e);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const getMinDateTime = () => {
    return new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  };

  const handleSchedule = async () => {
    setError("");
    setStatus("");

    if (!to || !subject || !body || !sendAt) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);
    try {
      const isoDate = sendAt + ":00";
      const uid = getUserId();

      console.log("Sending:", { to, subject, body, send_at: isoDate, user_id: uid });

      const res = await axios.post(`${API_URL}/schedule-email`, {
        to,
        subject,
        body,
        send_at: isoDate,
        user_id: uid,  // ✅ Added user_id
      });

      console.log("Response:", res.data);

      if (res.data.status === "scheduled") {
        setStatus(`Email scheduled for ${new Date(sendAt).toLocaleString()}`);
        setTo("");
        setSubject("");
        setBody("");
        setSendAt("");
        fetchJobs();
      } else if (res.data.status === "error") {
        setError(res.data.error);
      } else {
        setError("Failed to schedule.");
      }
    } catch (e) {
      console.error("Full error:", e);
      console.error("Response data:", e.response?.data);
      setError(
        e.response?.data?.detail
          ? JSON.stringify(e.response.data.detail)
          : e.message || "Error connecting to backend."
      );
    }
    setLoading(false);
  };

  const getStatusBadge = (s) => {
    if (s === "sent") return "badge-sent";
    if (s === "failed") return "badge-failed";
    return "badge-pending";
  };

  return (
    <div className="schedule-shell">

      {/* HEADER */}
      <div className="schedule-header">
        <button onClick={onBack} className="schedule-back-btn">
          ← Back to Chat
        </button>
        <h2>Schedule Email</h2>
      </div>

      <div className="schedule-layout">

        {/* FORM */}
        <div className="schedule-form-card">
          <h3 className="schedule-section-title">New Scheduled Email</h3>

          {error && <p className="schedule-error">{error}</p>}
          {status && <p className="schedule-success">{status}</p>}

          <div className="schedule-field">
            <label>To</label>
            <input
              className="schedule-input"
              placeholder="recipient@example.com"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </div>

          <div className="schedule-field">
            <label>Subject</label>
            <input
              className="schedule-input"
              placeholder="Email subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>

          <div className="schedule-field">
            <label>Body</label>
            <textarea
              className="schedule-textarea"
              placeholder="Write your email..."
              rows={6}
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          </div>

          <div className="schedule-field">
            <label>Send At</label>
            <input
              className="schedule-input"
              type="datetime-local"
              value={sendAt}
              min={getMinDateTime()}
              onChange={(e) => setSendAt(e.target.value)}
            />
          </div>

          <button
            className="schedule-btn"
            onClick={handleSchedule}
            disabled={loading}
          >
            {loading ? "Scheduling..." : "Schedule Email"}
          </button>
        </div>

        {/* SCHEDULED JOBS */}
        <div className="schedule-jobs-card">
          <h3 className="schedule-section-title">
            Scheduled Emails ({jobs.length})
          </h3>

          {jobs.length === 0 ? (
            <p className="schedule-empty">No scheduled emails yet</p>
          ) : (
            <div className="schedule-job-list">
              {jobs.map((job, i) => (
                <div key={i} className="schedule-job-item">
                  <div className="schedule-job-top">
                    <span className="schedule-job-to">{job.to}</span>
                    <span className={`schedule-badge ${getStatusBadge(job.status)}`}>
                      {job.status}
                    </span>
                  </div>
                  <p className="schedule-job-subject">{job.subject}</p>
                  <p className="schedule-job-time">
                    {new Date(job.send_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}