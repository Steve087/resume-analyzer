import { useState } from "react";
import axios from "axios";
import JDInput from "./components/JDInput";
import ResumeUpload from "./components/ResumeUpload";
import RankCard from "./components/ResultsCard";

interface Candidate {
  name: string;
  filename: string;
  score: number;
  category_breakdown: string;
  explanation: string;
  strengths: string[];
  gaps: string[];
  log: string;
}

const API = "https://resume-analyzer-xx0x.onrender.com";

export default function App() {
  const [jd, setJd] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const handleRank = async () => {
    if (!jd.trim()) return alert("Please enter a job description.");
    if (files.length === 0) return alert("Please upload at least one resume.");
    setLoading(true);
    setCandidates([]);
    setErrors([]);
    const fd = new FormData();
    fd.append("job_description", jd);
    files.forEach(f => fd.append("files", f));
    try {
      const res = await axios.post(`${API}/rank`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setCandidates(res.data.candidates);
      setErrors(res.data.errors);
    } catch {
      alert("Could not reach the backend. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    await axios.delete(`${API}/cache`);
    alert("Cache cleared.");
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0f1117",
      color: "#e8eaf0",
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      padding: "2rem 1rem",
    }}>
      <div style={{ maxWidth: 860, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div style={{
            display: "inline-block",
            background: "rgba(99,102,241,0.15)",
            color: "#818cf8",
            border: "1px solid rgba(99,102,241,0.3)",
            borderRadius: 20, padding: "0.3rem 1rem",
            fontSize: 12, fontWeight: 600, letterSpacing: 1,
            marginBottom: "1rem", textTransform: "uppercase",
          }}>
            AI-Powered
          </div>
          <h1 style={{
            fontSize: "clamp(1.8rem, 5vw, 2.8rem)",
            fontWeight: 800, margin: "0 0 0.5rem",
            background: "linear-gradient(135deg, #e8eaf0 0%, #818cf8 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            Resume Ranking System
          </h1>
          <p style={{ color: "#6b7280", fontSize: 15, margin: 0 }}>
            Match candidates to any job description — powered by Gemini & Groq
          </p>
        </div>

        {/* Inputs */}
        <JDInput value={jd} onChange={setJd} />
        <ResumeUpload
          files={files}
          onChange={setFiles}
          dragging={dragging}
          setDragging={setDragging}
        />

        {/* Actions */}
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            onClick={handleRank}
            disabled={loading}
            style={{
              flex: 1, padding: "0.85rem 1.5rem",
              background: loading ? "#2a2d3a" : "linear-gradient(135deg, #6366f1, #8b5cf6)",
              color: loading ? "#6b7280" : "white",
              border: "none", borderRadius: 10,
              fontSize: 15, fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "⏳ Analyzing resumes..." : "🚀 Rank Candidates"}
          </button>
          <button
            onClick={handleClearCache}
            style={{
              padding: "0.85rem 1.25rem",
              background: "#1a1d27", color: "#6b7280",
              border: "1px solid #2a2d3a", borderRadius: 10,
              fontSize: 14, fontWeight: 600, cursor: "pointer",
            }}
          >
            🗑️ Clear Cache
          </button>
        </div>

        {/* Errors */}
        {errors.length > 0 && (
          <div style={{
            background: "rgba(239,68,68,0.08)",
            border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 10, padding: "1rem",
            marginTop: "1.25rem", fontSize: 13, color: "#fca5a5"
          }}>
            {errors.map((e, i) => <div key={i}>⚠ {e}</div>)}
          </div>
        )}

        {/* Results */}
        {candidates.length > 0 && (
          <div style={{ marginTop: "2rem" }}>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: "1rem", color: "#e8eaf0" }}>
              📊 Results — {candidates.length} candidate{candidates.length > 1 ? "s" : ""} ranked
            </div>
            {candidates.map((c, i) => (
              <RankCard key={i} rank={i + 1} candidate={c} />
            ))}
          </div>
        )}

      </div>
    </div>
  );
}