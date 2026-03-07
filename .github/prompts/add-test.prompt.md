---
description: "Add pytest tests for a specific function or module in hledger-lit"
agent: "agent"
argument-hint: "Function or module to test (e.g., DataTransformer.parent)"
---

Add tests for the specified function or module. A test suite already exists in `tests/`.

## Steps

1. **Identify the target** — determine which module and function(s) to test from the user's description.

2. **Find the right test file** — place tests in the existing `tests/test_<module>.py` file. If it doesn't exist yet, create it following the pattern of other test files in `tests/`.

3. **Check existing fixtures** — review [tests/conftest.py](../../tests/conftest.py) for reusable fixtures before creating new ones. Add new fixtures to `conftest.py` only if they'll be shared; otherwise use local fixtures or inline data.

4. **Write focused tests** covering:
   - Happy path with representative input
   - Edge cases (empty input, missing keys, boundary values)
   - Error cases (invalid input raises expected exceptions)

5. **Run the tests** to verify they pass:
   ```bash
   uv run pytest tests/test_<module>.py -v
   ```

## Constraints

- Use `from __future__ import annotations` in test files
- Mock `subprocess.run` for anything in `hledger.py` — never call real hledger
- Use `tmp_path` for any file I/O (config tests)
- Assert on `@dataclass` instances directly, not dicts
- One test function per behavior — use descriptive names like `test_parent_returns_empty_for_top_level`
