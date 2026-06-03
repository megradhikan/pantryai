const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  fresh:         { color: "var(--status-fresh)",    label: "Fresh" },
  low:           { color: "var(--status-low)",      label: "Low" },
  expiring_soon: { color: "var(--status-expiring)", label: "Expiring" },
  expired:       { color: "var(--status-expired)",  label: "Expired" },
  finished:      { color: "var(--status-finished)", label: "Done" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? { color: "var(--faint)", label: status };
  return (
    <span className="inline-flex items-center gap-1.5" style={{ fontSize: "0.6875rem", color: "var(--muted)" }}>
      <span
        className="shrink-0 rounded-full"
        style={{ width: 7, height: 7, background: config.color }}
      />
      {config.label}
    </span>
  );
}
