// ============================================================
// Mock Data for Taiga Capital PE Investment AI Platform
// ============================================================

export interface KPI {
  label: string;
  value: string;
  change: number;
  unit?: string;
}

export interface Deal {
  id: string;
  company: string;
  sector: string;
  stage: "sourcing" | "screening" | "dd" | "valuation" | "ic" | "execution" | "closed";
  aiScore: number;
  ev: string;
  ebitda: string;
  multiple: string;
  assignee: string;
  updatedAt: string;
  flags: string[];
}

export interface PortfolioCompany {
  id: string;
  name: string;
  sector: string;
  investmentDate: string;
  investedAmount: string;
  currentValue: string;
  moic: number;
  irr: number;
  revenue: number[];
  ebitda: number[];
  status: "on-track" | "watch" | "at-risk";
  aiAlerts: string[];
}

export interface LPReport {
  id: string;
  fund: string;
  quarter: string;
  status: "draft" | "review" | "sent";
  nav: string;
  dpi: string;
  tvpi: string;
  generatedAt: string;
}

export interface AIInsight {
  id: string;
  type: "risk" | "opportunity" | "alert" | "recommendation";
  title: string;
  description: string;
  confidence: number;
  source: string;
  timestamp: string;
  relatedDeal?: string;
}

// ---- Dashboard KPIs ----
export const dashboardKPIs: KPI[] = [
  { label: "AUM", value: "¥248.5B", change: 12.3 },
  { label: "Active Deals", value: "23", change: 4.5 },
  { label: "Portfolio IRR", value: "18.7%", change: 2.1 },
  { label: "Fund III TVPI", value: "1.62x", change: 0.08 },
  { label: "AI Insights Today", value: "47", change: 15.0 },
  { label: "DD in Progress", value: "5", change: -1.0 },
];

// ---- Deal Pipeline ----
export const deals: Deal[] = [
  {
    id: "D-001",
    company: "Nexus Precision Manufacturing",
    sector: "Industrial / Manufacturing",
    stage: "dd",
    aiScore: 87,
    ev: "¥12.5B",
    ebitda: "¥1.8B",
    multiple: "6.9x",
    assignee: "Tanaka",
    updatedAt: "2026-03-08",
    flags: ["Owner Age 68", "Niche Top Share"],
  },
  {
    id: "D-002",
    company: "CloudBridge Solutions",
    sector: "Technology / SaaS",
    stage: "valuation",
    aiScore: 92,
    ev: "¥8.2B",
    ebitda: "¥1.2B",
    multiple: "6.8x",
    assignee: "Yamamoto",
    updatedAt: "2026-03-07",
    flags: ["High Growth", "Recurring Revenue 85%"],
  },
  {
    id: "D-003",
    company: "Sakura Healthcare Group",
    sector: "Healthcare",
    stage: "screening",
    aiScore: 74,
    ev: "¥18.0B",
    ebitda: "¥2.5B",
    multiple: "7.2x",
    assignee: "Suzuki",
    updatedAt: "2026-03-09",
    flags: ["Aging Population Tailwind"],
  },
  {
    id: "D-004",
    company: "GreenLogix Corp",
    sector: "Logistics / Supply Chain",
    stage: "sourcing",
    aiScore: 68,
    ev: "¥6.8B",
    ebitda: "¥0.9B",
    multiple: "7.6x",
    assignee: "Ito",
    updatedAt: "2026-03-09",
    flags: ["EV Transition", "Customer Concentration Risk"],
  },
  {
    id: "D-005",
    company: "Tokyo Food Technologies",
    sector: "Food & Beverage",
    stage: "ic",
    aiScore: 81,
    ev: "¥15.3B",
    ebitda: "¥2.1B",
    multiple: "7.3x",
    assignee: "Tanaka",
    updatedAt: "2026-03-06",
    flags: ["Export Growth Potential"],
  },
  {
    id: "D-006",
    company: "Matic Robotics",
    sector: "Technology / Robotics",
    stage: "sourcing",
    aiScore: 79,
    ev: "¥4.5B",
    ebitda: "¥0.6B",
    multiple: "7.5x",
    assignee: "Yamamoto",
    updatedAt: "2026-03-08",
    flags: ["Labor Shortage Theme"],
  },
  {
    id: "D-007",
    company: "Pacific Building Materials",
    sector: "Construction",
    stage: "screening",
    aiScore: 63,
    ev: "¥9.1B",
    ebitda: "¥1.3B",
    multiple: "7.0x",
    assignee: "Suzuki",
    updatedAt: "2026-03-05",
    flags: ["Cyclical Risk", "Strong Asset Base"],
  },
  {
    id: "D-008",
    company: "Aether Semiconductors",
    sector: "Technology / Semiconductor",
    stage: "execution",
    aiScore: 90,
    ev: "¥22.0B",
    ebitda: "¥3.8B",
    multiple: "5.8x",
    assignee: "Tanaka",
    updatedAt: "2026-03-04",
    flags: ["SPA Signed", "Closing Q2"],
  },
  {
    id: "D-009",
    company: "Wellness Connect",
    sector: "Healthcare / Digital",
    stage: "dd",
    aiScore: 76,
    ev: "¥5.5B",
    ebitda: "¥0.7B",
    multiple: "7.9x",
    assignee: "Ito",
    updatedAt: "2026-03-08",
    flags: ["Regulatory Pending"],
  },
  {
    id: "D-010",
    company: "Atlas Industrial Services",
    sector: "Industrial Services",
    stage: "closed",
    aiScore: 85,
    ev: "¥14.0B",
    ebitda: "¥2.0B",
    multiple: "7.0x",
    assignee: "Tanaka",
    updatedAt: "2026-02-28",
    flags: ["Fund III Portfolio"],
  },
];

