import { useState } from "react";

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

function getScoreColor(score: number) {
  if (score >= 80) return { bg: "rgba(16,185,129,0.15)", color: "#34d399", border: "1px solid rgba(16,185,129,0.3)" };
  if (score >= 60) return { bg: "rgba(251,191,36,0.12)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.25)" };
  return { bg: "rgba(239,68,68,0.12)", color: "#f87171", border: "1px solid rgba(239,68,68,0.25)" };
}

export default function RankCard({ rank, candidate }: { rank: number; candidate: Candidate }) {
  const [open, setOpen] = useState(false);
  const sc = getScoreColor(candidate.score);

  return (
    <div style={{
      background: "#1a1d27",
      border: "1px solid #2a2d3a",
      borderRadius: 14,
      marginBottom: "0.75rem",
      overflow: "hidden"
    }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "1rem 1.25rem",
          cursor: "pointer",
        }}
        onClick={() => setOpen(!open)}
        onMouseEnter={e => (e.currentTarget.style.background = "#1e2130")}
        onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "rgba(99,102,241,0.15)",
            border: "1px solid rgba(99,102,241,0.3)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 12, fontWeight: 700, color: "#818cf8", flexShrink: 0,
          }}>
            #{rank}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15, color: "#e8eaf0" }}>{candidate.name}</div>
            <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>📁 {candidate.filename}</div>
            {candidate.log && (
              <div style={{ fontSize: 11, color: "#6366f1", marginTop: 3 }}>
                {candidate.log}
              </div>
            )}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div style={{
            padding: "0.35rem 0.9rem", borderRadius: 20,
            fontWeight: 700, fontSize: 14, flexShrink: 0,
            background: sc.bg, color: sc.color, border: sc.border
          }}>
            {candidate.score}/100
          </div>
          <span style={{ color: "#6b7280", fontSize: 12 }}>{open ? "▲" : "▼"}</span>
        </div>
      </div>

      {open && (
        <div style={{ padding: "0 1.25rem 1.25rem", borderTop: "1px solid #2a2d3a" }}>
          {candidate.category_breakdown && (
            <div style={{
              background: "#0f1117", borderRadius: 8,
              padding: "0.75rem 1rem", fontSize: 13,
              color: "#9ca3af", margin: "0.75rem 0",
              fontFamily: "monospace"
            }}>
              {candidate.category_breakdown}
            </div>
          )}
          <p style={{ fontSize: 14, color: "#9ca3af", lineHeight: 1.6, marginBottom: "1rem" }}>
            {candidate.explanation}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div style={{
              background: "rgba(16,185,129,0.06)",
              border: "1px solid rgba(16,185,129,0.15)",
              borderRadius: 8, padding: "0.75rem"
            }}>
              <div style={{
                fontSize: 12, fontWeight: 700, letterSpacing: 0.8,
                textTransform: "uppercase", color: "#34d399", marginBottom: "0.5rem"
              }}>
                ✓ Strengths
              </div>
              {candidate.strengths.map((s, i) => (
                <div key={i} style={{ fontSize: 13, color: "#9ca3af", marginBottom: "0.3rem" }}>• {s}</div>
              ))}
            </div>
            <div style={{
              background: "rgba(239,68,68,0.06)",
              border: "1px solid rgba(239,68,68,0.15)",
              borderRadius: 8, padding: "0.75rem"
            }}>
              <div style={{
                fontSize: 12, fontWeight: 700, letterSpacing: 0.8,
                textTransform: "uppercase", color: "#f87171", marginBottom: "0.5rem"
              }}>
                ✗ Gaps
              </div>
              {candidate.gaps.map((g, i) => (
                <div key={i} style={{ fontSize: 13, color: "#9ca3af", marginBottom: "0.3rem" }}>• {g}</div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}