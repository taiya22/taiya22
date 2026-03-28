# Verify Skill

Run the full harness quality gate to check code quality.

```bash
bash scripts/verify.sh
```

This runs:
1. **ruff check** - Lint for bugs, style, imports
2. **ruff format --check** - Formatting consistency
3. **mypy** - Type safety
4. **pytest** - All tests pass

If any check fails, fix the issues and re-run.

For a faster check (skips mypy):
```bash
bash scripts/verify.sh --quick
```
