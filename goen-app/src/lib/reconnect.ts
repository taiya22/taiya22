import { GoenData, ReconnectSuggestion } from "@/types";

export function getReconnectSuggestions(data: GoenData, limit = 5): ReconnectSuggestion[] {
  const now = new Date();
  const suggestions: ReconnectSuggestion[] = [];

  for (const person of data.persons) {
    const encounters = data.encounters
      .filter((e) => e.personIds.includes(person.id))
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    if (encounters.length === 0) continue;

    const lastEncounter = encounters[0];
    const lastDate = new Date(lastEncounter.createdAt);
    const daysSince = Math.floor((now.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));

    // Suggest reconnect if more than 30 days since last encounter
    if (daysSince >= 30) {
      const reason = buildReason(lastEncounter, daysSince, encounters.length);
      suggestions.push({
        person,
        daysSinceLastSeen: daysSince,
        lastEncounter,
        reason,
      });
    }
  }

  // Sort by a blend of recency and encounter frequency
  return suggestions
    .sort((a, b) => {
      const scoreA = a.daysSinceLastSeen * 0.7 + (1 / (getEncounterCount(data, a.person.id) + 1)) * 100;
      const scoreB = b.daysSinceLastSeen * 0.7 + (1 / (getEncounterCount(data, b.person.id) + 1)) * 100;
      return scoreB - scoreA;
    })
    .slice(0, limit);
}

function getEncounterCount(data: GoenData, personId: string): number {
  return data.encounters.filter((e) => e.personIds.includes(personId)).length;
}

function buildReason(lastEncounter: import("@/types").Encounter, daysSince: number, totalEncounters: number): string {
  const months = Math.floor(daysSince / 30);
  const timeText = months >= 2 ? `${months}ヶ月前` : `${daysSince}日前`;

  const lastText = lastEncounter.text.length > 40
    ? lastEncounter.text.slice(0, 40) + "..."
    : lastEncounter.text;

  const frequencyText = totalEncounters >= 5
    ? "よくお会いしていた方です。"
    : totalEncounters >= 2
    ? ""
    : "一度きりの出会い、大切にしたいですね。";

  return `最後にお会いしたのは${timeText}。「${lastText}」${frequencyText}`;
}
