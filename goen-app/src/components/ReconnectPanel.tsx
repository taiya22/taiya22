"use client";

import { GoenData, ReconnectSuggestion } from "@/types";
import { getReconnectSuggestions } from "@/lib/reconnect";

interface ReconnectPanelProps {
  data: GoenData;
}

const MOOD_EMOJI: Record<string, string> = {
  inspired: "✨",
  grateful: "🙏",
  energized: "⚡",
  thoughtful: "💭",
  warm: "☀️",
  neutral: "◦",
};

export default function ReconnectPanel({ data }: ReconnectPanelProps) {
  const suggestions = getReconnectSuggestions(data);

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h2 className="text-sm font-medium text-cosmos-dim mb-3 tracking-wider uppercase">
        久しぶりのご縁
      </h2>
      <div className="space-y-3">
        {suggestions.map((suggestion) => (
          <SuggestionCard key={suggestion.person.id} suggestion={suggestion} />
        ))}
      </div>
    </div>
  );
}

function SuggestionCard({ suggestion }: { suggestion: ReconnectSuggestion }) {
  const { person, daysSinceLastSeen, lastEncounter, reason } = suggestion;
  const months = Math.floor(daysSinceLastSeen / 30);

  return (
    <div className="bg-cosmos-surface/50 border border-cosmos-dim/20 rounded-xl p-4 hover:border-cosmos-accent/30 hover:glow transition-all duration-300 cursor-default group">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-cosmos-star font-medium">{person.name}</span>
            <span className="text-xs text-cosmos-dim">
              {months >= 2 ? `${months}ヶ月` : `${daysSinceLastSeen}日`}
            </span>
          </div>
          <p className="text-sm text-cosmos-dim/80 mt-1.5 leading-relaxed">
            {reason}
          </p>
          {lastEncounter.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {lastEncounter.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-0.5 rounded-full bg-cosmos-warm/10 text-cosmos-warm/70 text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        <span className="text-lg opacity-50 group-hover:opacity-100 transition-opacity">
          {MOOD_EMOJI[lastEncounter.mood] || "◦"}
        </span>
      </div>
    </div>
  );
}
