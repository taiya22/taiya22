# Models - Agent Guide

## Purpose
Pure data models using `@dataclass`. No business logic beyond computed properties.

## Rules
- Always use `@dataclass` (not Pydantic or attrs)
- Use `from __future__ import annotations` for forward references
- Derived values must be `@property`, not stored fields
- Financial amounts: `int` in JPY
- All fields must have type annotations
- Default values for optional fields via `field(default=...)` or `field(default_factory=...)`

## Examples
```python
@dataclass
class ProfitLoss:
    revenue: int
    cogs: int

    @property
    def gross_profit(self) -> int:
        return self.revenue - self.cogs
```
