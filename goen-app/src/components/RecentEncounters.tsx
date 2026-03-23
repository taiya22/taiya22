"use client";

import { GoenData } from "@/types";

interface RecentEncountersProps {
  data: GoenData;
}

const MOOD_COLORS: Record<string, string> = {
  inspired: "border-purple-500/30",
  grateful: "border-emerald-500/30",
  energized: "border-amber-500/30",
  thoughtful: "border-blue-500/30",
  warm: "border-orange-500/30",
  neutral: "border-cosmos-dim/20",
};

export default function RecentEncounters({ data }: RecentEncountersProps) {
  const recent = [...data.encounters]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 10);

  if (recent.length === 0) return null;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h2 className="text-sm font-medium text-cosmos-dim mb-3 tracking-wider uppercase">
        最近の記録
      </h2>
      <div className="space-y-2">
        {recent.map((encounter) => {
          const date = new Date(encounter.createdAt);
          const isToday = new Date().toDateString() === date.toDateString();
          const borderColor = MOOD_COLORS[encounter.mood] || MOOD_COLORS.neutral;

          return (
            <div
              key={encounter.id}
              className={`bg-cosmos-surface/30 border-l-2 ${borderColor} rounded-r-lg px-4 py-3`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-cosmos-dim">
                  {isToday
                    ? "今日"
                    : date.toLocaleDateString("ja-JP", {
                        month: "short",
                        day: "numeric",
                      })}
                </span>
                {encounter.personNames.map((name) => (
                  <span
                    key={name}
                    className="px-2 py-0.5 rounded-full bg-cosmos-accent/10 text-cosmos-glow text-xs"
                  >
                    {name}
                  </span>
                ))}
              </div>
              <p className="text-sm text-cosmos-star/80">{encounter.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
