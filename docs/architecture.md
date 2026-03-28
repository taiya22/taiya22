# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                  SimulationRunner                     │
│  (orchestrates all engines for 30-year simulation)   │
├──────────┬──────────┬──────────┬────────────────────┤
│Financial │   M&A    │    HR    │   Compensation     │
│ Engine   │  Engine  │  Engine  │     Engine         │
├──────────┼──────────┼──────────┼────────────────────┤
│  Crisis  │ Investor │   KPI   │                    │
│  Engine  │  Engine  │  Engine  │                    │
├──────────┴──────────┴──────────┴────────────────────┤
│                    Models Layer                       │
│  (SimulationConfig, SimulationState, Financial,      │
│   Organization, Compensation dataclasses)             │
└─────────────────────────────────────────────────────┘
```

## Engine Interface Contract

Every engine follows the same pattern:

```python
class XxxEngine:
    def __init__(self, config: SimulationConfig): ...
    def process(self, state: SimulationState) -> SimulationState: ...
```

- **Stateless between calls** — all state lives in `SimulationState`
- **No cross-engine imports** — orchestration is `SimulationRunner`'s job
- **Financial values in JPY (int)** — never float for currency

## Data Flow

```
SimulationConfig
    │
    ▼
SimulationRunner.run(years=30)
    │
    ├── For each year:
    │   ├── MAEngine.process()        → acquisitions, divestitures
    │   ├── FinancialEngine.process() → P/L, B/S, cash flow
    │   ├── HREngine.process()        → hiring, turnover
    │   ├── CompensationEngine.process() → pay calculation
    │   ├── CrisisEngine.process()    → macro shock check
    │   ├── InvestorEngine.process()  → returns calculation
    │   └── KPIEngine.process()       → traffic light signals
    │
    ▼
List[AnnualReport]  → charts, analysis, reports
```

## Key Domain Concepts

### Phases (from requirements_v1.1.md)
| Phase | Years | Target |
|-------|-------|--------|
| 0: 調達 | 0 | Post-money 50億円 |
| 1: サバイバル | 1-3 | Revenue 30億, EBITDA 5億 |
| 2: 離陸 | 4-6 | Revenue 70億, EBITDA 20億 |
| 3: 拡大 | 7-10 | Revenue 1000億, EBITDA 150億 |
| 4: 支配 | 11-15 | Revenue 2000億, EBITDA 400億 |
| 5: 上場 | 16-20 | EV 1兆円, IPO |
| 6: グローバル | 21-30 | EV 30兆円 |

### Conglomerate Premium Model
Based on academic research (Berger & Ofek 1995, Villalonga 2004, Khanna & Palepu 2000):
- Related diversification → premium
- Unrelated diversification → discount
- PMI capability (DBS-like operating system) → moderates discount
- Japanese institutional context → favorable for conglomerates

### Crisis Model
Based on Reinhart & Rogoff:
- Major recession every 10-15 years
- Two structural shock windows: Year 8-12, Year 20-25
- Random shocks: ~5-8% annual probability
