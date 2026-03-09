"use client";

import Header from "@/components/Header";
import { deals, stageLabels, stageOrder } from "@/lib/mock-data";
import type { Deal } from "@/lib/mock-data";
import { Brain, User, Calendar, Tag } from "lucide-react";

function DealCard({ deal }: { deal: Deal }) {
  const scoreColor =
    deal.aiScore >= 85
      ? "text-success"
      : deal.aiScore >= 70
      ? "text-accent"
      : "text-warning";
  const scoreBg =
    deal.aiScore >= 85
      ? "bg-success-subtle"
      : deal.aiScore >= 70
      ? "bg-accent-subtle"
      : "bg-warning-subtle";

  return (
    <div className="rounded-lg border border-border bg-surface p-4 hover:shadow-sm transition-shadow cursor-pointer group">
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-sm font-semibold text-foreground group-hover:text-accent transition-colors leading-tight">
          {deal.company}
        </h4>
        <div
          className={`flex items-center gap-1 rounded-full px-2 py-0.5 ${scoreBg}`}
        >
          <Brain className={`h-3 w-3 ${scoreColor}`} />
          <span className={`text-[10px] font-bold ${scoreColor}`}>
            {deal.aiScore}
          </span>
        </div>
      </div>

      <p className="text-[11px] text-muted mb-3">{deal.sector}</p>

      <div className="space-y-1.5 mb-3">
        <div className="flex justify-between text-[11px]">
          <span className="text-muted">EV</span>
          <span className="font-medium text-foreground">{deal.ev}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-muted">EBITDA</span>
          <span className="font-medium text-foreground">{deal.ebitda}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-muted">Multiple</span>
          <span className="font-medium text-foreground">{deal.multiple}</span>
        </div>
      </div>

      {/* Flags */}
      <div className="flex flex-wrap gap-1 mb-3">
        {deal.flags.map((flag) => (
          <span
            key={flag}
            className="inline-flex items-center gap-0.5 rounded-md bg-surface-secondary px-1.5 py-0.5 text-[10px] text-muted"
          >
            <Tag className="h-2.5 w-2.5" />
            {flag}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-border-light">
        <div className="flex items-center gap-1 text-[10px] text-muted-light">
          <User className="h-3 w-3" />
          {deal.assignee}
        </div>
        <div className="flex items-center gap-1 text-[10px] text-muted-light">
          <Calendar className="h-3 w-3" />
          {deal.updatedAt}
        </div>
      </div>
    </div>
  );
}

function StageColumn({ stage, stageDeals }: { stage: Deal["stage"]; stageDeals: Deal[] }) {
  const stageColors: Record<string, string> = {
    sourcing: "bg-muted-light",
    screening: "bg-muted",
    dd: "bg-accent",
    valuation: "bg-accent-light",
    ic: "bg-foreground",
    execution: "bg-success",
    closed: "bg-foreground",
  };

  return (
    <div className="flex flex-col min-w-[280px] max-w-[300px]">
      {/* Column Header */}
      <div className="flex items-center gap-2 mb-3 px-1">
        <div className={`h-2 w-2 rounded-full ${stageColors[stage]}`} />
        <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">
          {stageLabels[stage]}
        </h3>
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-secondary text-[10px] font-bold text-muted">
          {stageDeals.length}
        </span>
      </div>

      {/* Cards */}
      <div className="space-y-3 flex-1">
        {stageDeals.map((deal) => (
          <DealCard key={deal.id} deal={deal} />
        ))}
        {stageDeals.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-6 text-center">
            <p className="text-xs text-muted-light">No deals</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function PipelinePage() {
  return (
    <>
      <Header title="Deal Pipeline" />
      <div className="p-6">
        {/* Summary Bar */}
        <div className="flex items-center gap-6 mb-6">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted">Total Deals:</span>
            <span className="font-semibold text-foreground">{deals.length}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted">Total Pipeline EV:</span>
            <span className="font-semibold text-foreground">¥115.9B</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted">Avg AI Score:</span>
            <span className="font-semibold text-accent">
              {Math.round(
                deals.reduce((sum, d) => sum + d.aiScore, 0) / deals.length
              )}
            </span>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="flex gap-4 overflow-x-auto pb-4">
          {stageOrder.map((stage) => (
            <StageColumn
              key={stage}
              stage={stage}
              stageDeals={deals.filter((d) => d.stage === stage)}
            />
          ))}
        </div>
      </div>
    </>
  );
}
