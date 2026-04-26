from pathlib import Path
from sansqrit.dsl import translate
bad = []
for p in sorted(Path('examples').glob('*.sq')):
    try:
        py = translate(p.read_text(), filename=str(p))
        compile(py, str(p), 'exec')
    except Exception as exc:
        bad.append((p, exc))
print('examples', len(list(Path('examples').glob('*.sq'))), 'bad', len(bad))
for p, exc in bad:
    print(p, exc)
raise SystemExit(1 if bad else 0)
