import { useCallback } from "react";

interface Props {
  files: File[];
  onChange: (fn: (prev: File[]) => File[]) => void;
  dragging: boolean;
  setDragging: (val: boolean) => void;
}

export default function ResumeUpload({ files, onChange, dragging, setDragging }: Props) {
  const handleFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const valid = Array.from(incoming).filter(
      f => f.name.endsWith(".pdf") || f.name.endsWith(".docx")
    );
    onChange(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...valid.filter(f => !names.has(f.name))];
    });
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  return (
    <div style={{
      background: "#1a1d27",
      border: "1px solid #2a2d3a",
      borderRadius: 14,
      padding: "1.5rem",
      marginBottom: "1.25rem"
    }}>
      <label style={{
        display: "block", fontSize: 13, fontWeight: 600,
        color: "#818cf8", marginBottom: "0.6rem",
        textTransform: "uppercase", letterSpacing: 0.8
      }}>
        Resumes
      </label>
      <div
        style={{
          border: `2px dashed ${dragging ? "#6366f1" : "#2a2d3a"}`,
          borderRadius: 10,
          padding: "1.5rem",
          textAlign: "center",
          cursor: "pointer",
          background: dragging ? "rgba(99,102,241,0.05)" : "#0f1117",
          transition: "border-color 0.2s, background 0.2s",
        }}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("fileInput")?.click()}
      >
        <div style={{ fontSize: 28, marginBottom: "0.5rem" }}>📂</div>
        <p style={{ color: "#6b7280", fontSize: 14, margin: 0 }}>
          Drop PDF or DOCX files here, or{" "}
          <span style={{ color: "#818cf8" }}>click to browse</span>
        </p>
        <p style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>
          Multiple files supported
        </p>
      </div>
      <input
        id="fileInput"
        type="file"
        accept=".pdf,.docx"
        multiple
        style={{ display: "none" }}
        onChange={e => handleFiles(e.target.files)}
      />
      {files.length > 0 && (
        <div style={{ marginTop: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {files.map((f, i) => (
            <div key={i} style={{
              background: "rgba(99,102,241,0.1)",
              border: "1px solid rgba(99,102,241,0.25)",
              borderRadius: 6, padding: "0.3rem 0.75rem",
              fontSize: 12, color: "#818cf8",
              display: "flex", alignItems: "center", gap: "0.5rem"
            }}>
              📎 {f.name}
               <span
                  onClick={() => onChange( ()=> files.filter((_, idx) => idx !== i))}
                  style={{
                    cursor: "pointer",
                    color: "#f87171",
                    fontWeight: 700,
                    fontSize: 14,
                    lineHeight: 1,
                  }}
                >
                  ×
                </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}