// ---- Portfolio Companies ----
export const portfolioCompanies: PortfolioCompany[] = [
  {
    id: "P-001",
    name: "Atlas Industrial Services",
    sector: "Industrial Services",
    investmentDate: "2024-06",
    investedAmount: "¥5.2B",
    currentValue: "¥8.9B",
    moic: 1.71,
    irr: 28.5,
    revenue: [4200, 4500, 4800, 5100, 5500, 5800],
    ebitda: [620, 680, 730, 790, 850, 920],
    status: "on-track",
    aiAlerts: [],
  },
  {
    id: "P-002",
    name: "Horizon Medical Devices",
    sector: "Healthcare",
    investmentDate: "2023-09",
    investedAmount: "¥7.8B",
    currentValue: "¥11.2B",
    moic: 1.44,
    irr: 16.2,
    revenue: [6800, 7100, 7400, 7200, 7500, 7800],
    ebitda: [980, 1020, 1080, 1010, 1060, 1120],
    status: "watch",
    aiAlerts: ["Revenue dip detected in Q3 2025", "Key customer contract renewal pending"],
  },
  {
    id: "P-003",
    name: "Digital Frontier Inc.",
    sector: "Technology / SaaS",
    investmentDate: "2024-01",
    investedAmount: "¥3.5B",
    currentValue: "¥6.8B",
    moic: 1.94,
    irr: 42.1,
    revenue: [1800, 2200, 2700, 3200, 3800, 4500],
    ebitda: [180, 280, 390, 520, 680, 850],
    status: "on-track",
    aiAlerts: [],
  },
  {
    id: "P-004",
    name: "Kanto Chemical Industries",
    sector: "Chemicals",
    investmentDate: "2022-12",
    investedAmount: "¥9.2B",
    currentValue: "¥10.1B",
    moic: 1.10,
    irr: 3.2,
    revenue: [12000, 11500, 11800, 11200, 10900, 10500],
    ebitda: [1800, 1650, 1700, 1550, 1480, 1380],
    status: "at-risk",
    aiAlerts: [
      "EBITDA declining 3 consecutive quarters",
      "Raw material cost surge +18% YoY",
      "Covenant breach risk: Net Debt/EBITDA approaching 5.0x",
    ],
  },
  {
    id: "P-005",
    name: "Premier Logistics Group",
    sector: "Logistics",
    investmentDate: "2023-04",
    investedAmount: "¥6.0B",
    currentValue: "¥9.3B",
    moic: 1.55,
    irr: 20.8,
    revenue: [8500, 8900, 9400, 9800, 10200, 10800],
    ebitda: [1100, 1180, 1260, 1350, 1420, 1510],
    status: "on-track",
    aiAlerts: [],
  },
];

