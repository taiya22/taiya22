#!/usr/bin/env bash
# =============================================================================
# Harness Quality Gate - verify.sh
# =============================================================================
# Unified quality gate script that acts as the "Evaluator" in the
# Generator+Evaluator harness pattern. Run this before every commit.
#
# Usage:
#   bash scripts/verify.sh          # Run all checks
#   bash scripts/verify.sh --quick  # Skip mypy (faster)
# =============================================================================

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
QUICK=false

[[ "${1:-}" == "--quick" ]] && QUICK=true

run_check() {
    local name="$1"
    shift
    echo -e "\n${YELLOW}[$name]${NC} Running..."
    if "$@" 2>&1; then
        echo -e "${GREEN}[$name] PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}[$name] FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo "============================================"
echo "  Harness Quality Gate"
echo "============================================"

# 1. Ruff lint check
run_check "ruff-lint" python -m ruff check .

# 2. Ruff format check
run_check "ruff-format" python -m ruff format --check .

# 3. Mypy type check (skip in quick mode)
if [[ "$QUICK" == false ]]; then
    run_check "mypy" python -m mypy taiga_sim/
fi

# 4. Pytest
run_check "pytest" python -m pytest tests/ -v --tb=short

# Summary
echo ""
echo "============================================"
echo -e "  Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo "============================================"

if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Quality gate FAILED. Fix issues before committing.${NC}"
    exit 1
else
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
fi
