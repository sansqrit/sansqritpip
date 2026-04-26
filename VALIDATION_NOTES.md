# Sansqrit v0.3.2 validation notes

Validated in this container with `/usr/bin/python3`:

```bash
PYTHONPATH=src /usr/bin/python3 -m py_compile src/sansqrit/*.py
PYTHONPATH=src /usr/bin/python3 scripts/compile_all_examples.py
PYTHONPATH=src /usr/bin/python3 - <<'PY'
from pathlib import Path
from sansqrit.dsl import run_file
for p in sorted(Path('examples').glob('25[3-9]_*.sq')) + sorted(Path('examples').glob('26*.sq')) + sorted(Path('examples').glob('27*.sq')):
    run_file(p)
PY
```

Results:

- Python source compiled successfully.
- 275 Sansqrit examples compiled successfully.
- New QEC examples 253-275 executed successfully.
- QEC unit tests were run directly and passed.

Note: the existing distributed-worker test can keep background server threads alive in this restricted container, so the full custom test runner was not used for the final validation log here. Run the full suite in a normal Python environment before production PyPI release.
