"use client";

import Header from "@/components/Header";
import { MiniSparkline } from "@/components/Charts";
import { portfolioCompanies } from "@/lib/mock-data";
import type { PortfolioCompany } from "@/lib/mock-data";
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  TrendingUp,
  TrendingDown,
  Building2,
  Calendar,
  DollarSign,
} from "lucide-react";

const statusConfig = {
  "on-track": {
    icon: CheckCircle2,
    label: "On Track",
    bg: "bg-success-subtle",
    text: "text-success",
    border: "border-success/20",
  },
  watch: {
    icon: Eye,
    label: "Watch",
    bg: "bg-warning-subtle",
    text: "text-warning",
    border: "border-warning/20",
  },
  "at-risk": {
    icon: AlertTriangle,
    label: "At Risk",
    bg: "bg-danger-subtle",
    text: "text-danger",
    border: "border-danger/20",
  },
};

function PortfolioCard({ company }: { company: PortfolioCompany }) {
  const config = statusConfig[company.status];
  const Icon = config.icon;
  const isGrowth = company.moic >= 1.3;

  return (
    <div
      className={`rounded-xl border ${config.border} bg-surface p-5 hover:shadow-md transition-shadow`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            {company.name}
          </h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[11px] text-muted flex items-center gap-1">
              <Building2 className="h-3 w-3" />
              {company.sector}
            </span>
            <span className="text-[11px] text-muted flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {company.investmentDate}
            </span>
          </div>
        </div>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-semibold ${config.bg} ${config.text}`}
        >
          <Icon className="h-3 w-3" />
          {config.label}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div>
          <p className="text-[10px] text-muted uppercase tracking-wider">
            Invested
          </p>
          <p className="text-sm font-semibold text-foreground mt-0.5">
            {company.investedAmount}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted uppercase tracking-wider">
            Current
          </p>
          <p className="text-sm font-semibold text-foreground mt-0.5">
            {company.currentValue}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted uppercase tracking-wider">
            MOIC
          </p>
          <p
            className={`text-sm font-semibold mt-0.5 flex items-center gap-1 ${
              isGrowth ? "text-success" : "text-warning"
            }`}
          >
            {isGrowth ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {company.moic.toFixed(2)}x
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted uppercase tracking-wider">
            IRR
          </p>
          <p
            className={`text-sm font-semibold mt-0.5 ${
              company.irr >= 15 ? "text-success" : company.irr >= 8 ? "text-foreground" : "text-danger"
            }`}
          >
            {company.irr.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Sparklines */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-lg bg-surface-secondary p-3">
          <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
            Revenue Trend
          </p>
          <MiniSparkline
            data={company.revenue}
            color={
              company.revenue[company.revenue.length - 1] >
              company.revenue[0]
                ? "#16a34a"
                : "#dc2626"
            }
          />
        </div>
        <div className="rounded-lg bg-surface-secondary p-3">
          <p className="text-[10px] text-muted uppercase tracking-wider mb-1">
            EBITDA Trend
          </p>
          <MiniSparkline
            data={company.ebitda}
            color={
              company.ebitda[company.ebitda.length - 1] >
              company.ebitda[0]
                ? "#2563eb"
                : "#dc2626"
            }
          />
        </div>
      </div>

      {/* AI Alerts */}
      {company.aiAlerts.length > 0 && (
        <div className="space-y-1.5">
          {company.aiAlerts.map((alert, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded-lg bg-danger-subtle px-3 py-2"
            >
              <AlertTriangle className="h-3 w-3 text-danger mt-0.5 shrink-0" />
              <p className="text-[11px] text-danger leading-relaxed">
                {alert}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PortfolioPage() {
  const totalInvested = "¥31.7B";
  const totalValue = "¥46.3B";
  const avgMOIC = (
    portfolioCompanies.reduce((s, c) => s + c.moic, 0) /
    portfolioCompanies.length
  ).toFixed(2);

  return (
    <>
      <Header title="Portfolio Monitoring" />
      <div className="p-6 space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <div className="rounded-xl border border-border bg-surface p-4">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Companies
            </p>
            <p className="text-xl font-bold text-foreground mt-1">
              {portfolioCompanies.length}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Total Invested
            </p>
            <p className="text-xl font-bold text-foreground mt-1">
              {totalInvested}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Current Value
            </p>
            <p className="text-xl font-bold text-success mt-1 flex items-center gap-1">
              <DollarSign className="h-4 w-4" />
              {totalValue}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Avg MOIC
            </p>
            <p className="text-xl font-bold text-accent mt-1">{avgMOIC}x</p>
          </div>
          <div className="rounded-xl border border-border bg-surface p-4">
            <p className="text-[10px] text-muted uppercase tracking-wider">
              Active Alerts
            </p>
            <p className="text-xl font-bold text-danger mt-1">
              {portfolioCompanies.reduce(
                (s, c) => s + c.aiAlerts.length,
                0
              )}
            </p>
          </div>
        </div>

        {/* Company Cards */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {portfolioCompanies.map((company) => (
            <PortfolioCard key={company.id} company={company} />
          ))}
        </div>
      </div>
    </>
  );
}
