import { TrendingUp, TrendingDown } from "lucide-react";
import type { KPI } from "@/lib/mock-data";

export default function KPICard({ kpi }: { kpi: KPI }) {
  const isPositive = kpi.change >= 0;
  return (
    <div className="rounded-xl border border-border bg-surface p-5 transition-shadow hover:shadow-sm">
      <p className="text-xs font-medium text-muted uppercase tracking-wider">
        {kpi.label}
      </p>
      <p className="mt-2 text-2xl font-bold text-foreground">{kpi.value}</p>
      <div className="mt-2 flex items-center gap-1.5">
        {isPositive ? (
          <TrendingUp className="h-3.5 w-3.5 text-success" />
        ) : (
          <TrendingDown className="h-3.5 w-3.5 text-danger" />
        )}
        <span
          className={`text-xs font-medium ${
            isPositive ? "text-success" : "text-danger"
          }`}
        >
          {isPositive ? "+" : ""}
          {kpi.change}%
        </span>
        <span className="text-xs text-muted-light">vs prev quarter</span>
      </div>
    </div>
  );
}
