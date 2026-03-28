# Add New Engine Skill

When the user asks to add a new simulation engine, follow this checklist:

1. **Create engine file** at `taiga_sim/engines/{name}_engine.py`
   - Use `from __future__ import annotations`
   - Follow the standard engine interface:
     ```python
     class {Name}Engine:
         def __init__(self, config: SimulationConfig): ...
         def process(self, state: SimulationState) -> SimulationState: ...
     ```
   - Import and use models from `taiga_sim/models/`

2. **Register in SimulationRunner** (`taiga_sim/engines/simulation_runner.py`)
   - Import the new engine
   - Instantiate in `__init__`
   - Call `process()` in the yearly loop

3. **Add tests** in `tests/test_simulation.py`
   - Create `class Test{Name}Engine`
   - Test the `process()` method with realistic scenarios
   - Test edge cases

4. **Update AGENTS.md** - Add the engine to the table in `taiga_sim/engines/AGENTS.md`

5. **Run quality gate**: `bash scripts/verify.sh`
