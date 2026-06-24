import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";

export const Route = createFileRoute("/app/")({});

export function Panel({
  title,
  subtitle,
  children,
  className = "",
  right,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  right?: React.ReactNode;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      className={`group relative rounded-xl border border-primary/45 bg-card/90 p-5 backdrop-blur-md shadow-[0_1px_0_0_rgba(255,255,255,0.6)_inset,0_8px_24px_-12px_rgba(15,23,42,0.18)] transition hover:shadow-[0_1px_0_0_rgba(255,255,255,0.6)_inset,0_16px_40px_-16px_rgba(79,70,229,0.25)] hover:border-[color:var(--color-secondary)]/30 ${className}`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[color:var(--color-secondary)]/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <header className="mb-4 flex items-start justify-between gap-2">
        <div>
          <h3 className="font-display text-sm font-semibold tracking-tight">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        {right}
      </header>
      {children}
    </motion.section>
  );
}

export function ChartTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card/95 px-3 py-2 text-xs shadow-lg backdrop-blur">
      {label && (
        <div className="mb-1 font-mono text-muted-foreground">{label}</div>
      )}
      {payload.map((p: any) => (
        <div key={p.dataKey ?? p.name} className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: p.color || p.payload?.color }}
          />
          <span className="capitalize">{p.name}</span>
          <span className="ml-auto font-mono font-semibold">{p.value}</span>
        </div>
      ))}
    </div>
  );
}
