import { GoenData, Person, Encounter } from "@/types";

const STORAGE_KEY = "goen-data";

function getDefaultData(): GoenData {
  return { persons: [], encounters: [] };
}

export function loadData(): GoenData {
  if (typeof window === "undefined") return getDefaultData();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return getDefaultData();
    return JSON.parse(raw) as GoenData;
  } catch {
    return getDefaultData();
  }
}

export function saveData(data: GoenData): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function addPerson(name: string, tags: string[] = []): Person {
  const data = loadData();
  const existing = data.persons.find(
    (p) => p.name.toLowerCase() === name.toLowerCase()
  );
  if (existing) return existing;

  const person: Person = {
    id: crypto.randomUUID(),
    name,
    createdAt: new Date().toISOString(),
    tags,
  };
  data.persons.push(person);
  saveData(data);
  return person;
}

export function addEncounter(encounter: Omit<Encounter, "id">): Encounter {
  const data = loadData();
  const full: Encounter = {
    ...encounter,
    id: crypto.randomUUID(),
  };
  data.encounters.push(full);
  saveData(data);
  return full;
}

export function getPersonEncounters(personId: string): Encounter[] {
  const data = loadData();
  return data.encounters
    .filter((e) => e.personIds.includes(personId))
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}

export function deletePerson(personId: string): void {
  const data = loadData();
  data.persons = data.persons.filter((p) => p.id !== personId);
  data.encounters = data.encounters.map((e) => ({
    ...e,
    personIds: e.personIds.filter((id) => id !== personId),
  }));
  saveData(data);
}

export function deleteEncounter(encounterId: string): void {
  const data = loadData();
  data.encounters = data.encounters.filter((e) => e.id !== encounterId);
  saveData(data);
}
