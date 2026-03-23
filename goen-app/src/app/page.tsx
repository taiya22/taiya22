"use client";

import { useState, useCallback, useEffect } from "react";
import { GoenData } from "@/types";
import { loadData, saveData } from "@/lib/storage";
import QuickInput from "@/components/QuickInput";
import Universe from "@/components/Universe";
import ReconnectPanel from "@/components/ReconnectPanel";
import RecentEncounters from "@/components/RecentEncounters";
import PeopleList from "@/components/PeopleList";
import Navigation from "@/components/Navigation";

// Demo data to show the app's potential on first load
function seedDemoData(): GoenData {
  const now = new Date();
  const daysAgo = (days: number) =>
    new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString();

  const persons = [
    { id: "p1", name: "田中", createdAt: daysAgo(120), tags: ["起業", "テクノロジー"] },
    { id: "p2", name: "鈴木", createdAt: daysAgo(90), tags: ["投資", "海外"] },
    { id: "p3", name: "山田", createdAt: daysAgo(60), tags: ["クリエイティブ", "学び"] },
    { id: "p4", name: "佐藤", createdAt: daysAgo(45), tags: ["起業", "投資"] },
    { id: "p5", name: "高橋", createdAt: daysAgo(200), tags: ["海外", "キャリア"] },
    { id: "p6", name: "伊藤", createdAt: daysAgo(10), tags: ["テクノロジー", "学び"] },
    { id: "p7", name: "渡辺", createdAt: daysAgo(150), tags: ["クリエイティブ"] },
  ];

  const encounters = [
    {
      id: "e1", text: "田中さんとランチ。AI事業の話で刺激を受けた。新しいプロダクトのアイデアが湧いた",
      personIds: ["p1"], personNames: ["田中"], tags: ["テクノロジー", "起業", "食事"],
      mood: "inspired" as const, createdAt: daysAgo(3),
    },
    {
      id: "e2", text: "鈴木さんから海外VCの紹介をいただいた。感謝しかない",
      personIds: ["p2"], personNames: ["鈴木"], tags: ["投資", "海外"],
      mood: "grateful" as const, createdAt: daysAgo(35),
    },
    {
      id: "e3", text: "山田さんのデザイン展に行った。クリエイティブの本質について深い対話",
      personIds: ["p3"], personNames: ["山田"], tags: ["クリエイティブ", "学び", "イベント"],
      mood: "thoughtful" as const, createdAt: daysAgo(15),
    },
    {
      id: "e4", text: "田中さんと佐藤さんの3人で起業について語った。熱い夜だった",
      personIds: ["p1", "p4"], personNames: ["田中", "佐藤"], tags: ["起業", "食事"],
      mood: "energized" as const, createdAt: daysAgo(20),
    },
    {
      id: "e5", text: "高橋さんと久しぶりに再会。シリコンバレーでの経験談が面白かった",
      personIds: ["p5"], personNames: ["高橋"], tags: ["海外", "キャリア"],
      mood: "inspired" as const, createdAt: daysAgo(100),
    },
    {
      id: "e6", text: "伊藤さんの勉強会に参加。AIエンジニアリングの最新トレンドを学んだ",
      personIds: ["p6"], personNames: ["伊藤"], tags: ["テクノロジー", "学び", "イベント"],
      mood: "energized" as const, createdAt: daysAgo(10),
    },
    {
      id: "e7", text: "渡辺さんのアート作品を見た。表現の幅に感動",
      personIds: ["p7"], personNames: ["渡辺"], tags: ["クリエイティブ"],
      mood: "inspired" as const, createdAt: daysAgo(150),
    },
    {
      id: "e8", text: "鈴木さんと佐藤さんの紹介で投資家ディナー。新しい世界が開けた",
      personIds: ["p2", "p4"], personNames: ["鈴木", "佐藤"], tags: ["投資", "食事"],
      mood: "grateful" as const, createdAt: daysAgo(50),
    },
    {
      id: "e9", text: "伊藤さんと山田さんでAI×デザインのブレスト。最高に楽しかった",
      personIds: ["p6", "p3"], personNames: ["伊藤", "山田"], tags: ["テクノロジー", "クリエイティブ"],
      mood: "warm" as const, createdAt: daysAgo(5),
    },
  ];

  return { persons, encounters };
}

export default function Home() {
  const [data, setData] = useState<GoenData>({ persons: [], encounters: [] });
  const [currentView, setCurrentView] = useState<"home" | "universe" | "people">("home");
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let stored = loadData();
    if (stored.persons.length === 0 && stored.encounters.length === 0) {
      stored = seedDemoData();
      saveData(stored);
    }
    setData(stored);
    setIsLoaded(true);
  }, []);

  const refresh = useCallback(() => {
    setData(loadData());
  }, []);

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-cosmos-dim animate-pulse text-xl">✦</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen pb-20">
      {/* Header */}
      <header className="pt-8 pb-4 px-6 text-center">
        <h1 className="text-2xl font-light tracking-widest text-cosmos-star/90">
          ご縁
        </h1>
        <p className="text-xs text-cosmos-dim/50 mt-1 tracking-wider">
          GOEN — your universe of connections
        </p>
      </header>

      {/* Views */}
      <div className="px-4">
        {currentView === "home" && (
          <div className="space-y-8">
            <QuickInput onEncounterAdded={refresh} />
            <ReconnectPanel data={data} />
            <RecentEncounters data={data} />
          </div>
        )}

        {currentView === "universe" && (
          <div className="h-[calc(100vh-160px)]">
            <Universe data={data} />
          </div>
        )}

        {currentView === "people" && (
          <PeopleList data={data} />
        )}
      </div>

      {/* Bottom Navigation */}
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
    </main>
  );
}
