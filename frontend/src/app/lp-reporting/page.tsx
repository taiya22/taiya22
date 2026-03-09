"use client";

import Header from "@/components/Header";
import { FundPerformanceChart } from "@/components/Charts";
import { lpReports } from "@/lib/mock-data";
import {
  FileText,
  Send,
  Clock,
  CheckCircle2,
  PenLine,
  Sparkles,
  Download,
  RefreshCw,
  Users,
  TrendingUp,
  BarChart3,
} from "lucide-react";

const statusConfig = {
  draft: {
    icon: PenLine,
    label: "Draft",
    bg: "bg-surface-secondary",
    text: "text-muted",
  },
  review: {
    icon: Clock,
    label: "In Review",
    bg: "bg-warning-subtle",
    text: "text-warning",
  },
  sent: {
    icon: CheckCircle2,
    label: "Sent",
    bg: "bg-success-subtle",
    text: "text-success",
  },
};

function LPCard() {
  const lps = [
    { name: "GPIF", commitment: "¥15.0B", type: "Pension Fund" },
    { name: "Dai-ichi Life Insurance", commitment: "¥8.0B", type: "Insurance" },
    { name: "University of Tokyo Endowment", commitment: "¥3.0B", type: "Endowment" },
    { name: "Mizuho Bank", commitment: "¥5.0B", type: "Bank" },
    { name: "Singapore GIC", commitment: "¥10.0B", type: "Sovereign Wealth" },
  ];

  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="flex items-center gap-2 mb-4">
        <Users className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-semibold text-foreground">
          LP Overview — Fund III
        </h3>
      </div>
      <div className="space-y-2">
        {lps.map((lp) => (
          <div
            key={lp.name}
            className="flex items-center justify-between rounded-lg bg-surface-secondary px-4 py-2.5"
          >
            <div>
              <p className="text-xs font-medium text-foreground">{lp.name}</p>
              <p className="text-[10px] text-muted">{lp.type}</p>
            </div>
            <span className="text-xs font-semibold text-foreground">
              {lp.commitment}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-4 pt-3 border-t border-border flex justify-between text-xs">
        <span className="text-muted">Total Commitment</span>
        <span className="font-bold text-foreground">¥41.0B</span>
      </div>
    </div>
  );
}

export default function LPReportingPage() {
  return (
    <>
      <Header title="LP Reporting" />
      <div className="p-6 space-y-6">
        {/* AI Report Generation Banner */}
        <div className="rounded-xl border border-accent/20 bg-accent-subtle p-5">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-white">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  AI Report Generation
                </h3>
                <p className="text-xs text-muted mt-1 max-w-xl">
                  Automatically generate quarterly LP reports from portfolio
                  data. AI analyzes KPIs, compiles performance metrics, and
                  drafts narratives in ILPA-compliant format.
                </p>
              </div>
            </div>
            <button className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-light transition-colors">
              <RefreshCw className="h-4 w-4" />
              Generate Q1 2026 Report
            </button>
          </div>
        </div>

        {/* Fund Summary Cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-accent" />
              <p className="text-[10px] text-muted uppercase tracking-wider">
                Fund III NAV
              </p>
            </div>
            <p className="text-xl font-bold text-foreground">¥44.1B</p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-success" />
              <p className="text-[10px] text-muted uppercase tracking-wider">
                Fund III TVPI
              </p>
            </div>
            <p className="text-xl font-bold text-success">1.67x</p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="h-4 w-4 text-foreground" />
              <p className="text-[10px] text-muted uppercase tracking-wider">
                Fund II NAV
              </p>
            </div>
            <p className="text-xl font-bold text-foreground">¥27.2B</p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="h-4 w-4 text-success" />
              <p className="text-[10px] text-muted uppercase tracking-wider">
                Fund II TVPI
              </p>
            </div>
            <p className="text-xl font-bold text-success">2.35x</p>
          </div>
        </div>

        {/* Reports Table + LP Card + Chart */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          {/* Reports Table */}
          <div className="xl:col-span-2 rounded-xl border border-border bg-surface overflow-hidden">
            <div className="px-5 py-4 border-b border-border">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileText className="h-4 w-4 text-accent" />
                Quarterly Reports
              </h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-secondary">
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Fund
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Quarter
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    NAV
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    DPI
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    TVPI
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {lpReports.map((report) => {
                  const config = statusConfig[report.status];
                  const StatusIcon = config.icon;
                  return (
                    <tr
                      key={report.id}
                      className="border-b border-border-light hover:bg-surface-secondary/50 transition-colors"
                    >
                      <td className="px-5 py-3 font-medium text-foreground text-xs">
                        {report.fund}
                      </td>
                      <td className="px-5 py-3 text-xs text-foreground">
                        {report.quarter}
                      </td>
                      <td className="px-5 py-3">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${config.bg} ${config.text}`}
                        >
                          <StatusIcon className="h-3 w-3" />
                          {config.label}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-xs font-medium text-foreground">
                        {report.nav}
                      </td>
                      <td className="px-5 py-3 text-xs text-foreground">
                        {report.dpi}
                      </td>
                      <td className="px-5 py-3 text-xs font-semibold text-accent">
                        {report.tvpi}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1">
                          <button className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-surface-secondary text-muted hover:text-foreground transition-colors">
                            <Download className="h-3.5 w-3.5" />
                          </button>
                          {report.status === "review" && (
                            <button className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-accent-subtle text-accent transition-colors">
                              <Send className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* LP Card */}
          <div className="xl:col-span-1">
            <LPCard />
          </div>
        </div>

        {/* Fund Performance Chart */}
        <FundPerformanceChart />
      </div>
    </>
  );
}
