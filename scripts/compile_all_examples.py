from pathlib import Path
from sansqrit.dsl import translate
import os, sys
bad = []
files = sorted(Path('examples').glob('*.sq'))
for p in files:
    try:
        py = translate(p.read_text(), filename=str(p))
        compile(py, str(p), 'exec')
    except Exception as exc:
        bad.append((p, exc))
print('examples', len(files), 'bad', len(bad), flush=True)
for p, exc in bad:
    print(p, exc, flush=True)
os._exit(1 if bad else 0)
