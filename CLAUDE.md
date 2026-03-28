# CLAUDE.md - Taiga Capital Group Simulation Engine

## Project Overview

Taiga Capital Group 30年ビジネスシミュレーションエンジン。
日本のコングロマリットの成長・買収・財務パフォーマンス・組織ダイナミクスを30年間シミュレートする。

- **Language**: Python 3.10+
- **Core deps**: numpy, pandas
- **Test framework**: pytest
- **Linter/Formatter**: ruff
- **Type checker**: mypy

## Knowledge Base

Detailed documentation lives in `docs/` — this file is a table of contents:
- `docs/architecture.md` — system overview, data flow, engine interface contract
- `docs/requirements_v1.1.md` — full requirements specification (Japanese)
- `docs/brand_identity.md` — corporate branding guidelines
- `docs/founding_story.md` — philosophy & founding narrative

## Progress Tracking

`claude-progress.json` tracks multi-session agent progress. Update it at the end of each session.

## Architecture

```
taiga_sim/
├── engines/          # Core simulation engines (financial, M&A, HR, etc.)
├── models/           # Dataclass-based data models
└── utils/            # Formatting utilities
tests/                # pytest test suite
scripts/              # Quality gate & automation scripts
docs/                 # Requirements, brand identity, founding story
site/                 # Corporate website (GitHub Pages)
```

### Key Engines
- `simulation_runner.py` - Main orchestrator, runs 30-year simulation
- `financial_engine.py` - P/L, B/S, cash flow modeling
- `ma_engine.py` - M&A strategy (acquisition, carve-out, divestiture)
- `compensation_engine.py` - Grade-based compensation system
- `crisis_engine.py` - Macro shocks and crisis handling
- `hr_engine.py` - Hiring, turnover, organizational growth
- `investor_engine.py` - Investor returns calculation
- `kpi_engine.py` - KPI tracking and reporting

### Models
All models use `@dataclass` with computed properties. Financial values are in JPY (Japanese Yen).

## Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=taiga_sim --cov-report=term-missing

# Lint (check only)
python -m ruff check .

# Lint (auto-fix)
python -m ruff check --fix .

# Format
python -m ruff format .

# Type check
python -m mypy taiga_sim/

# Run full quality gate (lint + type check + test)
bash scripts/verify.sh

# Run simulation
python run_simulation.py

# Run all analyses
python run_all_analyses.py
```

## Coding Conventions

### Must Follow
- Use `@dataclass` for all data models; prefer computed `@property` over storing derived values
- Financial amounts are always in JPY (int); never use float for currency
- Use `from __future__ import annotations` at the top of every module
- All engine classes follow the pattern: `__init__(config)` + `process(state) -> state`
- Keep functions under 50 lines; extract helpers if longer
- Write docstrings for public classes and methods (Japanese OK for domain-specific terms)
- Type hints are required for all function signatures

### Naming
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_`

### Testing
- Every engine must have corresponding tests in `tests/`
- Test class naming: `Test{ClassName}`
- Test method naming: `test_{method}_{scenario}`
- Use `pytest.approx()` for floating point comparisons
- Use fixtures for common setup (SimulationConfig, SimulationState)

### Error Handling
- Validate inputs at public API boundaries only
- Use `ValueError` for invalid parameters
- Never silently swallow exceptions

### Git
- Commit messages in English, imperative mood
- One logical change per commit
- Always run `bash scripts/verify.sh` before committing

## Domain Knowledge

### Financial Terms (JP -> EN)
- 売上高 = Revenue
- 営業利益 = Operating Income
- EBITDA = Earnings Before Interest, Taxes, Depreciation, and Amortization
- 純利益 = Net Income
- 有利子負債 = Interest-bearing Debt
- FCF = Free Cash Flow

### Simulation Parameters
- Simulation period: 30 years
- M&A failure rate: ~50% (KPMG benchmark)
- New venture failure rate: ~60%
- Major recession cycle: every 10-15 years (Reinhart & Rogoff)
- Tax rate: 30% (Japanese corporate tax approximation)

## What NOT to Do
- Do not modify `site/index.html` without explicit request - it's the production website
- Do not change simulation parameters in models without understanding downstream effects
- Do not add new dependencies without adding to `pyproject.toml`
- Do not use `print()` for debugging - use proper logging or remove before commit
- Do not commit `.pyc`, `__pycache__/`, or generated `data/` files
