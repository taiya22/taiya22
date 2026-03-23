export interface Person {
  id: string;
  name: string;
  createdAt: string;
  tags: string[];
}

export interface Encounter {
  id: string;
  text: string;
  personIds: string[];
  personNames: string[];
  tags: string[];
  mood: "inspired" | "grateful" | "energized" | "thoughtful" | "warm" | "neutral";
  createdAt: string;
}

export interface GoenData {
  persons: Person[];
  encounters: Encounter[];
}

export interface StarNode {
  id: string;
  name: string;
  encounters: number;
  lastSeen: string;
  tags: string[];
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface StarLink {
  source: string | StarNode;
  target: string | StarNode;
  strength: number;
  sharedTags: string[];
}

export interface ReconnectSuggestion {
  person: Person;
  daysSinceLastSeen: number;
  lastEncounter: Encounter;
  reason: string;
}
