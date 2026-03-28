# Engines - Agent Guide

## Purpose
Each engine encapsulates a single domain of the simulation.

## Pattern
All engines follow the same interface:
```python
class XxxEngine:
    def __init__(self, config: SimulationConfig): ...
    def process(self, state: SimulationState) -> SimulationState: ...
```

## Rules
- Engines must be stateless between calls - all state lives in `SimulationState`
- Never import one engine from another; orchestration is `SimulationRunner`'s job
- Financial calculations use `int` (JPY) - never `float` for currency
- Reference academic sources in comments when using domain-specific formulas
- Every new engine needs tests in `tests/test_simulation.py`

## Existing Engines
| Engine | Domain | Key Models |
|---|---|---|
| `financial_engine` | P/L, B/S, Cash Flow | `ProfitLoss`, `BalanceSheet`, `CashFlow` |
| `ma_engine` | Acquisitions, divestitures | `Company`, `CompanyType` |
| `hr_engine` | Hiring, turnover | `Member`, `MemberGrade` |
| `compensation_engine` | Grade-based pay | `CompensationTier` |
| `crisis_engine` | Macro shocks | Phase-based triggers |
| `investor_engine` | Returns calculation | IRR, multiples |
| `kpi_engine` | KPI tracking | Revenue, headcount metrics |
