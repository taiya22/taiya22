import {
  AlertTriangle,
  TrendingUp,
  Bell,
  Lightbulb,
} from "lucide-react";
import type { AIInsight } from "@/lib/mock-data";

const typeConfig = {
  risk: {
    icon: AlertTriangle,
    bg: "bg-danger-subtle",
    text: "text-danger",
    border: "border-danger/20",
    label: "Risk",
  },
  opportunity: {
    icon: TrendingUp,
    bg: "bg-success-subtle",
    text: "text-success",
    border: "border-success/20",
    label: "Opportunity",
  },
  alert: {
    icon: Bell,
    bg: "bg-warning-subtle",
    text: "text-warning",
    border: "border-warning/20",
    label: "Alert",
  },
  recommendation: {
    icon: Lightbulb,
    bg: "bg-accent-subtle",
    text: "text-accent",
    border: "border-accent/20",
    label: "Recommendation",
  },
};

export default function AIInsightCard({ insight }: { insight: AIInsight }) {
  const config = typeConfig[insight.type];
  const Icon = config.icon;

  return (
    <div
      className={`rounded-xl border ${config.border} bg-surface p-5 transition-shadow hover:shadow-sm`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${config.bg}`}
          >
            <Icon className={`h-4 w-4 ${config.text}`} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${config.bg} ${config.text}`}
              >
                {config.label}
              </span>
              <span className="text-[10px] text-muted-light">
                Confidence: {insight.confidence}%
              </span>
            </div>
            <h4 className="text-sm font-semibold text-foreground">
              {insight.title}
            </h4>
            <p className="mt-1.5 text-xs text-muted leading-relaxed">
              {insight.description}
            </p>
            <div className="mt-3 flex items-center gap-3 text-[10px] text-muted-light">
              <span>{insight.source}</span>
              <span>·</span>
              <span>{insight.timestamp}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
