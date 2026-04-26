from pathlib import Path
from sansqrit.dsl import run_file
import builtins
bad = []
for p in sorted(Path('examples').glob('*.sq')):
    old_print = builtins.print
    try:
        builtins.print = lambda *args, **kwargs: None
        run_file(p)
    except Exception as exc:
        bad.append((p, exc))
    finally:
        builtins.print = old_print
print('examples', len(list(Path('examples').glob('*.sq'))), 'bad', len(bad))
for p, exc in bad:
    print(p, exc)
raise SystemExit(1 if bad else 0)
