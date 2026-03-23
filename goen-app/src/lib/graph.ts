import { GoenData, StarNode, StarLink } from "@/types";

export function buildGraph(data: GoenData): { nodes: StarNode[]; links: StarLink[] } {
  const nodes: StarNode[] = [];
  const linkMap = new Map<string, { strength: number; sharedTags: Set<string> }>();

  for (const person of data.persons) {
    const personEncounters = data.encounters.filter((e) =>
      e.personIds.includes(person.id)
    );
    const allTags = personEncounters.flatMap((e) => e.tags);
    const lastEncounter = personEncounters.sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    )[0];

    nodes.push({
      id: person.id,
      name: person.name,
      encounters: personEncounters.length,
      lastSeen: lastEncounter?.createdAt || person.createdAt,
      tags: Array.from(new Set(allTags)),
    });
  }

  // Build co-occurrence links: people who appear in the same encounter
  for (const encounter of data.encounters) {
    const ids = encounter.personIds;
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const key = [ids[i], ids[j]].sort().join("-");
        const existing = linkMap.get(key);
        if (existing) {
          existing.strength += 1;
          encounter.tags.forEach((t) => existing.sharedTags.add(t));
        } else {
          linkMap.set(key, {
            strength: 1,
            sharedTags: new Set(encounter.tags),
          });
        }
      }
    }
  }

  const links: StarLink[] = [];
  linkMap.forEach((value, key) => {
    const [source, target] = key.split("-");
    links.push({
      source,
      target,
      strength: value.strength,
      sharedTags: Array.from(value.sharedTags),
    });
  });

  return { nodes, links };
}

export function getConstellations(data: GoenData): Map<string, string[]> {
  const tagToPersons = new Map<string, Set<string>>();

  for (const encounter of data.encounters) {
    for (const tag of encounter.tags) {
      if (!tagToPersons.has(tag)) tagToPersons.set(tag, new Set());
      for (const personId of encounter.personIds) {
        tagToPersons.get(tag)!.add(personId);
      }
    }
  }

  const constellations = new Map<string, string[]>();
  tagToPersons.forEach((personIds, tag) => {
    if (personIds.size >= 2) {
      constellations.set(tag, Array.from(personIds));
    }
  });

  return constellations;
}
