interface Props {
  value: string;
  onChange: (val: string) => void;
}

export default function JDInput({ value, onChange }: Props) {
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
        Job Description
      </label>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Paste the job description here..."
        rows={7}
        style={{
          width: "100%",
          background: "#0f1117",
          border: "1px solid #2a2d3a",
          borderRadius: 10,
          color: "#e8eaf0",
          fontSize: 14,
          padding: "0.85rem 1rem",
          resize: "vertical",
          outline: "none",
          lineHeight: 1.6,
          boxSizing: "border-box",
          transition: "border-color 0.2s",
        }}
        onFocus={e => (e.target.style.borderColor = "#6366f1")}
        onBlur={e => (e.target.style.borderColor = "#2a2d3a")}
      />
    </div>
  );
}