"use client";

import Header from "@/components/Header";
import KPICard from "@/components/KPICard";
import AIInsightCard from "@/components/AIInsightCard";
import {
  FundPerformanceChart,
  SectorAllocationChart,
  DealStageChart,
} from "@/components/Charts";
import {
  dashboardKPIs,
  deals,
  aiInsights,
  stageLabels,
  stageOrder,
} from "@/lib/mock-data";
import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const stageCounts = stageOrder
    .filter((s) => s !== "closed")
    .map((stage) => ({
      stage: stageLabels[stage],
      count: deals.filter((d) => d.stage === stage).length,
    }));

  const topInsights = aiInsights.slice(0, 4);

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        {/* KPI Grid */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          {dashboardKPIs.map((kpi) => (
            <KPICard key={kpi.label} kpi={kpi} />
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <DealStageChart stageCounts={stageCounts} />
          </div>
          <div className="lg:col-span-1">
            <FundPerformanceChart />
          </div>
          <div className="lg:col-span-1">
            <SectorAllocationChart />
          </div>
        </div>

        {/* AI Insights Feed */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <h2 className="text-sm font-semibold text-foreground">
                Latest AI Insights
              </h2>
            </div>
            <Link
              href="/ai-insights"
              className="flex items-center gap-1 text-xs font-medium text-accent hover:text-accent-light transition-colors"
            >
              View All <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {topInsights.map((insight) => (
              <AIInsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        </div>

        {/* Recent Deals */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">
              Recent Deal Activity
            </h2>
            <Link
              href="/pipeline"
              className="flex items-center gap-1 text-xs font-medium text-accent hover:text-accent-light transition-colors"
            >
              View Pipeline <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="rounded-xl border border-border bg-surface overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-secondary">
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Sector
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Stage
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    AI Score
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    EV
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody>
                {deals.slice(0, 5).map((deal) => (
                  <tr
                    key={deal.id}
                    className="border-b border-border-light hover:bg-surface-secondary/50 transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-foreground">
                      {deal.company}
                    </td>
                    <td className="px-4 py-3 text-muted text-xs">
                      {deal.sector}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-accent-subtle px-2.5 py-0.5 text-[10px] font-semibold text-accent">
                        {stageLabels[deal.stage]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-surface-secondary overflow-hidden">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{ width: `${deal.aiScore}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-foreground">
                          {deal.aiScore}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs font-medium text-foreground">
                      {deal.ev}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted">
                      {deal.updatedAt}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
