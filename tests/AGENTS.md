# Tests - Agent Guide

## Purpose
pytest-based test suite for the simulation engine.

## Rules
- Group tests by class: `class Test{ClassName}`
- Name tests: `test_{method}_{scenario}`
- Use `pytest.approx()` for float comparisons
- Use `pytest.raises()` for expected exceptions
- Prefer small, focused tests over large integration tests
- Financial test values should use realistic Japanese corporate scale (億円 = 100M JPY)

## Running
```bash
python -m pytest tests/ -v
python -m pytest tests/ -k "test_profit"  # run specific tests
```
