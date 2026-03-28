# Add New Model Skill

When the user asks to add a new data model, follow this checklist:

1. **Create or extend model file** in `taiga_sim/models/`
   - Use `from __future__ import annotations`
   - Use `@dataclass` decorator
   - All fields must have type annotations
   - Derived values as `@property`
   - Financial values as `int` (JPY)

2. **Export from `__init__.py`** - Add to `taiga_sim/models/__init__.py`

3. **Add tests** in `tests/test_simulation.py`
   - Test all computed properties
   - Test with realistic Japanese corporate financial scale

4. **Run quality gate**: `bash scripts/verify.sh`
