// Lightweight local extraction of person names, tags, and mood from free text.
// No external API needed — uses heuristics and pattern matching.

const MOOD_KEYWORDS: Record<string, string[]> = {
  inspired: ["刺激", "インスパイア", "inspired", "目から鱗", "衝撃", "すごい", "感動"],
  grateful: ["感謝", "ありがたい", "grateful", "おかげ", "助けて", "救われ"],
  energized: ["元気", "やる気", "energized", "モチベ", "燃えた", "熱い", "パワー"],
  thoughtful: ["考えさせ", "深い", "thoughtful", "哲学", "本質", "気づき", "学び"],
  warm: ["温かい", "嬉しい", "楽しい", "warm", "幸せ", "笑", "和やか"],
};

export function extractMood(text: string): "inspired" | "grateful" | "energized" | "thoughtful" | "warm" | "neutral" {
  for (const [mood, keywords] of Object.entries(MOOD_KEYWORDS)) {
    if (keywords.some((k) => text.includes(k))) {
      return mood as "inspired" | "grateful" | "energized" | "thoughtful" | "warm";
    }
  }
  return "neutral";
}

// Extract person names from text using common Japanese patterns
// Matches: ◯◯さん, ◯◯くん, ◯◯氏, ◯◯先生, @name, etc.
const NAME_PATTERNS = [
  /([一-龥ぁ-んァ-ヶA-Za-z]{1,10}?)(?:さん|くん|ちゃん|氏|先生|社長|部長|課長|代表)/g,
  /@([A-Za-zぁ-んァ-ヶ一-龥_]{2,15})/g,
];

export function extractPersonNames(text: string): string[] {
  const names = new Set<string>();
  for (const pattern of NAME_PATTERNS) {
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const name = match[1].trim();
      if (name.length >= 1) {
        names.add(name);
      }
    }
  }
  return Array.from(names);
}

// Extract tags/keywords from text
const TAG_PATTERNS = [
  /#([A-Za-zぁ-んァ-ヶ一-龥_]+)/g,
];

const AUTO_TAG_KEYWORDS: Record<string, string[]> = {
  "起業": ["起業", "スタートアップ", "創業", "ビジネス"],
  "キャリア": ["転職", "キャリア", "仕事", "就職"],
  "海外": ["海外", "留学", "グローバル", "英語"],
  "テクノロジー": ["AI", "テック", "エンジニア", "プログラミング", "開発"],
  "クリエイティブ": ["デザイン", "アート", "クリエイティブ", "音楽", "写真"],
  "投資": ["投資", "資金", "ファンド", "VC"],
  "学び": ["勉強", "学び", "読書", "セミナー", "研修"],
  "食事": ["ランチ", "ディナー", "飲み", "食事", "カフェ", "コーヒー"],
  "イベント": ["イベント", "カンファレンス", "勉強会", "meetup", "交流会"],
};

export function extractTags(text: string): string[] {
  const tags = new Set<string>();

  // Explicit hashtags
  for (const pattern of TAG_PATTERNS) {
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      tags.add(match[1]);
    }
  }

  // Auto-detected tags
  for (const [tag, keywords] of Object.entries(AUTO_TAG_KEYWORDS)) {
    if (keywords.some((k) => text.toLowerCase().includes(k.toLowerCase()))) {
      tags.add(tag);
    }
  }

  return Array.from(tags);
}
