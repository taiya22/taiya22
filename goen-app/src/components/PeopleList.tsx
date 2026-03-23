"use client";

import { GoenData } from "@/types";

interface PeopleListProps {
  data: GoenData;
}

export default function PeopleList({ data }: PeopleListProps) {
  const people = data.persons.map((person) => {
    const encounters = data.encounters
      .filter((e) => e.personIds.includes(person.id))
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    const lastEncounter = encounters[0];
    const allTags = Array.from(new Set(encounters.flatMap((e) => e.tags)));
    return { person, encounters, lastEncounter, allTags };
  }).sort((a, b) => {
    const dateA = a.lastEncounter ? new Date(a.lastEncounter.createdAt).getTime() : 0;
    const dateB = b.lastEncounter ? new Date(b.lastEncounter.createdAt).getTime() : 0;
    return dateB - dateA;
  });

  if (people.length === 0) {
    return (
      <div className="text-center text-cosmos-dim/60 py-20">
        <div className="text-5xl mb-4">✦</div>
        <p>まだ誰も記録されていません</p>
        <p className="text-sm mt-1">ホームから最初のご縁を記録しましょう</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <h2 className="text-sm font-medium text-cosmos-dim mb-4 tracking-wider uppercase">
        {people.length}人のご縁
      </h2>
      <div className="space-y-2">
        {people.map(({ person, encounters, lastEncounter, allTags }) => {
          const daysSince = lastEncounter
            ? Math.floor(
                (Date.now() - new Date(lastEncounter.createdAt).getTime()) /
                  (1000 * 60 * 60 * 24)
              )
            : null;

          return (
            <div
              key={person.id}
              className="bg-cosmos-surface/40 border border-cosmos-dim/15 rounded-xl p-4 hover:border-cosmos-accent/20 transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-cosmos-star font-medium">{person.name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-cosmos-dim">
                      {encounters.length}回の出会い
                    </span>
                    {daysSince !== null && (
                      <span className="text-xs text-cosmos-dim">
                        {daysSince === 0
                          ? "今日"
                          : daysSince < 30
                          ? `${daysSince}日前`
                          : `${Math.floor(daysSince / 30)}ヶ月前`}
                      </span>
                    )}
                  </div>
                </div>
                {/* Brightness indicator */}
                <div
                  className="w-3 h-3 rounded-full mt-1"
                  style={{
                    backgroundColor:
                      daysSince !== null && daysSince < 7
                        ? "#f0f0ff"
                        : daysSince !== null && daysSince < 30
                        ? "#818cf8"
                        : daysSince !== null && daysSince < 90
                        ? "#6366f1"
                        : "#4a4a6a",
                    boxShadow:
                      daysSince !== null && daysSince < 7
                        ? "0 0 8px rgba(240,240,255,0.5)"
                        : "none",
                  }}
                />
              </div>
              {allTags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {allTags.slice(0, 5).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded-full bg-cosmos-accent/10 text-cosmos-glow/70 text-xs"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {lastEncounter && (
                <p className="text-xs text-cosmos-dim/60 mt-2 truncate">
                  {lastEncounter.text}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
