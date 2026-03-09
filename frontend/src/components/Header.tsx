"use client";

import { Bell, Search, Sparkles } from "lucide-react";

export default function Header({ title }: { title: string }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-surface/80 backdrop-blur-sm px-6">
      <h1 className="text-lg font-semibold text-foreground">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-light" />
          <input
            type="text"
            placeholder="Search deals, companies..."
            className="h-9 w-64 rounded-lg border border-border bg-surface-secondary pl-9 pr-4 text-sm text-foreground placeholder:text-muted-light outline-none focus:border-accent focus:ring-1 focus:ring-accent/20 transition-colors"
          />
        </div>

        {/* AI Status */}
        <button className="flex items-center gap-2 rounded-lg border border-accent/20 bg-accent-subtle px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent-muted">
          <Sparkles className="h-3.5 w-3.5" />
          <span>AI Active</span>
          <span className="flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent"></span>
          </span>
        </button>

        {/* Notifications */}
        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted hover:bg-surface-secondary hover:text-foreground transition-colors">
          <Bell className="h-4 w-4" />
          <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-white">
            5
          </span>
        </button>

        {/* Avatar */}
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-foreground text-surface text-xs font-semibold">
          TK
        </div>
      </div>
    </header>
  );
}
