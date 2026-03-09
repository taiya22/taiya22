"use client";

import { useState } from "react";
import Header from "@/components/Header";
import AIInsightCard from "@/components/AIInsightCard";
import { aiInsights } from "@/lib/mock-data";
import type { AIInsight } from "@/lib/mock-data";
import {
  Brain,
  MessageSquare,
  Send,
  Filter,
  Sparkles,
  FileSearch,
  Upload,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from "lucide-react";

const filterTypes = ["all", "risk", "opportunity", "alert", "recommendation"] as const;

function DDSimulator() {
  const [messages, setMessages] = useState<
    { role: "user" | "ai"; content: string }[]
  >([
    {
      role: "ai",
      content:
        "Hello, I'm your AI Due Diligence assistant. Upload documents or ask me questions about ongoing deals. I can analyze IMs, contracts, financial data, and more.",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    // Simulate AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: getSimulatedResponse(userMsg),
        },
      ]);
    }, 800);
  };

  return (
    <div className="rounded-xl border border-border bg-surface flex flex-col h-[600px]">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-border px-5 py-3">
        <Brain className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-semibold text-foreground">
          AI DD Assistant
        </h3>
        <span className="flex h-2 w-2 ml-1">
          <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-success opacity-75"></span>
          <span className="relative inline-flex h-2 w-2 rounded-full bg-success"></span>
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-accent text-white"
                  : "bg-surface-secondary text-foreground"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 px-5 py-2 overflow-x-auto">
        {[
          { icon: FileSearch, label: "Analyze IM" },
          { icon: Upload, label: "Upload Document" },
          { icon: AlertTriangle, label: "Red Flag Check" },
        ].map((action) => (
          <button
            key={action.label}
            className="flex items-center gap-1.5 shrink-0 rounded-lg border border-border px-3 py-1.5 text-[11px] font-medium text-muted hover:bg-surface-secondary hover:text-foreground transition-colors"
          >
            <action.icon className="h-3 w-3" />
            {action.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about a deal, request analysis..."
            className="flex-1 rounded-lg border border-border bg-surface-secondary px-4 py-2.5 text-sm text-foreground placeholder:text-muted-light outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition-colors"
          />
          <button
            onClick={handleSend}
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-white hover:bg-accent-light transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function getSimulatedResponse(query: string): string {
  const q = query.toLowerCase();
  if (q.includes("nexus") || q.includes("manufacturing")) {
    return "Nexus Precision Manufacturing — AI Score: 87/100\n\nKey findings from IM analysis:\n• Owner (age 68) seeking succession solution — strong alignment with our thesis\n• Niche market leader in precision parts for semiconductor equipment (32% domestic share)\n• EBITDA margin stable at 14.2% over 5 years\n• Red flags: Customer concentration (top 3 = 45%), aging facility infrastructure\n\nRecommendation: Proceed to DD with focus on customer contract durability and capex requirements.";
  }
  if (q.includes("risk") || q.includes("red flag")) {
    return "Cross-portfolio Red Flag Summary:\n\n1. Kanto Chemical — CRITICAL: Covenant breach projected Q2 2026 (Net Debt/EBITDA 5.2x)\n2. Horizon Medical — MODERATE: Key customer contract renewal uncertainty\n3. GreenLogix (Pipeline) — HIGH: 62% customer concentration, no LTA with top customer\n\nI recommend prioritizing the Kanto Chemical situation. Shall I draft a lender communication strategy?";
  }
  if (q.includes("cloudbridge") || q.includes("saas")) {
    return "CloudBridge Solutions — Valuation Analysis:\n\nDCF (WACC 9.5%): ¥7.8B - ¥9.1B\nComps (EV/Revenue): ¥8.0B - ¥9.5B\nLBO (Target IRR 20%): Max bid ¥8.4B\n\nKey value driver: 85% recurring revenue with 118% net retention. SaaS multiples currently elevated (12.3x median). The AI model suggests a fair bid range of ¥7.5B - ¥8.5B with 15-22% expected IRR.";
  }
  return "I've analyzed your query. Based on our current deal pipeline and portfolio data, here are my key observations:\n\n• Current pipeline has 23 active deals with average AI score of 80\n• 3 deals are in advanced stages (IC/Execution)\n• Portfolio monitoring has flagged 5 alerts requiring attention\n\nWould you like me to dive deeper into any specific deal or generate a detailed report?";
}

// DD Progress tracker
function DDTracker() {
  const ddItems = [
    { name: "Financial DD", status: "complete", progress: 100 },
    { name: "Legal DD", status: "in-progress", progress: 72 },
    { name: "Business DD", status: "in-progress", progress: 58 },
    { name: "Tax DD", status: "in-progress", progress: 45 },
    { name: "IT/Cyber DD", status: "pending", progress: 10 },
    { name: "ESG DD", status: "pending", progress: 0 },
  ];

  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <h3 className="text-sm font-semibold text-foreground mb-1">
        DD Progress — Nexus Precision
      </h3>
      <p className="text-xs text-muted mb-4">AI-assisted due diligence tracking</p>
      <div className="space-y-3">
        {ddItems.map((item) => (
          <div key={item.name} className="flex items-center gap-3">
            {item.status === "complete" ? (
              <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
            ) : item.status === "in-progress" ? (
              <Clock className="h-4 w-4 text-accent shrink-0" />
            ) : (
              <div className="h-4 w-4 rounded-full border-2 border-border shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-foreground">
                  {item.name}
                </span>
                <span className="text-[10px] text-muted">{item.progress}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-surface-secondary overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    item.status === "complete"
                      ? "bg-success"
                      : item.status === "in-progress"
                      ? "bg-accent"
                      : "bg-border"
                  }`}
                  style={{ width: `${item.progress}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AIInsightsPage() {
  const [activeFilter, setActiveFilter] = useState<string>("all");

  const filteredInsights =
    activeFilter === "all"
      ? aiInsights
      : aiInsights.filter((i) => i.type === activeFilter);

  return (
    <>
      <Header title="AI Insights" />
      <div className="p-6 space-y-6">
        {/* Top Row: DD Assistant + DD Tracker */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <DDSimulator />
          </div>
          <div className="xl:col-span-1">
            <DDTracker />
          </div>
        </div>

        {/* Insights Feed */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <h2 className="text-sm font-semibold text-foreground">
                AI Insights Feed
              </h2>
              <span className="text-xs text-muted">
                ({filteredInsights.length})
              </span>
            </div>
            {/* Filters */}
            <div className="flex items-center gap-1">
              <Filter className="h-3.5 w-3.5 text-muted mr-1" />
              {filterTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => setActiveFilter(type)}
                  className={`rounded-lg px-3 py-1.5 text-[11px] font-medium transition-colors ${
                    activeFilter === type
                      ? "bg-accent text-white"
                      : "bg-surface-secondary text-muted hover:text-foreground"
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {filteredInsights.map((insight) => (
              <AIInsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