// ---- AI Insights ----
export const aiInsights: AIInsight[] = [
  {
    id: "AI-001",
    type: "risk",
    title: "Covenant Breach Risk — Kanto Chemical",
    description:
      "Net Debt/EBITDA ratio projected to reach 5.2x by Q2 2026 based on current trajectory. Recommend initiating lender discussion for covenant waiver or amendment.",
    confidence: 89,
    source: "Financial Monitoring Agent",
    timestamp: "2026-03-09 08:15",
    relatedDeal: "P-004",
  },
  {
    id: "AI-002",
    type: "opportunity",
    title: "Cross-sell Synergy: Atlas × Premier Logistics",
    description:
      "Atlas Industrial Services and Premier Logistics share 12 common customers. Bundled service offering could generate estimated ¥340M incremental revenue.",
    confidence: 76,
    source: "Portfolio Synergy Agent",
    timestamp: "2026-03-09 07:30",
  },
  {
    id: "AI-003",
    type: "alert",
    title: "Regulatory Change — Healthcare Sector",
    description:
      "MHLW announced revised medical device approval process effective April 2026. Impact analysis: Horizon Medical may benefit from expedited approval pathway for Class II devices.",
    confidence: 82,
    source: "Market Intelligence Agent",
    timestamp: "2026-03-09 06:45",
    relatedDeal: "P-002",
  },
  {
    id: "AI-004",
    type: "recommendation",
    title: "Optimal Exit Window — Digital Frontier",
    description:
      "SaaS sector M&A multiples at 24-month high (avg 12.3x EV/Revenue). Digital Frontier's growth profile positions it for premium valuation. Recommend initiating exit preparation.",
    confidence: 71,
    source: "Exit Optimization Agent",
    timestamp: "2026-03-08 22:00",
    relatedDeal: "P-003",
  },
  {
    id: "AI-005",
    type: "risk",
    title: "Customer Concentration — GreenLogix",
    description:
      "Top 3 customers account for 62% of revenue. DD data room analysis reveals no long-term contracts for top customer (28% of revenue). Recommend pricing adjustment in bid.",
    confidence: 94,
    source: "DD Analysis Agent",
    timestamp: "2026-03-08 18:30",
    relatedDeal: "D-004",
  },
  {
    id: "AI-006",
    type: "opportunity",
    title: "New Sourcing Lead — Industrial Automation",
    description:
      'AI sourcing agent identified 3 companies matching "labor shortage solutions" theme with owner age >65 and no clear successor. Estimated combined EV: ¥8-12B.',
    confidence: 68,
    source: "Sourcing Agent",
    timestamp: "2026-03-08 14:00",
  },
  {
    id: "AI-007",
    type: "alert",
    title: "IM Analysis Complete — Sakura Healthcare",
    description:
      "Automated IM parsing complete. Key findings: 23% EBITDA margin (sector avg 18%), strong regional monopoly position, capex cycle ending FY2026. 3 red flags identified for DD focus.",
    confidence: 88,
    source: "Screening Agent",
    timestamp: "2026-03-09 09:00",
    relatedDeal: "D-003",
  },
  {
    id: "AI-008",
    type: "recommendation",
    title: "Pricing Optimization — Atlas Industrial",
    description:
      "Price elasticity analysis across 847 SKUs reveals 15% of products are significantly underpriced relative to market. Estimated EBITDA uplift: ¥120-180M annually.",
    confidence: 83,
    source: "Value-Up Agent",
    timestamp: "2026-03-08 11:00",
    relatedDeal: "P-001",
  },
];

// ---- LP Reports ----
export const lpReports: LPReport[] = [
  {
    id: "LP-001",
    fund: "Taiga Capital Fund III",
    quarter: "Q4 2025",
    status: "sent",
    nav: "¥42.8B",
    dpi: "0.32x",
    tvpi: "1.62x",
    generatedAt: "2026-01-15",
  },
  {
    id: "LP-002",
    fund: "Taiga Capital Fund III",
    quarter: "Q1 2026",
    status: "draft",
    nav: "¥44.1B",
    dpi: "0.32x",
    tvpi: "1.67x",
    generatedAt: "2026-03-09",
  },
  {
    id: "LP-003",
    fund: "Taiga Capital Fund II",
    quarter: "Q4 2025",
    status: "sent",
    nav: "¥28.5B",
    dpi: "1.15x",
    tvpi: "2.31x",
    generatedAt: "2026-01-15",
  },
  {
    id: "LP-004",
    fund: "Taiga Capital Fund II",
    quarter: "Q1 2026",
    status: "review",
    nav: "¥27.2B",
    dpi: "1.22x",
    tvpi: "2.35x",
    generatedAt: "2026-03-08",
  },
];

// ---- Fund Performance (for charts) ----
export const fundPerformanceData = [
  { quarter: "Q1 24", fundIII: 1.05, fundII: 1.82, benchmark: 1.0 },
  { quarter: "Q2 24", fundIII: 1.12, fundII: 1.95, benchmark: 1.03 },
  { quarter: "Q3 24", fundIII: 1.22, fundII: 2.05, benchmark: 1.05 },
  { quarter: "Q4 24", fundIII: 1.35, fundII: 2.12, benchmark: 1.08 },
  { quarter: "Q1 25", fundIII: 1.41, fundII: 2.18, benchmark: 1.10 },
  { quarter: "Q2 25", fundIII: 1.48, fundII: 2.22, benchmark: 1.12 },
  { quarter: "Q3 25", fundIII: 1.55, fundII: 2.28, benchmark: 1.14 },
  { quarter: "Q4 25", fundIII: 1.62, fundII: 2.31, benchmark: 1.16 },
  { quarter: "Q1 26", fundIII: 1.67, fundII: 2.35, benchmark: 1.18 },
];

export const sectorAllocation = [
  { name: "Technology", value: 28, color: "#2563eb" },
  { name: "Healthcare", value: 22, color: "#6366f1" },
  { name: "Industrial", value: 20, color: "#404040" },
  { name: "Logistics", value: 15, color: "#737373" },
  { name: "Chemicals", value: 10, color: "#a3a3a3" },
  { name: "Other", value: 5, color: "#d4d4d4" },
];

// Stage labels
export const stageLabels: Record<Deal["stage"], string> = {
  sourcing: "Sourcing",
  screening: "Screening",
  dd: "Due Diligence",
  valuation: "Valuation",
  ic: "Investment Committee",
  execution: "Execution",
  closed: "Closed",
};

export const stageOrder: Deal["stage"][] = [
  "sourcing",
  "screening",
  "dd",
  "valuation",
  "ic",
  "execution",
  "closed",
];
