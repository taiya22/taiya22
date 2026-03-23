"use client";

interface NavigationProps {
  currentView: "home" | "universe" | "people";
  onViewChange: (view: "home" | "universe" | "people") => void;
}

export default function Navigation({ currentView, onViewChange }: NavigationProps) {
  const tabs = [
    { id: "home" as const, label: "ホーム", icon: HomeIcon },
    { id: "universe" as const, label: "ユニバース", icon: UniverseIcon },
    { id: "people" as const, label: "ご縁", icon: PeopleIcon },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-cosmos-surface/80 backdrop-blur-lg border-t border-cosmos-dim/20 z-50">
      <div className="max-w-2xl mx-auto flex">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onViewChange(tab.id)}
            className={`flex-1 flex flex-col items-center gap-1 py-3 transition-all duration-300 ${
              currentView === tab.id
                ? "text-cosmos-accent"
                : "text-cosmos-dim hover:text-cosmos-star/60"
            }`}
          >
            <tab.icon active={currentView === tab.id} />
            <span className="text-xs">{tab.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}

function HomeIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.5 : 1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function UniverseIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.5 : 1.5} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="4" />
      <line x1="21.17" x2="12" y1="8" y2="8" />
      <line x1="3.95" x2="8.54" y1="6.06" y2="14" />
      <line x1="10.88" x2="15.46" y1="21.94" y2="14" />
    </svg>
  );
}

function PeopleIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.5 : 1.5} strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
